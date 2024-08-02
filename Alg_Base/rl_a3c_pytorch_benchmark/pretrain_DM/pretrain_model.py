import torch
from torchvision import models
import numpy as np
from pretrain_utils import Acquire_need_statedict,norm_col_init
import torch.nn.functional as F

WEIGHT_PATH_DICT = {
    "resnet18":"resnet18-5c106cde.pth",
    "resnet34":"resnet34-333f7ec4.pth",
}

PRETRAIN_DIR = "./pretrain_weight/"

def load_resnet(cfg_dict:list):
    Backbone = cfg_dict["Backbone"]
    
    ## Get General Tensor shape for FCN layer
    Tensor_shape = [cfg_dict["State_channel"]*cfg_dict["State_Buffer"],cfg_dict["State_size"],cfg_dict["State_size"]]
    layer_shapedict = {"Conv1":[64,2,0],"Layer1":[64,1,0],"Layer2":[128,2,0],"Layer3":[256,2,0],"Layer4":[512,2,0]}
    for layer_name in layer_shapedict.keys():
        if layer_name in Backbone:
            Tensor_shape[0] = layer_shapedict[layer_name][0]
            Tensor_shape[1] /= layer_shapedict[layer_name][1]
            Tensor_shape[2] /= layer_shapedict[layer_name][1]
            Tensor_shape[1] = int(Tensor_shape[1])+layer_shapedict[layer_name][2]
            Tensor_shape[2] = int(Tensor_shape[2])+layer_shapedict[layer_name][2]
    in_dim = Tensor_shape[0]*Tensor_shape[1]*Tensor_shape[2]

    ## Get Backbone layer
    if cfg_dict["Model_Type"] in ["resnet18"]:
        ori_model = models.resnet18(pretrained=False)
    elif cfg_dict["Model_Type"] == "resnet34":
        ori_model = models.resnet34(pretrained=False)
    layer_blockdict = {"conv1":ori_model.conv1,"bn1":ori_model.bn1,\
                       "layer1":ori_model.layer1,"layer2":ori_model.layer2,\
                       "layer3":ori_model.layer3,"layer4":ori_model.layer4}
    
    ## Init Linear Module
    lin1 = torch.nn.Linear(in_features=in_dim,out_features=cfg_dict["Hidden_dim"][0])
    lin1.bias.data.fill_(0)
    lin1.weight.data = norm_col_init(
            lin1.weight.data, 1.0
        )
    lin2 = torch.nn.Linear(in_features=cfg_dict["Hidden_dim"][0],out_features=cfg_dict["Hidden_dim"][1])
    lin2.bias.data.fill_(0)
    lin2.weight.data = norm_col_init(
            lin2.weight.data, 1.0
        )
    lin3 = torch.nn.Linear(in_features=cfg_dict["Hidden_dim"][1],out_features=cfg_dict["Action_dim"]*cfg_dict["Number_Action"])
    lin3.bias.data.fill_(0)
    lin3.weight.data = norm_col_init(
            lin3.weight.data, 1.0
        )
    
    Linear1 = torch.nn.Sequential(
        lin1,
        torch.nn.ReLU())
    Linear2 = torch.nn.Sequential(
        lin2,
        torch.nn.ReLU())
    Linear3 = torch.nn.Sequential(
        lin3,
        torch.nn.Softmax())

    backbone = torch.nn.Sequential()
    for name in layer_blockdict.keys():
        if name.title() in Backbone:
            backbone.add_module(name=name,module=layer_blockdict[name])
        else:
            pass
    head = torch.nn.Sequential()
    head.add_module("linear1",Linear1)
    head.add_module("linear2",Linear2)
    head.add_module("linear3",Linear3)
    return backbone,head

