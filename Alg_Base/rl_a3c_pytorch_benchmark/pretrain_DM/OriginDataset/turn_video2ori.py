import os
import shutil

ORIDATASET_PATH = "./OriginDataset/"
VIDEO_PATH = "./OriginDataset/droneVideos/"
VIDEO_PREFIX = "DRONE"
EPISODE_PREFIX = "episode"
MIN_EPISODE_LEN = 500

## if exists data in OriginDataset dir rm the dirs
episode_list = os.listdir(ORIDATASET_PATH)
for episode_name in episode_list:
    if EPISODE_PREFIX in episode_name:
        shutil.rmtree(ORIDATASET_PATH+episode_name)

video_folders = os.listdir(VIDEO_PATH)
video_folder_list = []
for folder_name in video_folders:
    if VIDEO_PREFIX in folder_name:
        video_folder_list.append(folder_name)

episode_idx = 0
for folder_name in video_folder_list:
    folder_path = VIDEO_PATH+folder_name
    drone_episode_list = os.listdir(folder_path)
    for idx in range(len(drone_episode_list)):
        episode_path = folder_path+"/"+drone_episode_list[idx]
        episode_path_dst = ORIDATASET_PATH+"episode{}".format(episode_idx)
        ## Judge whether the folder is empty
        if len(os.listdir(episode_path)) > MIN_EPISODE_LEN:
            shutil.copytree(episode_path,episode_path_dst)
            os.rename(episode_path_dst+"/mark.json",episode_path_dst+"/Direction_label.json")
            episode_idx += 1

