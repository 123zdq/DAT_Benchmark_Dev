import json
from collections import OrderedDict
import copy
from torchvision import models
import torch

def read_config(file_path:str)->dict:
    """Read JSON config."""
    json_object = json.load(open(file_path, 'r'))
    return json_object

def dump_json(data:dict,json_path:str)->None:
    with open(json_path, 'w') as f:
        json.dump(data, f)

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


if __name__ == "__main__":
    d = {"11":1,"22":2}
    for key in d.keys():
        print(type(key))
