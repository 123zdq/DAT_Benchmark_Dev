from envreward_utils import read_config
from glob import glob
import os 
from torchvision import transforms
from PIL import Image
from torch.utils.data import Dataset

CFG_PATH = "./envreward_cfg.json"
ENVREWARD_DATAPATH = "./EnvReward_Dataset/"
END_IMAGE = "end_img.json"

class EnvRewardDataset(Dataset):

    def __init__(self,cfg_path=CFG_PATH,root_dir=ENVREWARD_DATAPATH,train=True):
        super(EnvRewardDataset, self).__init__()
        self.cfg_dict = read_config(cfg_path)
        self.dynamics_dir = root_dir
        self.train = train
        if self.train:
            self.dataset_dir = self.dynamics_dir+"train/"
        else:
            self.dataset_dir = self.dynamics_dir+"test/"
        

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
        
        self.data_end_dict = read_config(self.dataset_dir+END_IMAGE)
        self.end_image_list = list(self.data_end_dict.values())
        
        self.total_image_list = glob(self.dataset_dir+"*.jpeg")
        
        # print(self.total_image_list[:10])
        
        self.order_image_list = list(set(self.total_image_list)-set(self.end_image_list))
        self.order_image_list.sort()

    def __len__(self):
        # Dataset Size
        return len(self.order_image_list)
    
    def __getitem__(self, idx):
        # 获取数据和标签
        image_path = self.order_image_list[idx]
        next_img_path = self.get_next_img(image_path)

        image = Image.open(image_path)
        next_image = Image.open(next_img_path)

        # 如果指定了transform，应用到数据上
        if self.transform:
            image_tensor = self.transform(image)
            next_image_tensor = self.transform(next_image)
        return image_tensor,next_image_tensor

    def get_next_img(self,image_path:str)->str:
        dir_name, file_name = os.path.split(image_path)
        idx_str = file_name[:-5]
        new_idx_ = int(idx_str)+1
        file_name = file_name.replace(idx_str,f"{new_idx_:06d}")
        next_img_path = os.path.join(dir_name, file_name)
        return next_img_path


if __name__ == "__main__":
    envrewardd = EnvRewardDataset()
    print(len(envrewardd.order_image_list))
    print(envrewardd.get_next_img(envrewardd.order_image_list[2]))
        
    