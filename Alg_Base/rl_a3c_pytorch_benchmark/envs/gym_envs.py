import gym
from gym import spaces
import gymnasium
import gymnasium.spaces
import numpy as np
from environment import general_env
from utils import read_config

from async_vecenv import ASYNC_SubprocVecEnv
import sys
# for path in sys.path:
#     print(path)

CONF = "./config.json"
ENV_CONF = "../../Webots_Simulation/traffic_project/config/env_config.json"

class UAV_VAT(gym.Env):
    def __init__(self,arg_worker:int=1,conf_path:str=CONF,env_conf_path:str=ENV_CONF,process_idx:int=0) -> None:
        super(UAV_VAT,self).__init__()
        self.action_space = spaces.Discrete(7)
        self.observation_space = spaces.Box(low=0,high=255,shape=(3,84,84),dtype=np.uint8)
        conf_json = read_config(conf_path)
        env_conf = conf_json["Benchmark"] # env_conf:dict

        self.webots_conf = read_config(env_conf_path)

        assert process_idx < arg_worker
        self.env,_ = general_env(env_id="Benchmark",env_conf=env_conf,arg_worker=arg_worker,process_idx=process_idx)
        self.state = None
    
    def reset(self):
        self.state,_ = self.env.reset()
        return self.state
    
    def step(self, action):
        info = {}
        self.state,reward,done,SuppleInfo = self.env.step(action=action)
        curr_step = self.env.curr_step
        if done and curr_step < self.webots_conf["Train_Total_Steps"]:
            info["TimeLimit.truncated"] = True
        else:
            info["TimeLimit.truncated"] = False
        return self.state,reward,done,info

    def render(self):
        pass

    def close(self):
        pass


class UAV_VAT_Gymnasium(gymnasium.Env):
    def __init__(self,arg_worker:int=1,conf_path:str=CONF,env_conf_path:str=ENV_CONF,process_idx:int=0) -> None:
        super(UAV_VAT_Gymnasium,self).__init__()
        self.action_space = gymnasium.spaces.Discrete(7)
        self.observation_space = gymnasium.spaces.Box(low=0,high=255,shape=(3,84,84),dtype=np.uint8)
        conf_json = read_config(conf_path)
        env_conf = conf_json["Benchmark"] # env_conf:dict

        self.webots_conf = read_config(env_conf_path)

        assert process_idx < arg_worker
        self.env,_ = general_env(env_id="Benchmark",env_conf=env_conf,arg_worker=arg_worker,process_idx=process_idx)
        self.state = None
    
    def reset(self,seed=None):
        reset_info={}
        self.state,_ = self.env.reset()
        return self.state,reset_info
    
    def step(self, action):
        info = {}
        self.state,reward,done,SuppleInfo = self.env.step(action=action)
        curr_step = self.env.curr_step
        info["SuppleInfo"] = SuppleInfo
        if done and curr_step < self.webots_conf["Train_Total_Steps"]:
            truncated = True
        else:
            truncated = False
        return self.state,reward,done,truncated,info

    def render(self):
        pass

    def close(self):
        pass



from gym.envs.registration import register

register(
    id='UAVVAT-v0',
    entry_point='gym_envs:UAV_VAT',
)


def gym_test():
    import gym
    import numpy as np
	
    env = gym.make('UAVVAT-v0')
    observation = env.reset()

    for _ in range(10000):
        action = env.action_space.sample()  # 随机生成一个动作
        observation, reward, done, info = env.step(action)
        env.render()

        if done:
            observation = env.reset()

    env.close()

def stableparallel_test(n_envs:int,gym=True):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv

    def make_env(n_envs,rank):
        def _init():
            if gym:
                env = UAV_VAT(arg_worker=n_envs,process_idx=rank)
            else:
                env = UAV_VAT_Gymnasium(arg_worker=n_envs,process_idx=rank)
            return env
        return _init
    
    # 创建16个并行环境
    n_envs = n_envs
    env = ASYNC_SubprocVecEnv([make_env(n_envs=n_envs,rank=rank) for rank in range(n_envs)])
    # env = SubprocVecEnv([make_env(n_envs=n_envs,rank=rank) for rank in range(n_envs)])
    model = PPO('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=100000) #,callback=CustomCallback
    env.close()

if __name__ == "__main__":
    # gym_test()
    stableparallel_test(n_envs=2,gym=False)



