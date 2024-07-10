from __future__ import print_function, division
import os
os.environ["OMP_NUM_THREADS"] = "1"
import argparse
import torch
import torch.multiprocessing as mp
from environment import general_env
from utils import read_config
from model import A3Clstm,A3ClstmE2E,A3ClstmADVOT
from train import train
from test import test
from shared_optim import SharedRMSprop, SharedAdam
#from gym.configuration import undo_logger_setup
import time

#undo_logger_setup()"
parser = argparse.ArgumentParser(description="A3C")
"""
    Argument that we need to config：
        --workers
        --gpu-ids
        --hidden-size
        --env
        --model_type
"""
parser.add_argument(
    "-w",
    "--workers",
    type=int,
    default=16,
    help="how many training processes to use (default: 16)",
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
    "-hs",
    "--hidden-size",
    type=int,
    default=256,
    help="LSTM Cell number of features in the hidden state h",
)
parser.add_argument(
    "-ev",
    "--env",
    default="Benchmark",
    help="environment to train on (default: Benchmark)",
)
parser.add_argument(
    "-model",
    "--model_type",
    type=str,
    default = "Default",
    help="type the model Type:Default or E2E or ADVOT",
)




parser.add_argument(
    "-l", "--lr", type=float, default=0.0001, help="learning rate (default: 0.0001)"
)
parser.add_argument(
    "-ec",
    "--entropy-coef",
    type=float,
    default=0.01,
    help="entropy loss coefficient (default: 0.01)",
)
parser.add_argument(
    "-vc",
    "--value-coef",
    type=float,
    default=0.5,
    help="value coefficient (default: 0.5)",
)
parser.add_argument(
    "-g",
    "--gamma",
    type=float,
    default=0.99,
    help="discount factor for rewards (default: 0.99)",
)
parser.add_argument(
    "-t", "--tau", type=float, default=1.00, help="parameter for GAE (default: 1.00)"
)
parser.add_argument(
    "-s", "--seed", type=int, default=1, help="random seed (default: 1)"
)

parser.add_argument(
    "-ns",
    "--num-steps",
    type=int,
    default=20,
    help="number of forward steps in A3C (default: 20)",
)
parser.add_argument(
    "-mel",
    "--max-episode-length",
    type=int,
    default=10000,
    help="maximum length of an episode (default: 10000)",
)
parser.add_argument(
    "-so",
    "--shared-optimizer",
    default=True,
    help="use an optimizer with shared statistics.",
)
parser.add_argument("-ld", "--load", help="load a trained model",default=True)
parser.add_argument(
    "-sm",
    "--save-max",
    # action="store_true",
    help="Save model on every test run high score matched or bested",
    default=False
)
parser.add_argument(
    "-o",
    "--optimizer",
    default="Adam",
    choices=["Adam", "RMSprop"],
    help="optimizer choice of Adam or RMSprop",
)
parser.add_argument(
    "-lmi",
    "--load-model-dir",
    default="trained_models/",
    help="folder to load trained models from",
)

parser.add_argument(
    "-lmd",
    "--load-model-idx",
    default=-1,
    help="idx of the trained model to load( Default=-1:load the last file weight in last training)",
)

parser.add_argument(
    "-smd",
    "--save-model-dir",
    default="trained_models/",
    help="folder to save trained models",
)
parser.add_argument("-lg", "--log-dir", default="logs/", help="folder to save logs")

parser.add_argument(
    "-a", "--amsgrad", action="store_true", help="Adam optimizer amsgrad parameter"
)
parser.add_argument(
    "--skip-rate",
    type=int,
    default=4,
    metavar='SR',
    help="frame skip rate (default: 4)")

parser.add_argument(
    "-tl",
    "--tensorboard-logger",
    # action="store_true",
    default=True,
    help="Creates tensorboard logger to see graph of model, view model weights and biases, and monitor test agent reward progress",
)
parser.add_argument(
    "-evc", "--env-config",
    default="./pretrain_DM/config.json",
    help="environment to crop and resize info (default: config.json)")
parser.add_argument(
    "-dss",
    "--distributed-step-size",
    type=int,
    default=[],
    nargs="+",
    help="use different step size among workers by using a list of step sizes to distributed among workers to use (default: [])",
)

# Based on
# https://github.com/pytorch/examples/tree/master/mnist_hogwild
# Training settings
# Implemented multiprocessing using locks but was not beneficial. Hogwild
# training was far superior
            # cv2.imshow("img",imageRead)
            # cv2.waitKey(0)
if __name__ == '__main__':
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    if args.gpu_ids != [-1]:
        torch.cuda.manual_seed(args.seed)
        mp.set_start_method("spawn")
    setup_json = read_config(args.env_config)
    for i in setup_json.keys():
        if i in args.env:
            env_conf = setup_json[i]
    if args.model_type == "Default":
        shared_model = A3Clstm(env_conf["State_channel"], env_conf["Action_dim"], args)
    elif args.model_type == "E2E":
        shared_model = A3ClstmE2E(env_conf["State_channel"], env_conf["Action_dim"], args)
    elif args.model_type == "ADVOT":
        shared_model = A3ClstmADVOT(env_conf["State_channel"], env_conf["Action_dim"], args)
    if args.load and os.path.exists(args.load_model_dir + "Benchmark_1.dat"):
        if args.load_model_idx == -1:
            num_file = len(os.listdir(args.load_model_dir))
            model_idx = num_file - 1 # except a markdown file
        else:
            model_idx = args.load_model_idx
        print("Loading Model: "+f"{args.load_model_dir}{args.env}_"+str(model_idx)+".dat")
        saved_state = torch.load(
            f"{args.load_model_dir}{args.env}_"+str(model_idx)+".dat",
            map_location=lambda storage, loc: storage,
        )
        shared_model.load_state_dict(saved_state)
    shared_model.share_memory()

    if args.shared_optimizer:
        if args.optimizer == 'RMSprop':
            optimizer = SharedRMSprop(shared_model.parameters(), lr=args.lr)
        if args.optimizer == 'Adam':
            optimizer = SharedAdam(
                shared_model.parameters(), lr=args.lr, amsgrad=args.amsgrad)
        optimizer.share_memory()
    else:
        optimizer = None

    processes = []
    p = mp.Process(target=test, args=(args, shared_model, env_conf))
    p.start()
    processes.append(p)
    time.sleep(0.001)
    for rank in range(0, args.workers):
        p = mp.Process(
            target=train, args=(rank, args, shared_model, optimizer, env_conf))
        p.start()
        processes.append(p)
        time.sleep(0.001)
    for p in processes:
        time.sleep(0.001)
        p.join()
