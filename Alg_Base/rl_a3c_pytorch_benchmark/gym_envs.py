import gym
from gym import spaces
import numpy as np
from environment import general_env
from utils import read_config
import sys
for path in sys.path:
    print(path)

ENV_CONF = "./config.json"

class UAV_VAT(gym.Env):
    def __init__(self,arg_worker:int,env_conf_path:str=ENV_CONF,process_idx:int=0) -> None:
        super(UAV_VAT,self).__init__()
        self.action_space = spaces.Discrete(7)
        self.observation_space = spaces.Box(low=0,high=255,shape=(84,84,3),dtype=np.uint8)
        env_conf_json = read_config(env_conf_path)
        env_conf = env_conf_json["Benchmark"] # env_conf:dict

        assert process_idx < arg_worker
        self.env = general_env(env_id="Benchmark",env_conf=env_conf,arg_worker=arg_worker,process_idx=process_idx)
        