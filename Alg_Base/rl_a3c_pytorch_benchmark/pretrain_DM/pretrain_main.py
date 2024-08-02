import argparse
from pretrain_utils import read_config,save_weight,get_newest_path
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
        --Epoch
        --gpu-ids
        --env-config
        --seed
        --tensorboard-logger
        --tensorboard-logdir
        --log-interval
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



def train(args,model:torch.nn.Module):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    ### tensorboard logger
    if args.tensorboard_logger:
        if not os.path.exists(args.tensorboard_logdir):
            os.makedirs(args.tensorboard_logdir)
        writer = SummaryWriter(args.tensorboard_logdir)
    ### start train config
    if args.load: # If need to load pretrain params,load the newest params in default
        if not os.path.exists(args.weight_dir) or not os.path.exists(args.weight_dir+args.TrainMode):
            raise FileNotFoundError(f"Directory:{args.weight_dir+args.TrainMode} does not exist")
        load_path = get_newest_path(args)
        model.load_state_dict(torch.load(load_path))
    model.to(device)
    model.train()
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
            if (i+1) % args.log_interval == 0 and args.tensorboard_logger:
                writer.add_scalar('training loss', running_loss / args.log_interval, epoch * len(train_dl) + i)
                running_loss = 0.0
        if (epoch+1) % args.save_interval == 0:
            save_weight(args,model,epoch+1)
    print("Finish Training")
    save_weight(args,model,args.Epoch)



def test(args,model:torch.nn.Module):
    ### get device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    ### Load model weight
    if not os.path.exists(args.weight_dir) or not os.path.exists(args.weight_dir+args.TrainMode):
            raise FileNotFoundError(f"Directory:{args.weight_dir+args.TrainMode} does not exist. Cannot Init Model weight!")
    load_path = get_newest_path(args)
    model.load_state_dict(torch.load(load_path))

    ### test set and loader
    test_dataset = DynamicsDataset(mode=args.TrainMode,train=False,shuffle=False)
    test_dl = DynamicsDataLoader(mode=args.TrainMode,dataset=test_dataset)
    criterion = torch.nn.CrossEntropyLoss()
    
    ### start test
    total_loss = 0.0 # loss sum
    correct = 0 # correct sample number
    total = 0 # number of sample
    with torch.no_grad():
        for data in test_dl:
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)
            
            # Feed forward
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            # Total loss
            total_loss += loss.item()
            
            # Accuracy
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # calculate average loss and accuracy
    average_loss = total_loss / len(test_dl) ## Average loss of batch
    accuracy = 100 * correct / total

    print(f"Average Loss: {average_loss:.4f}")
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    cfg = read_config(args.env_config)
    cfg_dict = cfg[args.TrainMode]
    model,params_opt = load_model(cfg_dict)
    train(args,model)
    test(args,model)
