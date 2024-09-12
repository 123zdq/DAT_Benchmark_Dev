import multiprocessing
from multiprocessing import connection
from multiprocessing.context import BaseContext
from typing import Literal
from tianshou.env.worker.subproc import ShArray,SubprocEnvWorker,_setup_buf
from tianshou.env.venvs import BaseVectorEnv
from tianshou.env.utils import ENV_TYPE
from tianshou.env.utils import CloudpickleWrapper
from tianshou.env.worker import EnvWorker
import numpy as np
from collections.abc import Sequence
from typing import Callable
import gymnasium

def _worker_tianshou(
    parent: connection.Connection,
    p: connection.Connection,
    env_fn_wrapper: CloudpickleWrapper,
    obs_bufs: dict | tuple | ShArray | None = None,
) -> None:
    def _encode_obs(
        obs: dict | tuple | np.ndarray,
        buffer: dict | tuple | ShArray,
    ) -> None:
        if isinstance(obs, np.ndarray) and isinstance(buffer, ShArray):
            buffer.save(obs)
        elif isinstance(obs, tuple) and isinstance(buffer, tuple):
            for o, b in zip(obs, buffer, strict=True):
                _encode_obs(o, b)
        elif isinstance(obs, dict) and isinstance(buffer, dict):
            for k in obs:
                _encode_obs(obs[k], buffer[k])

    parent.close()
    env = env_fn_wrapper.data()
    try:
        while True:
            try:
                cmd, data = p.recv()
            except EOFError:  # the pipe has been closed
                p.close()
                break
            try:
                done
            except:
                done = False
            if cmd == "step":
                if not done:
                    env_return = env.step(data)
                    done = env_return[2] or env_return[3]
                    if obs_bufs is not None:
                        _encode_obs(env_return[0], obs_bufs)
                        env_return = (None, *env_return[1:])
                    p.send(env_return)
                else:
                    done = False
                    obs, info = env.reset()
                    if obs_bufs is not None:
                        _encode_obs(obs, obs_bufs)
                        obs = None
                    p.send((obs,0.0,0.0,False,info))
            elif cmd == "reset":
                obs, info = env.reset(**data)
                if obs_bufs is not None:
                    _encode_obs(obs, obs_bufs)
                    obs = None
                p.send((obs, info))
            elif cmd == "close":
                p.send(env.close())
                p.close()
                break
            elif cmd == "render":
                p.send(env.render(**data) if hasattr(env, "render") else None)
            elif cmd == "seed":
                if hasattr(env, "seed"):
                    p.send(env.seed(data))
                else:
                    env.action_space.seed(seed=data)
                    env.reset(seed=data)
                    p.send(None)
            elif cmd == "getattr":
                p.send(getattr(env, data) if hasattr(env, data) else None)
            elif cmd == "setattr":
                setattr(env.unwrapped, data["key"], data["value"])
            else:
                p.close()
                raise NotImplementedError
    except KeyboardInterrupt:
        p.close()

class SubprocEnvWorker_TS(SubprocEnvWorker,EnvWorker):
    """Subprocess worker used in SubprocVectorEnv and ShmemVectorEnv."""

    def __init__(
        self,
        env_fn: Callable[[], gymnasium.Env],
        share_memory: bool = False,
        context: BaseContext | Literal["fork", "spawn"] | None = None,
    ) -> None:
        if not isinstance(context, BaseContext):
            context = multiprocessing.get_context(context)
        self.parent_remote, self.child_remote = context.Pipe()
        self.share_memory = share_memory
        self.buffer: dict | tuple | ShArray | None = None
        assert hasattr(context, "Process")  # for mypy
        if self.share_memory:
            dummy = env_fn()
            obs_space = dummy.observation_space
            dummy.close()
            del dummy
            self.buffer = _setup_buf(obs_space, context)
        args = (
            self.parent_remote,
            self.child_remote,
            CloudpickleWrapper(env_fn),
            self.buffer,
        )
        self.process = context.Process(target=_worker_tianshou, args=args, daemon=True)
        self.process.start()
        self.child_remote.close()
        EnvWorker.__init__(self,env_fn)


class SubprocVectorEnv_TS(BaseVectorEnv):
    def __init__(
        self,
        env_fns: Sequence[Callable[[], ENV_TYPE]],
        wait_num: int | None = None,
        timeout: float | None = None,
        share_memory: bool = False,
        context: Literal["fork", "spawn"] | None = None,
    ) -> None:
        def worker_fn(fn: Callable[[], gymnasium.Env]) -> SubprocEnvWorker:
            return SubprocEnvWorker_TS(fn, share_memory=share_memory, context=context)

        super().__init__(
            env_fns,
            worker_fn,
            wait_num,
            timeout,
        )
