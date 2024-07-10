import json
from collections import OrderedDict
import copy
from torchvision import models
import torch

def read_config(file_path:str):
    """Read JSON config."""
    json_object = json.load(open(file_path, 'r'))
    return json_object

def judge_state_dict(key:str,cfg_dict:dict)->bool:
    sub_str3 = key[:3]
    sub_str5 = key[:5]
    sub_str6 = key[:6]
    Backbone = cfg_dict["Backbone"]
    if sub_str3 in Backbone or sub_str5 in Backbone or sub_str6 in Backbone:
        return True
    else:
        return False
    
def Acquire_need_statedict(pretrained_dict:OrderedDict,cfg_dict:dict)->OrderedDict:
    pretrained_dict_need = copy.deepcopy(pretrained_dict)
    for key in pretrained_dict.keys():
        if judge_state_dict(key.title(),cfg_dict):
            pass
        else:
            pretrained_dict_need.pop(key.title().lower())
    pretrained_dict_need2 = copy.deepcopy(pretrained_dict_need)
    for key_need in pretrained_dict_need.keys():
        key_need2 = "backbone."+key_need
        pretrained_dict_need2[key_need2] = pretrained_dict_need[key_need]
        pretrained_dict_need2.pop(key_need)
        # print(key_need)
    return pretrained_dict_need2


def norm_col_init(weights, std=1.0):
    x = torch.randn(weights.size())
    x *= std / torch.sqrt((x**2).sum(1, keepdim=True))
    return x

def load_resnet18(cfg_dict:list):
    Backbone = cfg_dict["Backbone"]
    
    ## Get General Tensor shape for FCN layer
    Tensor_shape = [cfg_dict["State_channel"]*cfg_dict["State_Buffer"],cfg_dict["State_size"],cfg_dict["State_size"]]
    layer_shapedict = {"Conv1":[64,2],"Layer1":[64,1],"Layer2":[128,2],"Layer3":[256,2],"Layer4":[512,2]}
    for layer_name in layer_shapedict.keys():
        if layer_name in Backbone:
            Tensor_shape[0] = layer_shapedict[layer_name][0]
            Tensor_shape[1] /= layer_shapedict[layer_name][1]
            Tensor_shape[2] /= layer_shapedict[layer_name][1]
            Tensor_shape[1] = int(Tensor_shape[1])
            Tensor_shape[2] = int(Tensor_shape[2])
    in_dim = Tensor_shape[0]*Tensor_shape[1]*Tensor_shape[2]

    ## Get Backbone layer
    ori_model = models.resnet18(pretrained=False)
    layer_blockdict = {"conv1":ori_model.conv1,"bn1":ori_model.bn1,\
                       "layer1":ori_model.layer1,"layer2":ori_model.layer2,\
                       "layer3":ori_model.layer3,"layer4":ori_model.layer4}
    
    ## Init Linear Module
    lin1 = torch.nn.Linear(in_features=in_dim,out_features=512)
    lin1.bias.data.fill_(0)
    lin1.weight.data = norm_col_init(
            lin1.weight.data, 1.0
        )
    lin2 = torch.nn.Linear(in_features=512,out_features=64)
    lin2.bias.data.fill_(0)
    lin2.weight.data = norm_col_init(
            lin2.weight.data, 1.0
        )
    lin3 = torch.nn.Linear(in_features=64,out_features=cfg_dict["Action_dim"])
    lin3.bias.data.fill_(0)
    lin3.weight.data = norm_col_init(
            lin3.weight.data, 1.0
        )
    
    Linaer1 = torch.nn.Sequential(
        lin1,
        torch.nn.ReLU())
    Linaer2 = torch.nn.Sequential(
        lin2,
        torch.nn.ReLU())
    Linaer3 = torch.nn.Sequential(
        lin3,
        torch.nn.Softmax())

    backbone = torch.nn.Sequential()
    for name in layer_blockdict.keys():
        if name.title() in Backbone:
            backbone.add_module(name=name,module=layer_blockdict[name])
        else:
            pass
    head = torch.nn.Sequential()
    head.add_module("linear1",Linaer1)
    head.add_module("linear2",Linaer2)
    head.add_module("linear3",Linaer3)
    return backbone,head

def load_selftrain(cfg_dict:list):
    conv1 = torch.nn.Conv2d(cfg_dict, 32, 5, stride=1, padding=2)
    conv2 = torch.nn.Conv2d(32, 32, 5, stride=1, padding=1)
    conv3 = torch.nn.Conv2d(32, 64, 4, stride=1, padding=1)
    conv4 = torch.nn.Conv2d(64, 64, 3, stride=1, padding=1)

if __name__ == "__main__":
    d = {"11":1,"22":2}
    for key in d.keys():
        print(type(key))
