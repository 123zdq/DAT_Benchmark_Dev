import os
import json

ORIDATASET_PATH = "./OriginDataset/"
EPISODE_PREFIX = "episode"

data_volume_dict = {}

num_episode = 0
oridata_list = os.listdir(ORIDATASET_PATH)
for episode_name in oridata_list:
    if EPISODE_PREFIX in episode_name:
        num_episode += 1

for episode_idx in range(num_episode):
    file_list = os.listdir(ORIDATASET_PATH+EPISODE_PREFIX+str(episode_idx))
    num_img = len(file_list)-1
    data_volume_dict[EPISODE_PREFIX+str(episode_idx)] = num_img


json_path = ORIDATASET_PATH+"data_volume.json"
if os.path.exists(json_path):
    os.unlink(json_path)
with open(json_path, 'w') as json_file:
    json.dump(data_volume_dict, json_file)

    