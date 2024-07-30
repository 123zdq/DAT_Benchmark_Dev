import asyncio
import numpy as np

"""
# Conda Environments
.conda/
.conda/*

# PPO Model Parameters
params.pth
"""


def GE(num):
    from main import parser
    from environment import general_env
    from utils import read_config
    import torch

    args = parser.parse_args()
    torch.manual_seed(args.seed)

    setup_json = read_config(args.env_config)
    for i in setup_json.keys():
        if i in args.env:
            env_conf = setup_json[i]
    res = []
    for _ in range(num):
        env, process_func = general_env(args.env, env_conf, num - 1, process_idx=_)
        res.append(env)
    return res


class Envs:
    class Env:  # need to modify
        def __init__(self, env):
            self.env = env
            self.state = None
            self.reward = None
            self.done = None
            self.should_reset = False

        def reset(self):
            self.state, _ = self.env.reset()

        def step(self, action: int):
            if self.should_reset:
                self.state, _ = self.env.reset()
                self.should_reset = False
                assert self.done
            else:
                self.state, self.reward, self.done, _ = self.env.step(action)
                if self.done > 0.5:
                    self.should_reset = True

    class Env_T:  # need to modify
        def __init__(self, env):
            self.env = env
            self.state = None
            self.reward = None
            self.done = None

            """
            self.rewards=0
            self.tot=0
            self.score=0
            self.y=[]
            self.x=[]
            self.steps=0
            """

        def reset(self):
            self.state, _ = self.env.reset()

        def step(self, action: int):
            self.state, self.reward, self.done, _ = self.env.step(action)
            if self.done:
                self.state, _ = self.env.reset()

            """
            self.steps+=1
            self.rewards+=self.reward
            if self.done:
                self.score+=self.rewards
                self.rewards=0
                self.tot+=1
            if self.tot==20:
                self.y.append(self.score/self.tot)
                self.x.append(self.steps)
                self.tot=0
                self.score=0
            """

    def __init__(self, *args, **kwargs):
        # num_envs
        # env_mk
        # env_mk_args
        # env_mk or env_list

        self.num_envs = kwargs["num_envs"]

        if "env_list" in kwargs:
            self.env_list = [self.Env(env) for env in kwargs["env_list"]]
        else:
            self.env_list = []
            for _ in range(self.num_envs):
                self.env_list.append(
                    self.Env(kwargs["env_mk"](*(kwargs["env_mk_args"])))
                )

        self.states = None
        self.rewards = None
        self.done = None

    async def reset_(self):
        await asyncio.gather(
            *tuple([asyncio.to_thread(env.reset) for env in self.env_list])
        )
        self.states = np.array([env.state for env in self.env_list])

    async def step_(self, actions):
        await asyncio.gather(
            *tuple(
                [
                    asyncio.to_thread(self.env_list[i].step, actions[i])
                    for i in range(self.num_envs)
                ]
            )
        )
        self.states, self.rewards, self.done = (
            np.array([env.state for env in self.env_list]),
            np.array([env.reward for env in self.env_list]),
            np.array([env.done for env in self.env_list]),
        )

    def reset(self):
        asyncio.run(self.reset_())
        return self.states

    def step(self, actions):
        asyncio.run(self.step_(actions))
        return self.states, self.rewards, self.done


"""#
my=Envs(num_envs=2,env_list=GE(2))
print("Gen!")
print(my.reset())
rng = np.random.default_rng()
while True:
    my.step(rng.integers(0, 7, size=2))

#"""
