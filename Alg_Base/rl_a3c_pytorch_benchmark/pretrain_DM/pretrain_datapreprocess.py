from pretrain_utils import read_config,dump_json
import pandas as pd
import os
import glob

PRETRAIN_ROOT="./pretrain_DM/"
ORIGIN_DATAPATH="./pretrain_DM/OriginDataset/"

DATA_VOLUME = ORIGIN_DATAPATH+"data_volume.json"
CFG_PATH="./pretrain_DM/pretrain_cfg.json"


class DataPreprocessing():
    def __init__(self,mode,cfg_path=CFG_PATH,ori_datapath=ORIGIN_DATAPATH) -> None:
        self.cfg = read_config(cfg_path)
        self.cfg_dict = self.cfg[mode]
        self.evo_step = self.cfg_dict["Evolution_step"]
        self.ori_datapath = ori_datapath

    def read_csv(self,csv_path:str):
        label_df = pd.read_csv(csv_path,sep=',',header='infer')
        img_list = list(label_df["name"])
        del img_list[-self.evo_step:]
        label_list = list(label_df["label"])
        return img_list,label_list
    
    def Acquire_full_label(self,img_list:list,label_list):
        full_label_list = []
        for idx in range(len(img_list)):
            idx_label = []
            for i in range(idx,self.evo_step):
                idx_label.append(label_list[i])
            full_label_list.append(idx_label)
        return full_label_list
    
    def data_preprocess(self):
        episode_list = glob.glob(self.ori_datapath+"*/")
        for episode in episode_list:
            csv_path = episode+"Direction_label.csv"
            json_path = episode+"Direction_label.json"
            img_list,label_list = self.read_csv(csv_path)
            full_label_list = self.Acquire_full_label(img_list,label_list)
            Direction_label_dict = dict(zip(img_list,full_label_list))
            dump_json(Direction_label_dict,json_path)

    
            
if __name__ == "__main__":
    label_df = pd.read_csv("C:\\Users\\20669\\Desktop\\test.csv",sep=',',header='infer')
    n_list = list(label_df["name"])
    l_list = list(label_df["label"])
    print(dict(zip(n_list,l_list)))
