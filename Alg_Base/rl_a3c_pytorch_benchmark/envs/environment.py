from __future__ import division
import gym
from functools import partial
import cv2
import numpy as np
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from communication.receiveSocket import RecvRewardDoneSocketPort,RecvImgSocketPort,RecvStateMachineSocketPort,RecvPointCloud,RecvRewardParams,is_file_in_use
from communication.sendSocket import SendActionSocket
import time
from logger_cfg import create_logger
import copy
from utils import get_E2E_reward,get_DVAT_reward,get_ENHANCE_reward,check_memory_usage
import math
from threading import Thread
from logs.Empty_Log import Empty_Logger
# import matplotlib.pyplot as plt

BASE_PORT = 6000

global_start_flag = False

"""
    process_frame:
        If choose to run LunarLander-v2 Env,the function will be run outside step()/reset()
        If choose to run Benchmark Env,the function will be run inside step()/reset()
    Input:
        env: env class
        state: state to be process
        conf: dict read from config.json
    Output:
        state_new: state after process
"""
def process_frame(state,conf,env=None):
    if conf["Need_render"]:
        state = env.render(mode = "rgb_array")
    state_new = cv2.resize(state, (conf["State_size"], conf["State_size"]))
    state_new = state_new.astype(np.float32)
    if conf["Norm_Type"] == 0:
        state_new = state_new/255.0
    elif conf["Norm_Type"] == 1:
        state_new = (state_new-128.0)/128.0
    state_new = cv2.cvtColor(state_new,cv2.COLOR_BGR2RGB)
    state_new = state_new.reshape((conf["State_channel"],conf["State_size"],conf["State_size"]))
    # plt.imshow(state_new.reshape(84,84,3))
    # plt.show()
    
    return state_new

"""
    Identity:
        To make output identical within general_env function
    Input:
        state
    Output:
        state
"""
def Identity(state,env):
    return state

"""
    general_env:
    Input:
        env_id(Str): Name of the desire env
        env_conf(Dict): dict get from config.json
        arg_worker(Int): Number of Process the User Choose
        process_idx(Int): Process Index of the Current Env
        Other_State(Bool): Whether use other_state or not(default=True)
        CloudPoint(Bool): Whether use cloudpoint or not(default=True)
        RewardParams(Bool): Whether use reward params or not(default=True)
    Output:
        env(BenchEnv_Multi): initialized env
        process_func(Function): partial the process the state frame
"""
def general_env(env_id,env_conf,arg_worker,process_idx):
    if env_id not in ["LunarLander-v2","Benchmark"]:
        print(env_id," is not valid!")
        raise NameError
    elif env_id == "LunarLander-v2":
        env = gym.make(env_id)
        process_func = partial(process_frame,conf=env_conf)
        return env,process_func
    elif env_id == "Benchmark":
        Other_State,CloudPoint,RewardParams = env_conf["Other_State"],env_conf["CloudPoint"],env_conf["RewardParams"]
        process_state = partial(process_frame,conf=env_conf)
        env = BenchEnv_Multi(Action_dim=env_conf["Action_dim"],process_state=process_state,arg_worker=arg_worker,\
                             process_idx=process_idx,Other_State=Other_State,CloudPoint=CloudPoint,RewardParams=RewardParams,\
                             action_list=[env_conf["Forward_Speed"],env_conf["Backward_Speed"],env_conf["Left_Speed"],\
                                          env_conf["Right_Speed"],env_conf["CW_omega"],env_conf["CCW_omega"]],\
                             port_process=env_conf["port_process"],end_reward=env_conf["end_reward"],end_reward_list=env_conf["end_reward_list"],\
                             scene=env_conf["scene"],weather=env_conf["weather"],auto_start=env_conf["auto_start"],Control_Frequence = env_conf["Control_Frequence"],\
                             reward_type=env_conf["RewardType"],verbose=env_conf["verbose"],delay=env_conf["delay"])
        process_func = Identity
        return env,process_func

