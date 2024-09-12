import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from envs.gym_envs import UAV_VAT_Gymnasium

# To-DO: 要让我们的Gymnasium环境适配两种的state(Actor和Critic)