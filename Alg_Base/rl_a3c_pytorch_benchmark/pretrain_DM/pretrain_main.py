import argparse
from pretrain_utils import read_config
import torch
from pretrain_model import load_model
from pretrain_dataset import DynamicsDataset,DynamicsDataLoader
import tqdm
from torch.utils.tensorboard import SummaryWriter
import os

parser = argparse.ArgumentParser(description="DynamicsModel")
"""
    Argument that we need to config：
        --TrainMode
        --gpu-ids
"""

parser.add_argument(
    "-m",
    "--TrainMode",
    type=str,
    default="Head_backbone",
    help="Train Mode Head_backbone/Head_backbone",
)

parser.add_argument(
    "-E",
    "--Epoch",
    type=int,
    default=100,
    help="Number epochs",
)

parser.add_argument(
    "-evc", "--env-config",
    default="./pretrain_DM/pretrain_cfg.json",
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
    default="./runs",
    help="dir of tensorboard logger",
)

parser.add_argument(
    "-login",
    "--log-interval",
    type=int,
    default=50,
    help="How many iteration do we log loss",
)

def train(args,model:torch.nn.Module):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    ### tensorboard logger
    if args.tensorboard_logger:
        if not os.path.exists(args.tensorboard_logdir):
            os.makedirs(args.tensorboard_logdir)
        writer = SummaryWriter(args.tensorboard_logdir)
    ### start train config
    model.to(device)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    train_dataset = DynamicsDataset(mode=args.TrainMode,train=True,shuffle=True)
    train_dl = DynamicsDataLoader(mode=args.TrainMode,dataset=train_dataset)
    for epoch in tqdm(range(args.Epoch),desc="Train Epochs"):
        running_loss = 0.0
        for i,train_data in tqdm(enumerate(train_dl),desc="Train Iteration",leave=False):
            train_tensor,train_label = train_data
            train_tensor.to(device)
            train_label.to(device)
            optimizer.zero_grad()
            output = model(train_tensor)
            loss = criterion(output,train_label)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            if i % args.log_interval == 0 and args.tensorboard_logger:
                writer.add_scalar('training loss', running_loss / args.log_interval, epoch * len(train_dl) + i)
                running_loss = 0.0
def test(testset:DynamicsDataset):
    pass



if __name__ == "__main__":
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    cfg = read_config(args.env_config)
    cfg_dict = cfg[args.TrainMode]
    model,params_opt = load_model(cfg_dict)
    dynamics_trainset = DynamicsDataset(train=True)
    dynamics_testset = DynamicsDataset(train=False)



    