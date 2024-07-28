'''
Author: lu 2231625449@qq.com
Date: 2024-04-30 19:17:23
LastEditors: lu 2231625449@qq.com
LastEditTime: 2024-07-28 19:21:20
FilePath: /UAV_Follow_Env/Webots_Simulation/traffic_project/controllers/global_receiver/drone_manager.py
Description: 

Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
'''
import sys
sys.path.append("../../libraries")
sys.path.append("../SUMOGod")
from controller import robot
from controller import Receiver, Emitter
from controller import Supervisor
import struct
import SUMOGod
import threading
import time
import random
import os
import platform
import logging
import MultiPortRecv
import socket


class droneManager:
    '''
    description: a manager to support an agent including communication, random init and control
    param {*} self
    param {Supervisor} supervisor: a webots supervisor node
    param {*} timeStep: simulation running timestep
    param {*} id: drone id
    param {*} recCtrlPort: multiple process communication port
    param {*} configData: simulation config data
    param {*} sumoList: a list that manage target car
    param {*} sumoDict: a dictionary that manage target car
    param {*} sumoGetFlag: a list that judges whether the cars are allocated 
    return {*}
    '''    
    def __init__(self, supervisor:Supervisor, timeStep, id, recCtrlPort, configData, sumoList, sumoDict, sumoGetFlag):
        # get supervisor node
        self.supervisor = supervisor
        # get timeStep value
        self.timeStep = timeStep
        # get communication port
        self.recCtrlPort = recCtrlPort
        # get drone id
        self.id = id
        # get configuration
        self.configData = configData
        # define sumoGod
        self.sumoGod = SUMOGod.getSumoCarNode(id, sumoList, sumoDict, sumoGetFlag)
        # create new drone node
        self.droneDef = 'DRONE' + str(id)
        droneString = 'DEF ' + self.droneDef + ' M100 { controller "drone_ctrl2" customData "online" supervisor TRUE }'
        rootChildrenField = self.supervisor.getRoot().getField('children')
        rootChildrenField.importMFNodeFromString(id, droneString)
        self.drone = self.supervisor.getFromDef(self.droneDef)
        droneTrV = self.drone.getField('translation').getSFVec3f()
        droneTrV[0] = droneTrV[0] + 1 * id
        droneTrV[1] = droneTrV[1] + 1 * id
        self.drone.getField('translation').setSFVec3f(droneTrV)
        # Logging
        MultiPortRecv.setup_logger("drone"+str(id),"../../logs/Agent"+str(id)+".log")
        self.logger = logging.getLogger("drone"+str(id))
        # init communications
        self.getFromActionPort = [0.] * 5
        # init action files
        self.actionActivateFile(0)
        # prepare main_loop state machine status
        self.machine_state = 1
        # multiprocess actuate flag
        self.multi_state = 0
        # establish drone manager threading
        self.loop = threading.Thread(target=self.mainLoop)
        self.videoloop = threading.Thread(target=self.mainLoopForVideo)
        
    '''
    description: update action data from multiple ALG
    param {*} self
    return {*}
    '''
    def actionUpdate(self):
        self.getFromActionPort = self.recCtrlPort.getAction(self.id)      
        
    '''
    description: use emitter to set action to drone controller
    param {*} self
    param {Emitter} emitter
    param {*} step_count
    return {*}
    '''
    def actionActivate(self, emitter:Emitter, step_count):
        action_message = struct.pack("fffff",self.getFromActionPort[0],self.getFromActionPort[1],self.getFromActionPort[2],self.getFromActionPort[3],step_count)
        emitter.send(action_message) 
        
        
    '''
    description: use file io to set action to drone controller
    param {*} self
    param {*} step_count
    return {*}
    '''
    def actionActivateFile(self, step_count):
        with open("../../cache/" + self.droneDef + "_Global2Ctrl.txt", "w") as f:
            actionStr = str(self.getFromActionPort[0]) + "\n" + str(self.getFromActionPort[1]) + "\n" + str(self.getFromActionPort[2]) + "\n" + str(self.getFromActionPort[3]) + "\n" + str(step_count) + "\n"
            f.write(actionStr)
            f.close()
        
        
    '''
    description: return state reward done / reward params / point cloud / image to ALG
    param {*} self
    return {*}
    '''
    def returnState(self, step_count):
        self.logger.info(str(step_count))
        # send state reward and done
        with open("../../cache/" + self.droneDef + "_Ctrl2Global.txt", "r") as f:
            data = f.readline()
            f.close()
        while len(data) < 2:
            with open("../../cache/" + self.droneDef + "_Ctrl2Global.txt", "r") as f:
                data = f.readline()
                f.close()
        self.logger.info(data)
        self.recCtrlPort.sendState(data,self.id,"../../Files2Alg/" + self.droneDef + "_Ctrl2Global.txt")
        # if config files defines,then send below data
        if self.configData["Customized_Rewards"]:
            with open("../../cache/" + self.droneDef + "_Ctrl2GlobalR.txt", "r") as f:
                data = f.readline()
                f.close()
            while len(data) < 2:
                with open("../../cache/" + self.droneDef + "_Ctrl2GlobalR.txt", "r") as f:
                    data = f.readline()
                    f.close()
            self.logger.info(data)
            self.recCtrlPort.sendMakeReward(data,self.id,"../../Files2Alg/" + self.droneDef + "_RewardParams.txt")
        if self.configData["Lidar_Enable"]:
            with open("../../cache/" + self.droneDef + "_LidarCloud.txt", "r") as f:
                data = f.readline()
                f.close()
            while len(data) < 2:
                with open("../../cache/" + self.droneDef + "_LidarCloud.txt", "r") as f:
                    data = f.readline()
                    f.close()
            self.recCtrlPort.sendPointCloud(data,self.id,"../../Files2Alg/" + self.droneDef + "_PointCloud.txt")
        # send camera graphs
        self.recCtrlPort.sendImage("../../cache/" + self.droneDef + "_VideoFrame.jpeg",
                                   self.id,
                                   "../../Files2Alg/" + self.droneDef + "_VideoFrame.jpeg",
                                   "../../Files2Alg/" + self.droneDef + "_VideoFrame.txt")
            
    '''
    description: return only image to ALG
    param {*} self
    return {*}
    '''
    def returnOnlyImage(self):
        # send camera graphs
        self.recCtrlPort.sendImage("../../cache/" + self.droneDef + "_VideoFrame.jpeg",
                                   self.id,
                                   "../../Files2Alg/" + self.droneDef + "_VideoFrame.jpeg",
                                   "../../Files2Alg/" + self.droneDef + "_VideoFrame.txt")
            
    '''
    description: drone get target car init
    param {*} self
    return {*}
    '''
    def init(self):
        if self.configData["Drone_Random_Config"]["height_random"] == False:
            transScale = self.configData["Drone_Random_Config"]["height_fixed"]
        else:
            transScale = random.uniform(self.configData["Drone_Random_Config"]["height_random_min"],self.configData["Drone_Random_Config"]["height_random_max"])
        transVector = [-2/3*transScale, 0, transScale]
        if self.configData["Drone_Random_Config"]["direction_random"] == False:
            rotateAngle = 0
        else:
            rotateAngle = random.uniform(self.configData["Drone_Random_Config"]["direction_random_min"],self.configData["Drone_Random_Config"]["direction_random_max"])
        return self.sumoGod.SingleProcessRandomInit(self.supervisor, self.timeStep, self.drone, transVector, rotateAngle)
        
    '''
    description: reset car controller
    param {*} self
    return {*}
    '''
    def reset(self):
        print("\nid:   ",self.id,"    reset: rrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
        self.drone.restartController()
        
    '''
    description: send socket to update machine state
    param {*} self
    return {*}
    '''
    def updateMachineState(self,filePath:str=None):
        self.recCtrlPort.sendMachine(self.machine_state,self.id,filePath)
        
    '''
    description: 1.Drone manager mainLoop, which manage the state machine.
                 2.Firstly init the drone and random select a available target car. Move the drone above it.
                 3.Then run into the step mode, which continuously communicates with ALG and controlled by ALG.
                 4.While satisfying the reset condition, get into reset mode and reset.
                 5.After reset, return to the init mode
    param {*} self
    return {*}
    '''
    def mainLoop(self):
        self.initTime = time.time()
        self.lastTime = self.initTime
        while True:
            self.initTime = time.time()
            self.updateMachineState("../../cache/" + self.droneDef + "_MachineState.txt")
            self.recCtrlPort.keepSocketRunning()
            self.actionUpdate()
            
            if self.multi_state == 1:
                if self.machine_state == 1:
                    self.recCtrlPort.is_reset[self.id] = False
                    self.recCtrlPort.is_step[self.id] = 0
                    self.step_count = 0
                    if self.init():
                        # self.logger.info("drone finish sumo init")
                        # self.returnOnlyImage()
                        self.returnState(self.step_count)
                        self.machine_state = 2 # init come to an end and transfer to steps
                elif self.machine_state == 2:
                    self.sumoGod.ResetSumoDictionary()
                    if self.recCtrlPort.is_reset[self.id] == True and self.step_count > 100:
                        # self.logger.info("begin to reset")
                        self.reset()
                        # self.logger.info("finish reset")
                        self.sumoGod.delectDefList()
                        self.recCtrlPort.is_reset[self.id] = False
                        self.machine_state = 1 # remember to reset
                    else:
                        self.actionActivateFile(self.step_count)
                        if self.recCtrlPort.is_step[self.id] == 1:
                            # self.logger.info("return states reward done")
                            self.returnState(self.step_count)
                        # reset step counts that have been actuated
                        self.recCtrlPort.is_step[self.id] = self.recCtrlPort.is_step[self.id] - 1
                        if self.recCtrlPort.is_step[self.id] < 0:
                            self.recCtrlPort.is_step[self.id] = 0
                        # complete a step count add one
                        self.step_count = self.step_count + 1
                        self.multi_state = 0
                        
    def mainLoopForVideo(self):
        self.initTime = time.time()
        self.lastTime = self.initTime
        is_step = [0]*self.configData["Out_Video"]["channels"] # Whether Trigger a step
        is_reset = [False]*self.configData["Out_Video"]["channels"] # Whether Trigger a reset
        episode = 0
        udp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        while True:
            self.initTime = time.time()
            sendAddress = (self.configData["Socket_Ip"],self.configData["Config_Agen_Num_Port"])
            data = bytes(str(0) + "\n", 'utf-8')
            udp_socket.sendto(data, sendAddress)

            if self.multi_state == 1:
                if self.machine_state == 1:
                    is_reset[self.id] = False
                    is_step[self.id] = 1
                    self.step_count = 0
                    System = platform.system()
                    if not os.path.exists("../../droneVideos/DRONE"+str(self.id)+"/episode"+str(episode)):
                        os.mkdir("../../droneVideos/DRONE"+str(self.id)+"/episode"+str(episode))
                    else:
                        if System == "Linux":
                            os.system("rm -rf ../../droneVideos/DRONE" + str(self.id) + "/episode" + str(episode) + "/*.jpeg")
                        elif System == "Windows":
                            os.system("del /s /q /f ../../droneVideos/DRONE" + str(self.id) + "/episode" + str(episode) + "/*.jpeg")
                    episode = episode + 1
                    if self.init():
                        # self.logger.info("drone finish sumo init")
                        with open("../../cache/" + self.droneDef + "_Ctrl2Global.txt", "r") as f:
                            data = f.readline()
                            f.close()
                        is_reset[self.id] = int(data.rstrip().split(',')[-1]) # 去除最后换行符,并按照逗号分割，读取最后一个reset参数
                        self.machine_state = 2 # init come to an end and transfer to steps
                elif self.machine_state == 2:
                    self.sumoGod.ResetSumoDictionary()
                    if is_reset[self.id] == True and self.step_count > 100:
                        # self.logger.info("begin to reset")
                        self.reset()
                        # self.logger.info("finish reset")
                        self.sumoGod.delectDefList()
                        is_reset[self.id] = False
                        self.machine_state = 1 # remember to reset
                    else:
                        self.sumoGod.MoveDroneToCar(self.sumoGod.currentUseCarNode, self.drone, self.sumoGod.transVector, self.sumoGod.rotateAngle, False)
                        if is_step[self.id] == 1:
                            # self.logger.info("return states reward done")
                            with open("../../cache/" + self.droneDef + "_Ctrl2Global.txt", "r") as f:
                                data = f.readline()
                                f.close()
                        if len(data)>10:
                            is_reset[self.id] = int(data.rstrip().split(',')[-1]) # 去除最后换行符,并按照逗号分割，读取最后一个reset参数
                        # reset step counts that have been actuated
                        is_step[self.id] = 1
                        # complete a step count add one
                        self.step_count = self.step_count + 1
                        self.multi_state = 0
            
    '''
    description: An external interface to start loops
    param {*} self
    param {*} state: if state is set to 1, the mainloop will actuate one loop
    return {*}
    '''
    def runMultiState(self, state):
        # If the thread is not finished, it blocks and waits for the thread to finish.
        while self.multi_state != 0:
            pass
        # Threads can be opened for a new run
        self.multi_state = state