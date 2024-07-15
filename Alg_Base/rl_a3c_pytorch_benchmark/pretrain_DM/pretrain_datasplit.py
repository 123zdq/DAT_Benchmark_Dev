from pretrain_utils import read_config,dump_json
import os
import random
import glob
import shutil

PRETRAIN_ROOT="./pretrain_DM/"
ORIGIN_DATAPATH="./pretrain_DM/OriginDataset/"
DATA_VOLUME = ORIGIN_DATAPATH+"data_volume.json"
CFG_PATH="./pretrain_DM/pretrain_cfg.json"
DYNAMICS_DATAPATH = "./pretrain_DM/DynamicsDataset/"

class DynamicsDataSplit():
    def __init__(self,mode,data_volume=DATA_VOLUME,cfg_path=CFG_PATH,oridata_path=ORIGIN_DATAPATH) -> None:
        self.oridata_path = oridata_path
        self.volume_dict = read_config(data_volume)
        self.cfg = read_config(cfg_path)
        self.cfg_dict = self.cfg[mode]
        self.bs = self.cfg_dict["Batch_size"]
        self.statebuf = self.cfg_dict["State_Buffer"]
        self.datavolome = self.Acquire_datavolume()

        ### Get train index and test index
        self.train_idx,self.test_idx = self.Acquire_Index()

        ### make 3 dir: base/train/test
        self.base_dir = DYNAMICS_DATAPATH+"Batch{Batch_size}State{State_Buffer}".format(Batch_size=self.bs,State_Buffer=self.statebuf)
        self.train_dir = self.base_dir+"/train/"
        self.test_dir = self.base_dir+"/test/"
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        if not os.path.exists(self.train_dir):
            os.makedirs(self.train_dir)
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

    def Acquire_datavolume(self):
        datavolume = 0
        for key in self.volume_dict.keys():
            episode_len = int(self.volume_dict[key]/self.bs)
            datavolume += episode_len
        return datavolume
    
    def Acquire_Index(self):
        idx_list = list(range(1,self.datavolome+1))
        train_volume = int(self.cfg_dict["TrainSplit"]*self.datavolome)
        random.shuffle(idx_list)
        
        train_idx = idx_list[:train_volume]
        test_idx = idx_list[train_volume:]
        return train_idx,test_idx
    
    def Split_data(self):
        ### extract episode data from 
        episode_pathlib = glob.glob(self.oridata_path+"*/")
        split_idx = 0
        for episode in episode_pathlib:
            img_lib = glob.glob(episode+"*.jpg")
            ### Split image
            while (split_idx+1)*self.bs < len(img_lib):
                curr_split_img = img_lib[split_idx*self.bs,(split_idx+1)*self.bs]
                if split_idx+1 in self.train_idx:
                    curr_split_path = self.train_dir+"episode{train_idx}".format(train_idx=split_idx+1)
                    json_path = self.train_dir+"episode{train_idx}".format(train_idx=split_idx+1)+"/Direction_label.json"
                else:
                    curr_split_path = self.test_dir+"episode{test_idx}".format(test_idx=split_idx+1)
                    json_path = self.test_dir+"episode{test_idx}".format(test_idx=split_idx+1)+"/Direction_label.json"

                os.makedirs(curr_split_path)
                for img_path in curr_split_img:
                    shutil.copy(img_path,curr_split_img)
            
                ### Split label
                label_idx_list = list(range(split_idx*self.bs+1,(split_idx+1)*self.bs+1))
                label_json = episode+"Direction_label.json"
                label_dict = read_config(label_json)
                curr_label_dict = {}
                
                for index in label_idx_list:
                    label_key = "image{index}".format(index=index)
                    label_value = label_dict[label_key]
                    curr_label_dict[label_key]=label_value
                dump_json(curr_label_dict,json_path)



"""
    !!!Notice: If run in this file,make sure mode="Head_only" matches real setting in pretrain_main.py
"""
if __name__ == "__main__":
    # print(glob.glob("*/"))
    datasplit = DynamicsDataSplit(mode="Head_only")