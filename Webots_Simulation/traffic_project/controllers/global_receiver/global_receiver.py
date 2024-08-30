'''
Author: lu 2231625449@qq.com
Date: 2024-04-10 21:18:38
LastEditors: lu 2231625449@qq.com
LastEditTime: 2024-08-27 12:11:14
FilePath: /UAV_Follow_Env/Webots_Simulation/traffic_project/controllers/global_receiver/global_receiver.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''
"""global_receiver controller."""

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot
from controller import Receiver, Emitter
from controller import Supervisor
import struct
import receiveSocket
import randomorder
import drone_manager
import MultiPortRecv
import time
import json
import random
import os
import platform
import transforms3d as tfs
import sys
sys.path.append("../../config")
import safetyCheck

def check(input:str, container:list):
        is_contain = False
        for i in range(len(container)):
            if input == container[i]:
                is_contain = True
        if is_contain == True:
            return input
        else:
            return container[0]


# check running system
System = platform.system()

# create the Robot instance.
robot = Supervisor()
run_mode = robot.getCustomData()

# get complete path of world file
world_path = robot.getWorldPath()

# read json config file
with open('../../config/env_config.json', 'r') as file:
    configData = json.load(file)
    file.close()
    
# safety check
configData["Simulation_Mode"] = check(str(configData["Simulation_Mode"]),safetyCheck.SIMULATION_MODE)
configData["Tracking_Object"] = check(configData["Tracking_Object"],safetyCheck.TRACKING_OBJECT)
configData["Reward_Config"]["reward_mode"] = check(configData["Reward_Config"]["reward_mode"],safetyCheck.REWARD_MODE)
configData["Sumo_Params"]["car_type"] = check(configData["Sumo_Params"]["car_type"],safetyCheck.CAR_TYPE)
    
# set config data to sumo interface
SUMO_Interface = robot.getFromDef("SUMO_INTERFACE")
if configData["Tracking_Object"] == "SUMO_VEHICLE":
    SUMO_Interface.getField("maxVehicles").setSFInt32(configData["Sumo_Params"]["max_sumo_car"])
else:
    SUMO_Interface.getField("maxVehicles").setSFInt32(0)
randomSeed = random.randint(1, 100)
SUMO_Interface.getField("seed").setSFInt32(randomSeed)

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())
# emitter node
emitter = robot.getDevice("emitter")

# the global init state is one
global_state = 1
global_init = False

# seperate different simulation modes
FollowPort = None
file_path = world_path[:-4] + '_net'
if configData["Simulation_Mode"] == "demo":
    drone_manager.droneManager(robot, timestep, 0, [], configData, [], {}, [False])
    data = [0.] * 6
    data[4] = -1 # inited to -1
    data[5] = -1
    # FollowPort = receiveSerial.SerialPort(6,data)
    FollowPort = receiveSocket.SocketPort(6,data,7790)
    getFromPort = [0.] * FollowPort.data_size
    getFromPortStr = ["0"] * FollowPort.data_size
    getFromPort[4] = -1
    getFromPort[5] = -1
    if configData["Tracking_Object"] == "SUMO_VEHICLE":
        # if configData["Sumo_Random_Mode"] == 1:
        #     randomorder.sumo_rou_random(file_path, int(4), configData["Sumo_Params"])
        # elif configData["Sumo_Random_Mode"] == 2:
        #     randomorder.sumo_rou_random_os(file_path, int(4), System, configData["Sumo_Params"])
        randomorder.sumo_rou_random_os(file_path, int(4), System, configData["Sumo_Params"])
elif configData["Simulation_Mode"] == "train":
    if System == "Linux":
        os.system("rm -rf ../../Files2Alg/*.txt")
        os.system("rm -rf ../../Files2Alg/*.jpeg")
        os.system("rm -rf ../../cache/*.txt")
        os.system("rm -rf ../../cache/*.jpeg")
    elif System == "Windows":
        os.system("del /s /q /f ../../Files2Alg/*.txt")
        os.system("del /s /q /f ../../Files2Alg/*.jpeg")
        os.system("del /s /q /f ../../cache/*.txt")
        os.system("del /s /q /f ../../cache/*.jpeg")
    # multiple communications
    multiCom = MultiPortRecv.MultiProcessRecv(configData["Socket_Ip"],5,configData["Control_Frequence"],configData["Config_Agen_Num_Port"],configData["Verbose"])
    multiCom.main()
    # activate map random init
    if configData["Tracking_Object"] == "SUMO_VEHICLE":
        # if configData["Sumo_Random_Mode"] == 1:
        #     randomorder.sumo_rou_random(file_path, int(multiCom.Number_process*3), configData["Sumo_Params"])
        # elif configData["Sumo_Random_Mode"] == 2:
        #     randomorder.sumo_rou_random_os(file_path, int(multiCom.Number_process*3), System, configData["Sumo_Params"])
        randomorder.sumo_rou_random_os(file_path, int(multiCom.Number_process*3), System, configData["Sumo_Params"])
    # according to the number of process ,establish multiple objects
    droneM = []
    # sumo shared storage section
    sumoList = []
    sumoDictionary = {}
    sumoGetCarFlag = [False]*multiCom.Number_process
    for i in range(multiCom.Number_process):
        droneM.append(drone_manager.droneManager(robot, timestep, i, multiCom, configData, sumoList, sumoDictionary, sumoGetCarFlag))
elif configData["Simulation_Mode"] == "video":
    # clear space
    delete_count = 0
    while os.path.exists("../../droneVideos/DRONE"+str(delete_count)):
        if System == "Linux":
            os.system("rm -rf ../../droneVideos/DRONE" + str(delete_count))
        elif System == "Windows":
            os.system("del /s /q /f ../../droneVideos/DRONE" + str(delete_count))
        delete_count = delete_count + 1
    # create directories to contain frames
    for i in range(configData["Out_Video"]["channels"]):
        os.mkdir("../../droneVideos/DRONE"+str(i))    
        
    # activate map random init
    if configData["Tracking_Object"] == "SUMO_VEHICLE":
        # if configData["Sumo_Random_Mode"] == 1:
        #     randomorder.sumo_rou_random(file_path, int(configData["Out_Video"]["channels"]*2), configData["Sumo_Params"])
        # elif configData["Sumo_Random_Mode"] == 2:
        #     randomorder.sumo_rou_random_os(file_path, int(configData["Out_Video"]["channels"]*2), System, configData["Sumo_Params"])
        randomorder.sumo_rou_random_os(file_path, int(configData["Out_Video"]["channels"]*2), System, configData["Sumo_Params"])
    # according to the number of process ,establish multiple objects
    droneM = []
    # sumo shared storage section
    sumoList = []
    sumoDictionary = {}
    sumoGetCarFlag = [False]*configData["Out_Video"]["channels"]
    for i in range(configData["Out_Video"]["channels"]):
        droneM.append(drone_manager.droneManager(robot, timestep, i, None, configData, sumoList, sumoDictionary, sumoGetCarFlag))
    

# Main loop:
# - perform simulation steps until Webots is stopping the controller
if configData["Simulation_Mode"] == "demo":
    while robot.step(timestep) != -1:
        getFromPort, getFromPortStr = FollowPort.read()
        for i in range(FollowPort.data_size):
            if getFromPort[i] == None:
                if i < 4:
                    getFromPort[i] = 0
                else:
                    getFromPort[i] = -1
        message = struct.pack("ffffff",getFromPort[0],getFromPort[1],getFromPort[2],getFromPort[3],getFromPort[4],getFromPort[5])
        emitter.setChannel(1)
        emitter.send(message)
        pass
elif configData["Simulation_Mode"] == "train":
    while True:
        if global_init == False:
            global_init = True
            init_count = 0
            # firstly run steps for sumo to prepare for the cars
            while init_count < (int(configData["Drone_Random_Config"]["start_time_bias_ms"]) + 6*multiCom.Number_process):
                init_count = init_count + 1
                while robot.step(timestep) == -1: # step until simulation is running
                    pass 
            for drone in droneM:
                drone.loop.start()
        
        # if step count larger than 0 then run a real step
        run_step = False
        for i in range(multiCom.Number_process):
            if multiCom.is_step[i] > 0:
                run_step = True
            
        if run_step == True:
            while robot.step(timestep) == -1: # step until simulation is running
                pass
            for drone in droneM:
                drone.runMultiState(1)
elif configData["Simulation_Mode"] == "video":
    while True:
        if global_init == False:
            global_init = True
            init_count = 0
            # firstly run steps for sumo to prepare for the cars
            while init_count < (int(configData["Drone_Random_Config"]["start_time_bias_ms"]) + 4*configData["Out_Video"]["channels"]):
                init_count = init_count + 1
                while robot.step(timestep) == -1: # step until simulation is running
                    pass 
            for drone in droneM:
                drone.videoloop.start()
        
        # if step count larger than 0 then run a real step
        run_step = False
        for i in range(configData["Out_Video"]["channels"]):
            run_step = True
            
        if run_step == True:
            while robot.step(timestep) == -1: # step until simulation is running
                pass
            for drone in droneM:
                drone.runMultiState(1)

                
        

                
# Enter here exit cleanup code.