class BenchEnv_Multi():
    """
        __init__: 
            Initialize whole Multi_Process Environment
        Input:
            Action_dim(Int): Dimension of Action
            action_list(List): A list that set specific parameter of each action
            process_state(Function): A Function that process the raw image(e.g:resize)
            arg_worker(Int): Number of Process
            process_idx(Int): Index of Current Process
            Other_State(Bool): Whether use addition state(default=False)
            CloudPoint(Bool): Whether use cloudpoint(default=False)
            RewardParams(Bool): Whether use Reward Parameter(default=False)
            Control_Frequence(Int): Webots Operating Frequency deciding the skip frame(Default=500:No frame skip)
        Output:
            None
    """
    def __init__(self,Action_dim,action_list,process_state,arg_worker,\
        process_idx,Other_State,CloudPoint,RewardParams,\
        port_process,end_reward,end_reward_list,scene,weather,auto_start,\
        Control_Frequence = 500,reward_type="default",verbose=False,delay=20) -> None:
        
        self.Action_dim = Action_dim
        self.process_state = process_state
        self.num_process = arg_worker
        self.process_id = process_idx
        self.port_list = []
        
        ## Action_list:[Forward,Backward,Left,Right,CW,CCW]
        self.Forward = action_list[0]
        self.Backward = action_list[1]
        self.Left = action_list[2]
        self.Right = action_list[3]
        self.CW = action_list[4]
        self.CCW = action_list[5]
        
        ## Flag decide whether open done detection
        self.done_flag = True

        """ 
            Choose Corresponding Port according to process_idx
            self.port_list: 2D List(Shape:[5,]) contains 5 socket for corresponding port and for all Process
                Socket 1: Webots Send Image to Client
                Socket 2: Webots Send State Machine Flag to Client
                Socket 3: Webots Send Env State , reward and done to Client
                Socket 4: Client Send Control to Webots(Action or Reset)
                Socket 5: Webots Send CloudPoint to Client
                Socket 6: Webots Send Params for Customize Reward
        """
        for i in range(6):
            self.port_list.append(BASE_PORT+6*process_idx+i)
        
        ## Specify the File Path of each system path
        ## To do: CHANGE ABSOLUTE PATH TO RELATIVE PATH
        self.action_path = "../../Webots_Simulation/traffic_project/Files2Alg/" + "DRONE" + str(process_idx) + "_AlgAction.txt"
        self.reward_path = "../../Webots_Simulation/traffic_project/Files2Alg/" + "DRONE" + str(process_idx) + "_Ctrl2Global.txt"
        self.img_path = "../../Webots_Simulation/traffic_project/Files2Alg/" + "DRONE" + str(process_idx) + "_VideoFrame.jpeg"
        self.pointcloud_path = "../../Webots_Simulation/traffic_project/Files2Alg/" + "DRONE" + str(process_idx) + "_PointCloud.txt"
        self.rewardparam_path = "../../Webots_Simulation/traffic_project/Files2Alg/" + "DRONE" + str(process_idx) + "_RewardParams.txt"
        
        self.port_process = port_process
        """
            Use Path above to create corresponding socket
                self.send_socket:
                self.recv_rewarddone_socket:
                self.recv_image_socket:
                self.recv_state_mechine:
                self.recv_reward_params:
        """ 
        self.send_socket=SendActionSocket(ip="127.0.0.1",port_action=self.port_list[3],port_control = self.port_list[3],port_process=self.port_process,action_path=self.action_path)
        self.recv_rewarddone_socket=RecvRewardDoneSocketPort(22,id=self.port_list[2],reward_path=self.reward_path)
        self.recv_image_socket=RecvImgSocketPort(320*240*3,id=self.port_list[0],img_path=self.img_path)
        self.recv_state_mechine = RecvStateMachineSocketPort(id=self.port_list[1])
        self.recv_point_cloud = RecvPointCloud(id=self.port_list[4],pointcloud_path=self.pointcloud_path)
        self.recv_reward_params = RecvRewardParams(id=self.port_list[5],rewardparam_path=self.rewardparam_path)
        
        ## Start The simulation end
        # global global_start_flag
        
        if process_idx == 0 and auto_start:
            if scene not in ["citystreet","downtown","lake","village","desert","farmland",None]:
                raise ValueError("scene: "+str(scene)+" is illegal!")
            if weather not in ["day","night","foggy","snow",None]:
                raise ValueError("weather: "+str(weather)+" is illegal!")
            self.scene = scene
            self.weather = weather
            if self.scene == None:
                self.scene = "citystreet"
            if self.weather == None:
                self.weather = "day"
            webots_path = "../../Webots_Simulation/traffic_project/worlds/"+self.scene+"-"+self.weather+".wbt"
            os.system("webots --no-rendering --batch --mode=fast "+webots_path+" &")
        #     if self.send_socket.judge_start():
        #         time.sleep(1)
        #         global_start_flag = True
        # while not global_start_flag:
        #     pass
        if auto_start:
            time.sleep(delay)
            
        
        # Inform Env of Num worker
        self.send_socket.send_signal(bytes(str(self.num_process)+"\n",'utf-8'),process=True) 
        # Information Flag Set by User
        self.Other_State=Other_State
        self.CloudPoint=CloudPoint
        self.RewardParams=RewardParams
        self.SuppleInfo = []
        
        # Use to resend the reset signal
        self.Control_Frequence = int(Control_Frequence)
        self.Resend_Internal = 10000/self.Control_Frequence
        self.last_done_flag = 0
        
        # Use to set done flag
        self.Set_Done_Step = 10000/self.Control_Frequence

        # Logging
        if verbose:
            self.logger = create_logger(self.process_id)
        else:
            self.logger = Empty_Logger()

        # reset
        self.reset_time = 0

        # end reward config
        self.end_reward = end_reward
        self.end_reward_list = end_reward_list

        # reward type
        if reward_type not in ["default","E2E","DVAT","ENHANCE"]:
            raise AttributeError(f"reward_type: {reward_type} is not legal! Legal ones: ['default','E2E','DVAT','ENHANCE']")
        else:
            self.reward_type = reward_type

        self.curr_step = 0

        # Memory Protect
        # if process_idx == 0:
        current_pid = os.getpid()
        self.memory_pretect_thread = Thread(target=check_memory_usage, args=(current_pid,0.85,))
        self.memory_pretect_thread.start()

    """
        step: 
            1. Send an action to server through socket
            2. Receive State,reward,done from server through socket
        Input:
            action: Action Chosen by Agent and send to server through socket
                action = 0: Go forward at V = action_list[0]
                action = 1: Go backward at V = action_list[1]
                action = 2: Go leftward at V = action_list[2]
                action = 3: Go rightward at V = action_list[3]
                action = 4: Turn Clockwise at w = action_list[4]
                action = 5: Turn CounterClockwise as w = action_list[5]
                action = 6: Stop Tracking
        Output:
            State: Next state received from server through socket
            Reward: Reward received from server through socket
            done: Whether the env is done receive from server through socket
            self.SuppleInfo: Other Sensor data/Reward Params for User to Customize their own State/Reward
    """
    def step(self,action,prob=None):
        self.logger.info("\n")
        self.logger.info('<----- Step Function ----->')
        
        
        ## If Exist Image when entering step function,DELETE IMAGE!!!
        while os.path.exists(self.img_path):
            self.logger.info('Unlink existing image first in step')
            time.sleep(0.001)
            while is_file_in_use(self.img_path):
                pass
            os.unlink(self.img_path)

        ## SuppleInfo Include Other_State/RewardParams/CloudPoint
        self.SuppleInfo = []

        ## Convert action to action_list
        if action == 0:
            self.action = [self.Forward,0,0,0]
        elif action == 1:
            self.action = [self.Backward,0,0,0]
        elif action == 2:
            self.action = [0,self.Left,0,0]
        elif action == 3:
            self.action = [0,self.Right,0,0]
        elif action == 4:
            self.action = [0,0,0,self.CW]
        elif action == 5:
            self.action = [0,0,0,self.CCW]
        elif action == 6:
            self.action = [0,0,0,0]
        
        ## Send Action List Converted Above
        self.logger.info('Begin to send action: ' + str(self.action))
        self.send_socket.send_action(self.action)
        self.logger.info('Finish sending action and begin to read Reward/Done/Step')

        ## Read Reward,Done,Current step(Use to Manage Done) and Other_state
        reward,done,step_curr,other_state = self.recv_rewarddone_socket.read(self.img_path)

        self.curr_step = step_curr

        ## Read Other_State/RewardParams/CloudPoint According to flag
        if self.Other_State:
            self.logger.info('Start Getting other_state')
            self.SuppleInfo.append(other_state)
            self.logger.info('Get other_state:  '+str(other_state))
        if self.RewardParams:
            self.logger.info('Start Getting reward_params')
            reward_params = self.recv_reward_params.read()
            self.logger.info('Get Reward Params:  '+str(reward_params))
            self.logger.info(f'delta y: {reward_params[-5]-reward_params[-8]} delta x: {reward_params[-4]-reward_params[-7]} delta z: {reward_params[-3]-reward_params[-6]}')
            self.SuppleInfo.append(reward_params)
        if self.CloudPoint:
            self.logger.info('Start Getting point_cloud')
            point_cloud = self.recv_point_cloud.read()
            self.logger.info('Get point_cloud:  '+str(point_cloud))
            self.SuppleInfo.append(point_cloud)

        self.logger.info('Get Direction of the car:  '+str(reward_params[-2]))

        self.logger.info(f'Get Crash of the car: {reward_params[-3]}')

        self.logger.info(f'Get Pos/Ori of the car: x-{reward_params[-6]} y-{reward_params[-5]} z-{reward_params[-4]} w-{reward_params[-7]}')

        ori_w = reward_params[-7]
        pos_x = reward_params[-6]
        pos_y = reward_params[-5]
        pos_z = reward_params[-4]
        camera_xw = reward_params[-10]
        camera_xg = reward_params[-16]
        crash = int(reward_params[-3])
        Afov = reward_params[2]

        ###### Test Cheat
        if prob is not None:
            
            cardir = int(reward_params[-2])
            if cardir == 0:
                dynamics = np.array([0,0,0,0,0,0,1])
            elif cardir == 1:
                dynamics = np.array([1,0,0,0,0,0,0])
            elif cardir == 2:
                dynamics = np.array([0,0,0,0,0,1,0])
            elif cardir == 3:
                dynamics = np.array([0,0,0,0,1,0,0])
            
            prob_np = copy.deepcopy(prob.detach().numpy())
            prob_np = np.ravel(prob_np)
            self.logger.info(f'Output Prob of Policy Network is {prob_np}')
            norm = np.linalg.norm(dynamics - prob_np)
            norm = float(norm)
            self.logger.info(f'Norm between dynamics and predict is {norm}')
        

        self.logger.info('Curr_reward: '+str(reward)+' Curr_done: '+str(done)+' Curr_step: '+str(step_curr))

        """
            Done Management:
                1. Open done detection in the early stage of episode
                2. If receive first done, close done detection to avoid re-detection
                3. If Webots do not receive done flag, open done detection again 
        """
        if int(step_curr) <= self.Set_Done_Step and self.done_flag == False:
            self.logger.info('Step_curr:{} self.Set_Done_Step:{} Open Done Flag'.format(step_curr,self.Set_Done_Step))
            self.done_flag = True
            self.last_done_flag = 0
            self.oriw_0 = ori_w
            self.d_curr = camera_xg - camera_xw
        
        if self.reward_type == "default":
            pass
        elif self.reward_type == "E2E":
            reward = get_E2E_reward(x=pos_y,y=pos_x,w=ori_w,w_0=self.oriw_0,d_curr=self.d_curr)
        elif self.reward_type == "DVAT":
            reward = get_DVAT_reward(A_fov=Afov,d_cmd=self.d_curr,x=pos_x,y=pos_y,z = pos_z,v=[0,0,0],u=[0,0,0],end_done=crash,discrete=True)
        elif self.reward_type == "ENHANCE":
            rho = math.sqrt(math.pow(pos_x,2)+math.pow(pos_y,2))
            theta = ori_w
            rho_cmd = self.d_curr
            theta_cmd = self.oriw_0
            reward = get_ENHANCE_reward(rho=rho,theta=theta,rho_cmd=rho_cmd,theta_cmd=theta_cmd)

        if done:
            if self.done_flag:
                self.done_flag = False
                self.last_done_flag = step_curr
                if self.end_reward and self.reward_type == "default":
                    if reward <= 0.0:
                        self.logger.info('<--Failure Situation--> Reward += {}'.format(self.end_reward_list[0]))
                        reward += self.end_reward_list[0]
                    else:
                        self.logger.info('<--Success Situation--> Reward += {}'.format(self.end_reward_list[1]))
                        reward += self.end_reward_list[1]
                    self.logger.info("done_step: "+str(step_curr)+"   process_id:  "+str(self.process_id))
            else:
                if step_curr - self.last_done_flag >= self.Resend_Internal:
                    done=True
                    self.last_done_flag = step_curr
                else:
                    done = False
                self.logger.info("curr_step"+str(step_curr)+"   process_id:  "+str(self.process_id))
        
        
        ## Receive Image and Process Image
        self.logger.info('Begin to receive image')
        image = self.recv_image_socket.receive(self.reward_path)
        self.logger.info('Finish receiving image')
        image = self.process_state(image)
        return image,reward,done,self.SuppleInfo

    """
        Reset: Receive first State from server through socket
        Input:
            None
        Output:
            State: First state received from server through socket
    """
    def reset(self): 
        self.logger.info("\n")
        self.logger.info('<----- !!!!!Reset Function!!!!! ----->')

        ## reset ori_w command and ori_y command
        self.oriw_0 = 0
        self.d_curr = 0


        ## If Reward still exist when entering reset function,DELETE REWARD FILE!!!
        if os.path.exists(self.reward_path):
            time.sleep(0.001)
            while is_file_in_use(self.reward_path):
                pass
            os.unlink(self.reward_path)
        
        ## SuppleInfo Include Other_State/RewardParams/CloudPoint
        self.SuppleInfo = []

        ## Send Special Action to inform Webots of reset stage
        self.logger.info('Begin to send reset [0,0,0,0,1]')
        self.send_socket.send_reset_control(self.process_id)
        self.logger.info('Finish sending reset [0,0,0,0,1]')

        ## Waiting For Action to be read
        if self.action_path is not None:
            while not self.send_socket.judge_empty():
                self.logger.info('Action File not empty')
                if os.path.exists(self.reward_path):
                    self.logger.info('Deleting reward file in reset')
                    while is_file_in_use(self.reward_path):
                        pass
                    os.unlink(self.reward_path)

        ## Read Reward,Done,Current step and Other_state abandoned
        reward,done,step_curr,other_state = self.recv_rewarddone_socket.read(self.img_path)
        self.logger.info('In reset: Curr_reward: '+str(reward)+' Curr_done: '+str(done)+' Curr_step: '+str(step_curr))
        
        ## Read Other_State/RewardParams/CloudPoint According to flag
        if self.Other_State:
            self.logger.info('Start Getting other_state')
            self.SuppleInfo.append(other_state)
            self.logger.info('Get other_state:  '+str(other_state))
        if self.RewardParams:
            self.logger.info('Start Getting reward_params')
            reward_params = self.recv_reward_params.read()
            self.logger.info('Get Reward Params:  '+str(reward_params))
            self.SuppleInfo.append(reward_params)
        if self.CloudPoint:
            self.logger.info('Start Getting point_cloud')
            point_cloud = self.recv_point_cloud.read()
            self.logger.info('Get point_cloud:  '+str(point_cloud))
            self.SuppleInfo.append(point_cloud)

        ## Begin to read image
        self.logger.info('Begin to receive image in reset')
        if self.reset_time == 0:
            image = self.recv_image_socket.receive(self.reward_path,reset=True,first_reset=True)
        else:
            image = self.recv_image_socket.receive(self.reward_path,reset=True)
        self.logger.info('Finish receiving image in reset')
        if self.reset_time != 0:
            ## Avoid image to be empty
            while len(image.shape) == 1:
                self.logger.info('Waiting for image again')
                image = self.recv_image_socket.receive(self.reward_path,reset=True)
                self.logger.info('Finish receiving img again')
        if os.path.exists(self.action_path):
            while is_file_in_use(self.action_path):
                pass
            os.unlink(self.action_path)
        image = self.process_state(image)
        self.reset_time += 1
        return image,self.SuppleInfo