def load_selftrain(cfg_dict:list):
    ## Get General Tensor shape for FCN layer
    Tensor_shape = [cfg_dict["State_channel"]*cfg_dict["State_Buffer"],cfg_dict["State_size"],cfg_dict["State_size"]]
    conv1 = torch.nn.Conv2d(Tensor_shape[0], 32, 5, stride=1, padding=2)
    conv2 = torch.nn.Conv2d(32, 32, 5, stride=1, padding=1)
    conv3 = torch.nn.Conv2d(32, 64, 4, stride=1, padding=1)
    conv4 = torch.nn.Conv2d(64, 64, 3, stride=1, padding=1)
    
    layer_shapedict = {"Layer1":[16,4,-1],"Layer2":[32,2,-1]}
    for layer_name in layer_shapedict.keys():
        Tensor_shape[0] = layer_shapedict[layer_name][0]
        Tensor_shape[1] /= layer_shapedict[layer_name][1]
        Tensor_shape[2] /= layer_shapedict[layer_name][1]
        Tensor_shape[1] = int(Tensor_shape[1])+layer_shapedict[layer_name][2]
        Tensor_shape[2] = int(Tensor_shape[2])+layer_shapedict[layer_name][2]
    in_dim = Tensor_shape[0]*Tensor_shape[1]*Tensor_shape[2]
    ### Backbone Structure
    conv1 = torch.nn.Conv2d(Tensor_shape[0], 16,8, stride=4)
    conv2 = torch.nn.Conv2d(16, 32, 4, stride=2)

    relu_gain = torch.nn.init.calculate_gain("relu")
    conv1.weight.data.mul_(relu_gain)
    conv1.bias.data.fill_(0)
    conv2.weight.data.mul_(relu_gain)
    conv2.bias.data.fill_(0)

    backbone = torch.nn.Sequential()

    layer1 = torch.nn.Sequential()
    layer1.add_module("conv1",conv1)
    layer1.add_module("relu1",torch.nn.ReLU())

    layer2 = torch.nn.Sequential()
    layer2.add_module("conv1",conv2)
    layer2.add_module("relu1",torch.nn.ReLU())

    backbone.add_module("conv_block1",layer1)
    backbone.add_module("conv_block2",layer2)

    ## head
    lin1 = torch.nn.Linear(in_features=in_dim,out_features=cfg_dict["Hidden_dim"][0])
    lin1.bias.data.fill_(0)
    lin1.weight.data = norm_col_init(
            lin1.weight.data, 1.0
        )
    lin2 = torch.nn.Linear(in_features=cfg_dict["Hidden_dim"][0],out_features=cfg_dict["Hidden_dim"][1])
    lin2.bias.data.fill_(0)
    lin2.weight.data = norm_col_init(
            lin2.weight.data, 1.0
        )
    lin3 = torch.nn.Linear(in_features=cfg_dict["Hidden_dim"][1],out_features=cfg_dict["Action_dim"]*cfg_dict["Number_Action"]*cfg_dict["Evolution_step"])
    lin3.bias.data.fill_(0)
    lin3.weight.data = norm_col_init(
            lin3.weight.data, 1.0
        )
    
    Linear1 = torch.nn.Sequential(
        lin1,
        torch.nn.ReLU())
    Linear2 = torch.nn.Sequential(
        lin2,
        torch.nn.ReLU())
    Linear3 = torch.nn.Sequential(
        lin3
    )
    head = torch.nn.Sequential()
    head.add_module("linear1",Linear1)
    head.add_module("linear2",Linear2)
    head.add_module("linear3",Linear3)

    return backbone,head

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
        if self.Model_Type in ["resnet18","resnet34"]:
            self.backbone,self.head = load_resnet(cfg_dict)
        elif self.Model_Type == "Self_train":
            self.backbone,self.head = load_selftrain(cfg_dict)

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

def init_model(model:Dynamics_Model,pretrain_dir=PRETRAIN_DIR)->Dynamics_Model:
    if model.cfg_dict["Model_Type"] != "Self_train":
        pretrain_dir = pretrain_dir
        pretrained_dict = torch.load(pretrain_dir+WEIGHT_PATH_DICT[model.cfg_dict["Model_Type"]])
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


class CNNLSTM(torch.nn.Module):
    def __init__(self,cfg_dict:dict)->None:
        super(CNNLSTM,self).__init__()
        self.conv1 = torch.nn.Conv2d(cfg_dict["State_channel"], 32, 5, stride=1, padding=2)
        self.conv2 = torch.nn.Conv2d(32, 32, 5, stride=1, padding=1)
        self.conv3 = torch.nn.Conv2d(32, 64, 4, stride=1, padding=1)
        self.conv4 = torch.nn.Conv2d(64, 64, 3, stride=1, padding=1)
        # Get ConvNet Output size
        self.input_shape = cfg_dict["State_size"]
        conv1_outdim = int(self.input_shape/2)
        conv2_outdim = int((conv1_outdim-2)/2)
        conv3_outdim = int((conv2_outdim-1)/2)
        conv4_outdim = int(conv3_outdim/2)
        self.conv_outdim = conv4_outdim

        # Fully connected layer
        self.fc_hidden = cfg_dict["Hidden_dim"][0]
        self.output_dim = cfg_dict["Action_dim"]
        self.fcn1 = torch.nn.Linear(64*self.conv_outdim*self.conv_outdim,self.fc_hidden)
        self.fcn2 = torch.nn.Linear(self.fc_hidden,self.output_dim)
        
        relu_gain = torch.nn.init.calculate_gain("relu")
        self.conv1.weight.data.mul_(relu_gain)
        self.conv1.bias.data.fill_(0)
        self.conv2.weight.data.mul_(relu_gain)
        self.conv2.bias.data.fill_(0)
        self.conv3.weight.data.mul_(relu_gain)
        self.conv3.bias.data.fill_(0)
        self.conv4.weight.data.mul_(relu_gain)
        self.conv4.bias.data.fill_(0)

        self.train()
    def forward(self,input):
        x = F.relu(F.max_pool2d(self.conv1(input), 2, 2))
        x = F.relu(F.max_pool2d(self.conv2(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv3(x), 2, 2))
        x = F.relu(F.max_pool2d(self.conv4(x), 2, 2))
        
        x = x.view(x.size(0), -1)

        x = F.relu(self.fcn1(x))
        x = F.relu(self.fcn2(x))
        
        return F.softmax(x)

if __name__ == "__main__":
    from torchsummary import summary
    # summary(models.resnet34(pretrained=False).cuda(),input_size=(3,84,84))
    
    from pretrain_utils import read_config,Acquire_need_statedict
    cfg = read_config("./pretrain_cfg.json")
    cfg_dict = cfg["Head_backbone"]
    # model = Dynamics_Model(cfg_dict)
    # model = init_model(model)
    model = CNNLSTM(cfg_dict)
    summary(model.cuda(),input_size=(3,84,84))

    # pretrain_dir = "./Alg_Base/rl_a3c_pytorch_benchmark/pretrain_DM/pretrain_weight/"
    # pretrained_dict = torch.load(pretrain_dir+"resnet34-333f7ec4.pth")
    # print(pretrained_dict.keys())
    
    # pretrained_dict_need = Acquire_need_statedict(pretrained_dict,cfg_dict)
    # print(pretrained_dict_need.keys())


