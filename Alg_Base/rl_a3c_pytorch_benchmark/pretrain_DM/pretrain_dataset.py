import glob
import os
import json
from PIL import Image
import numpy as np
from pretrain_utils import read_config
import random
import copy
from torchvision import transforms
import torch

ORIGIN_DATAPATH="./OriginDataset/"
DYNAMICS_DATAPATH = "./DynamicsDataset/"
CFG_PATH="./pretrain_cfg.json"

class DynamicsDataset(object):
    r"""`DynamicsDataset`_ Datasets.
    
    Args:
        mode (string): training mode
        cfg_path (string): path of pretrain_cfg.json
        root_dir (string): path of DynamicsDataset
        train: whether the dataset is trained or not

    """

    def __init__(self,mode,cfg_path=CFG_PATH,root_dir=DYNAMICS_DATAPATH,train=True):
        super(DynamicsDataset, self).__init__()
        self.cfg = read_config(cfg_path)
        self.cfg_dict = self.cfg[mode]
        self.bs = self.cfg_dict["Batch_size"]
        self.statebuf = self.cfg_dict["State_Buffer"]
        self.dynamics_dir = root_dir+"Batch{Batch_size}State{State_Buffer}/".format(Batch_size=self.bs,State_Buffer=self.statebuf)
        if train:
            self.dataset_dir = self.dynamics_dir+"train/"
        else:
            self.dataset_dir = self.dynamics_dir+"test/"
        
        self.dataset_prefix = "episode"
        self.dataset_path_list = sorted(glob.glob(
            os.path.join(self.dataset_dir, '*/')))
        random.shuffle(self.dataset_path_list)

        self.img_size = self.cfg_dict["State_size"]
        self.img_channel = self.cfg_dict["State_channel"]
        if self.img_channel == 1:
            self.transform = transforms.Compose([
                transforms.Resize((self.img_size, self.img_size)),  # Resize image
                transforms.Grayscale(num_output_channels=1), # Turn RGB to Grayscale
                transforms.ToTensor(),          # Turn Image into tensor and normalize
            ])
        elif self.img_channel == 3:
            self.transform = transforms.Compose([
                transforms.Resize((self.img_size, self.img_size)),  # Resize image
                transforms.ToTensor(),          # Turn Image into tensor(HWC->CHW)
            ])
        else:
            raise ValueError("State_channel:{} is illegal! Legal value: 1(Grayscale) or 3(RGB)".format(self.img_channel))


    ### get image and label for a sequence(data of one batch)
    def __getitem__(self, index):
        r"""        
        Args:
            index (integer or string): Index of a sequence.
        
        Returns:
            tuple: (img_files, anno), where ``img_files`` is a list of
                file names and ``anno`` is a N x 4 (rectangles) numpy array.
        """
        if index < 0 or index >= len(self.dynamics_dir):
            raise Exception('Index:{} is illegal.'.format(index))

        img_files = sorted(glob.glob(
            os.path.join(self.dataset_path_list[index], '*.jpeg')))

        if self.statebuf > 1:
            total_img_list = self.imglist2statebuf(img_files)
        else:
            total_img_list = img_files
        anno_path = self.dataset_path_list[index]+"Direction_label.json"
        with open(anno_path, 'r') as f:
            label_res = json.load(f)
        label_list = list(label_res.values())
        label_list = sum(label_list, [])

        ## Get Image tensor and label tensor
        label_tensor = torch.tensor(label_list,dtype=torch.float32)
        img_PIL_dict = self.imgpath2PIL(img_files)
        full_state_tensor = self.imglist2tensor(total_img_list,img_PIL_dict)

        return full_state_tensor, label_tensor
    ### Return number of sequence in dataset
    def __len__(self):
        return len(self.dataset_path_list)
    
    ### turn img list to state buffer style
    def imglist2statebuf(self,img_list:list)->list:
        total_img_list = []
        single_img_list = [img_list[0]]*self.statebuf
        for img_path in img_list:
            single_img_list.append(img_path)
            del single_img_list[0]
            total_img_list.append(copy.deepcopy(single_img_list))
        return total_img_list
    
    def imgpath2PIL(self,path_list_single:list)->dict:
        img_PIL_dict = {}
        for img_path in path_list_single:
            img_PIL_dict[img_path] = copy.deepcopy(Image.open(img_path))
        return img_PIL_dict

    ### Path list to tensor
    def imglist2tensor(self,path_list:list,img_PIL_dict:dict)->torch.Tensor:
        full_state_list = []
        for statebuf in path_list:
            statetensor_list = []
            for img_path in statebuf:
                image = img_PIL_dict[img_path]
                image_tensor = self.transform(image)
                statetensor_list.append(copy.deepcopy(image_tensor))
            statetensor = torch.stack(statetensor_list,dim=0) # shape:(10*3,84,84)
            new_shape_tuple = (statetensor.shape[0]*statetensor.shape[1], statetensor.shape[2], statetensor.shape[3])
            statetensor = torch.reshape(statetensor, new_shape_tuple)
            full_state_list.append(copy.deepcopy(statetensor))
        full_state_tensor = torch.stack(full_state_list,dim=0)
        return full_state_tensor


    
class DynamicsDataLoader(object):
    def __init__(self,mode:str,dataset:DynamicsDataset,cfg_dict:dict,batch_size:int,shuffle=True,root_path=DYNAMICS_DATAPATH) -> None:
        self.cfg_dict = cfg_dict
        self.State_Buffer = cfg_dict["State_Buffer"]
        self.root_path = root_path
        self.batch_volume = self.GetBatch_volume(train_dir=self.root_path+"train")
        self.dataset = dataset
        
    """
        Return how many batch in trainset
    """
    def GetBatch_volume(self,train_dir)->int:
        batch_list = os.listdir(train_dir)
        return len(batch_list)
    
    def __iter__(self):
        self.curr_idx = 0
        return self
    
    def __next__(self):
        if self.curr_idx >= self.batch_volume:
            raise StopIteration
        else:
            ori_img_files,label_res = self.dataset[self.curr_idx]
            real_img_files = self.Get_real_img(ori_img_files) # list of ndarray
            self.curr_idx += 1
            return real_img_files,label_res

    def Get_real_img(self,ori_img_list:list)->list:
        first_img_np = np.array(Image.open(ori_img_list[0])) # (height, width, 3)
        real_image_list = []
        state_buffer_np = np.tile(first_img_np, (1, 1, self.State_Buffer)) # (height, width, 3*self.State_Buffer)
        for idx in range(len(ori_img_list)):
            state_buffer_del = np.delete(state_buffer_np,[0,1,2],2)
            state_buffer_np = np.concatenate((state_buffer_del, ori_img_list[idx]), axis=-1)
            real_image_list.append(state_buffer_np)
        return real_image_list
    
if __name__ == "__main__":
    ddateset = DynamicsDataset(mode="Head_backbone")
    sample_tensor = ddateset[1][1]
    # print(sample_tensor.shape)
    # print(sample_tensor)
    # import matplotlib.pyplot as plt
    # for i in range(10):
    #     plt.imshow(sample_tensor[i*3:(i+1)*3,:,:].permute(1, 2, 0).numpy())
    #     plt.show()

