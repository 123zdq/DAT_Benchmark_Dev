from stable_baselines3.common.vec_env import SubprocVecEnv
import multiprocessing as mp
from stable_baselines3.common.vec_env.base_vec_env import CloudpickleWrapper,VecEnv
from typing import Optional,Dict,Any,List,Callable
from stable_baselines3.common.vec_env.patch_gym import _patch_env
import gymnasium as gym


def _worker_Async(
    remote: mp.connection.Connection,
    parent_remote: mp.connection.Connection,
    env_fn_wrapper: CloudpickleWrapper,
) -> None:
    # Import here to avoid a circular import
    from stable_baselines3.common.env_util import is_wrapped

    parent_remote.close()
    env = _patch_env(env_fn_wrapper.var())
    reset_info: Optional[Dict[str, Any]] = {}
    while True:
        try:
            cmd, data = remote.recv()
            if cmd == "step":
                try:
                    done
                except NameError:
                    done = False
                if not done:
                    observation, reward, terminated, truncated, info = env.step(data)
                # convert to SB3 VecEnv api
                # done = terminated or truncated
                    info["TimeLimit.truncated"] = truncated and not terminated
                    done = terminated or truncated
                # if done:
                else:
                    # save final observation where user can get it, then reset
                    info["terminal_observation"] = observation
                    observation, reset_info = env.reset()
                    done = False
                remote.send((observation, reward, done, info, reset_info))
            elif cmd == "reset":
                maybe_options = {"options": data[1]} if data[1] else {}
                observation, reset_info = env.reset(seed=data[0], **maybe_options)
                remote.send((observation, reset_info))
            elif cmd == "render":
                remote.send(env.render())
            elif cmd == "close":
                env.close()
                remote.close()
                break
            elif cmd == "get_spaces":
                remote.send((env.observation_space, env.action_space))
            elif cmd == "env_method":
                method = getattr(env, data[0])
                remote.send(method(*data[1], **data[2]))
            elif cmd == "get_attr":
                remote.send(getattr(env, data))
            elif cmd == "set_attr":
                remote.send(setattr(env, data[0], data[1]))  # type: ignore[func-returns-value]
            elif cmd == "is_wrapped":
                remote.send(is_wrapped(env, data))
            else:
                raise NotImplementedError(f"`{cmd}` is not implemented in the worker")
        except EOFError:
            break

class ASYNC_SubprocVecEnv(SubprocVecEnv,VecEnv):
    def __init__(self,env_fns: List[Callable[[], gym.Env]], start_method: Optional[str] = None):
        self.waiting = False
        self.closed = False
        n_envs = len(env_fns)

        if start_method is None:
            # Fork is not a thread safe method (see issue #217)
            # but is more user friendly (does not require to wrap the code in
            # a `if __name__ == "__main__":`)
            forkserver_available = "forkserver" in mp.get_all_start_methods()
            start_method = "forkserver" if forkserver_available else "spawn"
        ctx = mp.get_context(start_method)

        self.remotes, self.work_remotes = zip(*[ctx.Pipe() for _ in range(n_envs)])
        self.processes = []
        for work_remote, remote, env_fn in zip(self.work_remotes, self.remotes, env_fns):
            args = (work_remote, remote, CloudpickleWrapper(env_fn))
            # daemon=True: if the main process crashes, we should not cause things to hang
            process = ctx.Process(target=_worker_Async, args=args, daemon=True)  # type: ignore[attr-defined]
            process.start()
            self.processes.append(process)
            work_remote.close()

        self.remotes[0].send(("get_spaces", None))
        observation_space, action_space = self.remotes[0].recv()

        VecEnv.__init__(self,len(env_fns), observation_space, action_space)

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
        env_fn: Callable[[], gym.Env],
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
        def worker_fn(fn: Callable[[], gym.Env]) -> SubprocEnvWorker:
            return SubprocEnvWorker_TS(fn, share_memory=share_memory, context=context)

        super().__init__(
            env_fns,
            worker_fn,
            wait_num,
            timeout,
        )
