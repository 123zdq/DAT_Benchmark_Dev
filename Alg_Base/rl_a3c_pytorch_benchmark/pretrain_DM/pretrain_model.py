import torch
from torchvision import models
import numpy as np
from pretrain_utils import Acquire_need_statedict,load_resnet18

class Dynamics_Model(torch.nn.Module):
    def __init__(self,cfg_dict:dict) -> None:
        super(Dynamics_Model, self).__init__()
        self.cfg_dict = cfg_dict
        self.Model_Type = self.cfg_dict["Model_Type"]
        self.State_BufferSize = self.cfg_dict["State_Buffer"]
        self.Action_BufferSize = self.cfg_dict["Action_Buffer"]
        self.State_size = self.cfg_dict["State_size"]
        self.State_channel = self.cfg_dict["State_channel"]
        self.Action_dim = self.cfg_dict["Action_dim"]

        ## Model Init
        if self.Model_Type == "resnet18":
            self.backbone,self.head = load_resnet18(cfg_dict)
        elif self.Model_Type == "Self_train":
            pass
        elif self.Model_Type == "resnet34":
            self.model = models.resnet34(pretrained=False)

        ## State Buffer Init
        self.State_Buffer = np.zeros((self.State_BufferSize,self.State_size,self.State_size,self.State_channel))

        ## Action Buffer Init
        self.Action_Buffer = np.zeros((self.Action_BufferSize,1))

    def forward(self,x:torch.Tensor):
        x = self.backbone(x)
        x = x.view(x.size(0), -1)
        print(x.shape)
        x = self.head(x)
        return x

def init_model(model:Dynamics_Model)->Dynamics_Model:
    if model.cfg_dict["Model_Type"] != "Self_train":
        pretrain_dir = "./Alg_Base/rl_a3c_pytorch_benchmark/pretrain_DM/pretrain_weight/"
        pretrained_dict = torch.load(pretrain_dir+"resnet18-5c106cde.pth")
        pretrained_dict_need = Acquire_need_statedict(pretrained_dict,model.cfg_dict)
        model.load_state_dict(pretrained_dict_need,strict=False)
        for name, value in model.named_parameters():
            if name[9:].lower() in pretrained_dict_need.keys() or name[5:].lower() in pretrained_dict_need.keys():
                value.requires_grad = False
        return model 
    else:
        return model      

def check_require_grad(model:Dynamics_Model):
    for name, param in model.named_parameters():
        if param.requires_grad:
            print(name+" requires_grad\n")
        else:
            print(name+" does not requires_grad\n")

def load_model(cfg_dict:dict):
    model = Dynamics_Model(cfg_dict)
    model = init_model(model)
    params_opt = filter(lambda p: p.requires_grad, model.parameters())
    return model,params_opt


if __name__ == "__main__":
    from torchsummary import summary
    # summary(models.resnet18(pretrained=False).cuda(),input_size=(3,84,84))
    
    from pretrain_utils import read_config,Acquire_need_statedict
    cfg = read_config("./pretrain_DM/pretrain_cfg.json")
    cfg_dict = cfg["Head_only"]
    model = Dynamics_Model(cfg_dict)
    model = init_model(model)
    
    summary(model.cuda(),input_size=(3,84,84))

    # pretrain_dir = "./Alg_Base/rl_a3c_pytorch_benchmark/pretrain_DM/pretrain_weight/"
    # pretrained_dict = torch.load(pretrain_dir+"resnet18-5c106cde.pth")
    # pretrained_dict_need = Acquire_need_statedict(pretrained_dict,cfg_dict)
    
    # print(pretrained_dict_need.keys())


