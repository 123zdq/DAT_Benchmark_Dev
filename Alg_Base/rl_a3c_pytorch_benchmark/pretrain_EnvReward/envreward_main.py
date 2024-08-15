import torch
from torch.utils.tensorboard import SummaryWriter
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from envrewardmodel import EnvRewardModel
from envreward_utils import read_config,get_newest_path,save_weight
import argparse
import torch.nn as nn
import tqdm
from torch.utils.data import DataLoader
from envreward_dataset import EnvRewardDataset


parser = argparse.ArgumentParser(description="EnvRewardModel")
"""
    Argument that we need to config：
        --Epoch
        --gpu-ids
        --env-config
        --seed
        --tensorboard-logger
        --tensorboard-logdir
        --log-interval
"""

parser.add_argument(
    "-E",
    "--Epoch",
    type=int,
    default=100,
    help="Number epochs",
)

parser.add_argument(
    "-bs",
    "--batch-size",
    type=int,
    default=1024,
    help="Batch size of dataloader"
)

parser.add_argument(
    "-evc", "--env-config",
    default="./envreward_cfg.json",
    help="pretrain Dynamics Model info (default: pretrain_cfg.json)")

parser.add_argument(
    "-s", "--seed", type=int, default=1, help="random seed (default: 1)"
)

parser.add_argument(
    "-tl",
    "--tensorboard-logger",
    type=bool,
    default=True,
    help="Creates tensorboard logger to view model weights and biases, and monitor test agent reward progress",
)

parser.add_argument(
    "-tldir",
    "--tensorboard-logdir",
    type=str,
    default="./runs/experiment",
    help="dir of tensorboard logger",
)

parser.add_argument(
    "-login",
    "--log-interval",
    type=int,
    default=50,
    help="How many iteration do we log loss",
)

parser.add_argument(
    "-l",
    "--load",
    type=bool,
    default=False,
    help="Whether load pretrain weight or not",
)


parser.add_argument(
    "-wd",
    "--weight-dir",
    type=str,
    default="./trained_models/",
    help="directory of train weight",
)

parser.add_argument(
    "-si",
    "--save-interval",
    type=int,
    default=10,
    help="How many epoch do we save a model",
)


Epoch = 100
batch_size = 256

def main(args,cfg):
    ### device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    ### tensorboard logger
    if args.tensorboard_logger:
        writer = SummaryWriter(args.tensorboard_logdir)

    ### start train config
    model = EnvRewardModel(input_shape=(cfg["State_channel"],cfg["State_size"],cfg["State_size"]),actions_dim=cfg["Action_dim"])
    if args.load: # If need to load pretrain params,load the newest params in default
        if not os.path.exists(args.weight_dir) or not os.path.exists(args.weight_dir+args.TrainMode):
            raise FileNotFoundError(f"Directory:{args.weight_dir+args.TrainMode} does not exist")
        load_path = get_newest_path(args)
        model.load_state_dict(torch.load(load_path))
    model.to(device)
    model.train()

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    train_dataset = EnvRewardDataset(mode=args.TrainMode,train=True)
    train_dl = DataLoader(train_dataset,batch_size=args.batch_size,shuffle=True,num_workers=16)
    for epoch in tqdm(range(args.Epoch),desc="Train Epochs"):
        running_loss = 0.0
        running_env_loss = 0.0
        running_reward_loss = 0.0

        for i,train_data in tqdm(enumerate(train_dl),desc=f"Train Iteration {len(train_dl)}",leave=False):
            train_tensor,train_label = train_data
            train_tensor = train_tensor.to(device)
            train_label = train_label.to(device).long()

            optimizer.zero_grad()
            output = model(train_tensor)
            total_loss,env_loss,reward_loss = compute_loss(output,train_label)
            total_loss.backward()
            optimizer.step()

            running_loss += total_loss.item()
            running_env_loss += env_loss.item()
            running_reward_loss += reward_loss.item()

            if (i+1) % args.log_interval == 0 and args.tensorboard_logger:
                writer.add_scalar('training total loss', running_loss / args.log_interval, epoch * len(train_dl) + i)
                writer.add_scalar('training env loss', running_env_loss / args.log_interval, epoch * len(train_dl) + i)
                writer.add_scalar('training reward loss', running_reward_loss / args.log_interval, epoch * len(train_dl) + i)
                running_loss = 0.0
                running_env_loss = 0.0
                running_reward_loss = 0.0
            
        if (epoch+1) % args.save_interval == 0:
            save_weight(args,model,epoch+1)
    print("Finish Training")
    save_weight(args,model,args.Epoch)

def compute_loss(pred_next_state, true_next_state, pred_reward, true_reward):
    env_fn = nn.MSELoss()
    reward_fc = nn.MSELoss()
    # loss for env head
    env_loss = env_fn(pred_next_state, true_next_state)
    
    # loss for reward head
    reward_loss = reward_fc(pred_reward, true_reward)
    
    # 合并损失（可以根据需要调整权重）
    total_loss = env_loss + reward_loss
    return total_loss,env_loss,reward_loss

if __name__ == "__main__":
    args = parser.parse_args()
    cfg = read_config(args.env_config)