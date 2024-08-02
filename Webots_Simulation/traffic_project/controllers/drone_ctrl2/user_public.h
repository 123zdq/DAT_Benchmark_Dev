/*
 * @Author: lu 2231625449@qq.com
 * @Date: 2024-04-09 11:41:54
 * @LastEditors: lu 2231625449@qq.com
 * @LastEditTime: 2024-08-02 16:19:37
 * @FilePath: /UAV_Follow_Env/Webots_Simulation/traffic_project/controllers/drone_ctrl2/user_public.h
 * @Description: 
 * 
 * Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
 */
#pragma once
#include <iostream>
#include <stdint.h>


namespace usrPublic{
    typedef struct _vector3{
        double x;
        double y;
        double z;
    }vector3;

    typedef struct _vector4{
        double w;
        double x;
        double y;
        double z;
    }vector4;

    // sensor data and reward and done ---- double * 22
    typedef struct _Odometry{
        double t;
        vector3 position;//三轴位置m
        vector3 linear;//三轴线速度m/s
        vector3 acc;//三轴加速度m/s^2
        vector3 angular;//三轴角速度rad
        vector4 orientation;//四元数
        vector3 angle;//欧拉角
        double reward;//reward
        double done;//是否结束仿真
    }Odometry;

    // make reward data ---- double * 64 + string
    typedef struct _rewardData{
        double cameraWidth;
        double cameraHeight;
        double cameraFov;
        double cameraF;
        double T_ct[16];
        vector3 BMW;
        vector3 Citroen;
        vector3 Lincoln;
        vector3 Benz;
        vector3 Rover;
        vector3 Tesla;
        vector3 Toyota;
        double T_tw[16];
        vector3 cameraMidGlobalPos;
        vector3 carMidGlobalPos;
        double carDir;
        std::string carTypename = std::string("ToyotaPriusSimple");
    }rewardData;

    typedef struct _Pose{
        vector4 orientation;
        vector3 position;
    }Pose;

    typedef struct _Joy{
        double axes[10];
    }Joy;
}
