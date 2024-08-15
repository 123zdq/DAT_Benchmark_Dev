from glob import glob
from typing import Dict,Tuple
import os
import shutil
from envreward_utils import dump_json

ORI_DATAPATH = "../../../Webots_Simulation/traffic_project/droneVideos/"
ENVREWARD_DATAPATH = "./EnvReward_Dataset/"
DRONE_PREFIX = "DRONE"
EPISODE_PREFIX = "episode"

"""
    Get data volume of dataset sample from simulator
    Input:
        path(str): path of origin data from simulator
    Output:
        data_volume_dict: dictation of drone and episode(e.g: Dict("Drone0",Dict("episode0",666)) )
"""
def get_datavolume(path = ORI_DATAPATH)->Dict[str,Dict[str,int]]:
    data_volume_dict = {}
    drone_list = glob(path+DRONE_PREFIX+"*/")
    drone_num = len(drone_list)
    for drone_idx in range(drone_num):
        drone_volume = {}
        droneidx_path = path+DRONE_PREFIX+str(drone_idx)+"/"
        episode_len = len(glob(droneidx_path+EPISODE_PREFIX+"*/"))
        for episode_idx in range(episode_len):
            episodeidx_path = droneidx_path+EPISODE_PREFIX+f"{episode_idx}/"
            episode_volume = len(glob(episodeidx_path+"*.jpeg"))
            drone_volume[EPISODE_PREFIX+f"{episode_idx}"] = episode_volume
        data_volume_dict[DRONE_PREFIX+str(drone_idx)] = drone_volume
    return data_volume_dict

def get_total_idx(data_volume_dict:Dict[str,Dict[str,int]],dronevolume:Dict[str,int],drone_idx:int,episode_idx:int,img_idx:int)->Tuple[str, bool]:
    real_idx = 0
    final_flag = False
    for drone_id in range(drone_idx):
        real_idx += dronevolume[DRONE_PREFIX+str(drone_id)]
    for episode_id in range(episode_idx):
        real_idx += data_volume_dict[DRONE_PREFIX+str(drone_idx)][EPISODE_PREFIX+str(episode_id)]
    if img_idx >= data_volume_dict[DRONE_PREFIX+str(drone_idx)][EPISODE_PREFIX+str(episode_idx)]:
        raise IndexError(f"Image Index Out of range! Index:{img_idx} while episode volume:{data_volume_dict[DRONE_PREFIX+str(drone_idx)][EPISODE_PREFIX+str(episode_idx)]}")
    real_idx += img_idx
    if img_idx == data_volume_dict[DRONE_PREFIX+str(drone_idx)][EPISODE_PREFIX+str(episode_idx)]-1:
        final_flag = True
    return f"{real_idx:06d}",final_flag

if __name__ == "__main__":
    MODE = "train/"
    datavolume_dict = get_datavolume()
    dronevolume = {}
    end_img_dict = {}
    for key in datavolume_dict.keys():
        dronevolume[key] = sum(datavolume_dict[key].values())
    # print(get_total_idx(datavolume_dict,dronevolume,2,0,377))
    
    if os.path.exists(ENVREWARD_DATAPATH+MODE):
        jpeg_files = glob(os.path.join(ENVREWARD_DATAPATH+MODE, "*.jpeg"))
        # Check if dataset exists
        if jpeg_files:
            for file in jpeg_files:
                os.remove(file)
        json_files = glob(os.path.join(ENVREWARD_DATAPATH+MODE, "*.json"))
        if json_files:
            for j_file in json_files:
                os.remove(j_file)
    i = 0
    total_ = []
    for drone_name in dronevolume.keys():
        drone_idx = int(drone_name.replace(DRONE_PREFIX,""))
        for episode_name in datavolume_dict[drone_name].keys():
            episode_idx = int(episode_name.replace(EPISODE_PREFIX,""))
            image_path_list = glob(ORI_DATAPATH+DRONE_PREFIX+str(drone_idx)+"/"+EPISODE_PREFIX+str(episode_idx)+"/*.jpeg")
            image_list = [os.path.basename(f) for f in image_path_list]
            for idx,img_name in enumerate(image_list):
                image_idx = int(img_name.replace(".jpeg", ""))
                real_idx_str,final_flag = get_total_idx(datavolume_dict,dronevolume,drone_idx,episode_idx,image_idx)
                total_.append(real_idx_str)
                if final_flag:
                    end_img_dict[DRONE_PREFIX+str(drone_idx)+"_"+EPISODE_PREFIX+str(episode_idx)]=ENVREWARD_DATAPATH+MODE+real_idx_str+".jpeg"
                src_path = image_path_list[idx]
                dst_path = ENVREWARD_DATAPATH+MODE+real_idx_str+".jpeg"
                if not os.path.exists(ENVREWARD_DATAPATH):
                    os.makedirs(ENVREWARD_DATAPATH)
                if not os.path.exists(ENVREWARD_DATAPATH+MODE):
                    os.makedirs(ENVREWARD_DATAPATH+MODE)
                if os.path.exists(dst_path):
                    i += 1
                shutil.copy(src_path,dst_path)
                
    json_path = ENVREWARD_DATAPATH+MODE+"end_img.json"
    dump_json(end_img_dict,json_path)
    print(len(list(total_)))
    print(len(list(set(total_))))