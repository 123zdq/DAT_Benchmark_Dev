import argparse
from pretrain_utils import read_config
import torch
from pretrain_model import load_model
from pretrain_dataset import DynamicsDataset,DynamicsDataLoader


parser = argparse.ArgumentParser(description="DynamicsModel")
"""
    Argument that we need to config：
        --gpu-ids
"""

parser.add_argument(
    "-E",
    "--Epoch",
    type=int,
    default=100,
    help="Number epochs",
)

parser.add_argument(
    "-gp",
    "--gpu-ids",
    type=int,
    default=[0],
    nargs="+",
    help="GPUs to use [-1 CPU only] (default: -1)",
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
    default=True,
    help="Creates tensorboard logger to view model weights and biases, and monitor test agent reward progress",
)

def train(args,trainset:DynamicsDataset):
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    for epoch in range(args.Epoch):
        pass

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
    


    