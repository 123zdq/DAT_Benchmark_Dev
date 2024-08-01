"""
    This Script is used to rapidly generate Dynamics Dataset that can be loaded by Dataset and Dataloader
"""

from turn_video2ori import Generate_Video2Ori
from generate_datavolume import Generate_Ori2DataVolume
### Append parent dir to sys_path
import sys
import os
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PARENT_DIR)
from pretrain_datasplit import DynamicsDataSplit
import argparse

parser = argparse.ArgumentParser(description="Data Generation Argparser")

# Add Arguments
parser.add_argument('-m', '--mode', type=str,default="Head_backbone", help="Config train mode Head_backbone/Head_only")

# Parse arguments
args = parser.parse_args()

## Begin split data
Generate_Video2Ori()
Generate_Ori2DataVolume()
dyna_datasplit = DynamicsDataSplit(args.mode)
dyna_datasplit.Split_data()
dyna_datasplit.Check_split()