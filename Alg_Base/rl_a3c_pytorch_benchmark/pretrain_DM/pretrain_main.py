import argparse
from pretrain_utils import read_config
import torch
from pretrain_model import load_model


parser = argparse.ArgumentParser(description="DynamicModel")
"""
    Argument that we need to config：
        --TrainMode
        --gpu-ids
"""
parser.add_argument(
    "-Mode",
    "--TrainMode",
    type=str,
    default="Head_only",
    help="Training Mode:Head_only(Only Train Dynamics Model Head);Head_backbone(Train Both Head and Backbone)",
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
    default="./pretrain_cfg.json",
    help="pretrain Dynamics Model info (default: pretrain_cfg.json)")

parser.add_argument(
    "-s", "--seed", type=int, default=1, help="random seed (default: 1)"
)

if __name__ == "__main__":
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    cfg = read_config(args.env_config)
    cfg_dict = cfg[args.TrainMode]
    model,params_opt = load_model(cfg_dict)