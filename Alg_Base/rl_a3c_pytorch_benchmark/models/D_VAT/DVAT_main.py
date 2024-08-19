import time
import gym
from customCNN import CustomCNN
import denseMlpPolicy
import wandb
import numpy as np
from stable_baselines3 import SAC
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from sacd.sacd import SACD
from pathlib import Path
from stable_baselines3.common.evaluation import evaluate_policy


from envs.gym_envs import make_env
from envs.async_vecenv import ASYNC_SubprocVecEnv

from DiscreteMlpPolicy import SACDiscretePolicy

if __name__ == "__main__":

    settings = {'num_cpu': 5,
                'n_timesteps': 60000,
                'batch_size': 64,
                'buffer_size': 10000,
                'train_freq': 8,
                'WandB': False,  # True if you want to use wandb for logging
                'WandB_project': '<your_wandb_project>',
                'WandB_entity': '<your_wandb_entity>',
                'WandB_API_key': '<your_wandb_api_key>',
                'render': True,  # True to disable black screen
                'eval_episodes': 20,
                'eval_mode': False,  # True for model Test - False for Training
                'ts': 0.05,
                'observation_buffer_length': 3
                }

    if settings['eval_mode']:
        # try:
        eval_env = ASYNC_SubprocVecEnv([make_env(n_envs=1,rank=0,gym=False)])
        model = SAC.load(os.path.join("experiments/SAC_{}".format(1711119972), "SAC_{}".format(0)), env=eval_env)


        # Eval
        mean_reward, std_reward = evaluate_policy(model, eval_env, n_eval_episodes=settings['eval_episodes'])
        print(f'Mean reward: {mean_reward} +/- {std_reward:.2f}')
    else:
        t = int(time.time())

        # Path for Models
        pathname = os.path.dirname(sys.argv[0])
        abs_path = os.path.abspath(pathname)
        current_path = Path(os.path.join(abs_path, "experiments", "SAC_{}".format(t)))
        current_path.mkdir(parents=True, exist_ok=True)

        if settings['WandB']:
            wandb.login(key=settings['WandB_API_key'])
            wandb.init(project=settings['WandB_project'], entity=settings['WandB_entity'],
                       name="SAC_{}".format(t), config=settings)

        tensorboard_logdir = "./models/D_VAT/DVAT_logs"

        # Multiprocess RL Training
        vec_env = ASYNC_SubprocVecEnv([make_env(n_envs=settings['num_cpu'],rank=i,gym=False,end_reward=True,log_dir=tensorboard_logdir) for i in range(settings['num_cpu'])])

        policy_kwargs = dict(
            net_arch=[512],
            normalize_images=False
        )


        model = SACD(SACDiscretePolicy,
                    vec_env,
                    verbose=1,
                    policy_kwargs=policy_kwargs,
                    tensorboard_log=tensorboard_logdir,
                    buffer_size=settings['buffer_size'],
                    batch_size=settings['batch_size'],
                    train_freq=settings['train_freq'])

        print(model.policy)
        print(model.critic)

        # Separate environment for evaluation
        # eval_env = ASYNC_SubprocVecEnv([make_env(n_envs=1,rank=0,gym=False,monitor=True)])
        best_episodes = np.zeros((10,))

        epoch = 0

        # Training
        while True:
            epoch += 1
            model.learn(settings['n_timesteps'])
            model.save(os.path.join(current_path, "SAC_Epoch{}".format(epoch)))
            # Eval
            # mean_reward, std_reward = evaluate_policy(model, eval_env, n_eval_episodes=settings['eval_episodes'], render=settings['render'])
            # print(f'Mean reward: {mean_reward} +/- {std_reward:.2f}')

            # if settings['WandB']:
            #     wandb.log({'test': mean_reward})

            # worst_model = np.argmin(best_episodes)
            # if mean_reward > best_episodes[worst_model]:
            #     best_episodes[worst_model] = mean_reward
            #     model.save(os.path.join(current_path, "SAC_{}".format(worst_model)))

