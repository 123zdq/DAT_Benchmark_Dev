import glob
import os
import json
from pretrain_datasplit import DynamicsDataSplit
from PIL import Image
import numpy as np

ORIGIN_DATAPATH="./pretrain_DM/OriginDataset/"
DYNAMICS_DATAPATH = "./pretrain_DM/DynamicsDataset/"

class DynamicsDataset(object):
    r"""`DynamicsDataset`_ Datasets.

    Publication:

    
    Args:
        root_dir (string): Root directory of dataset where sequence
            folders exist.

    """

    def __init__(self,root_dir=ORIGIN_DATAPATH,train=True):

        super(DynamicsDataset, self).__init__()
        if train:
            self.root_dir = root_dir+"train/"
        else:
            self.root_dir = root_dir+"test/"
        self.dataset_prefix = "episode"
        self.anno_files = sorted(glob.glob(
            os.path.join(root_dir, '*/Direction_label.json')))

        self.seq_dirs = [os.path.dirname(f) for f in self.anno_files]


        self.seq_names = [os.path.basename(d) for d in self.seq_dirs]

    ### get image and label for a sequence(data of one batch)
    def __getitem__(self, index):
        r"""        
        Args:
            index (integer or string): Index of a sequence.
        
        Returns:
            tuple: (img_files, anno), where ``img_files`` is a list of
                file names and ``anno`` is a N x 4 (rectangles) numpy array.
        """
        if not self.dataset_prefix+str(index) in self.seq_names:
            raise Exception('Sequence {} not found.'.format(index))

        img_files = sorted(glob.glob(
            os.path.join(self.seq_dirs[index], '*.jpg')))

        with open(self.anno_files[index], 'r') as f:
            label_res = json.load(f)

        # assert len(img_files) == len(label_res['gt_rect'])
        assert len(label_res['gt_rect'][0]) == 4

        return img_files, label_res
    ### Return number of sequence in dataset
    def __len__(self):
        return len(self.seq_names)
    
    ### Select Empty file in filenames 
    def _filter_files(self, filenames):
        filtered_files = []
        for filename in filenames:
            with open(filename, 'r') as f:
                if f.read().strip() == '':
                    print('Warning: %s is empty.' % filename)
                else:
                    filtered_files.append(filename)

        return filtered_files
    
class DynamicsDataLoader(object):
    def __init__(self,mode:str,dataset:DynamicsDataset,cfg_dict:dict,batch_size:int,shuffle=True,root_path=DYNAMICS_DATAPATH) -> None:
        self.cfg_dict = cfg_dict
        self.State_Buffer = cfg_dict["State_Buffer"]
        self.root_path = root_path
        self.batch_volume = self.GetBatch_volume(train_dir=self.root_path+"train")
        self.dataset = dataset
        ## If it needs shuffling,run split data again
        if shuffle:
            self.datasplit = DynamicsDataSplit(mode)
            self.datasplit.Split_data()
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