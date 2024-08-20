/*
 * @Author: lu 2231625449@qq.com
 * @Date: 2024-05-10 11:32:26
 * @LastEditors: lu 2231625449@qq.com
 * @LastEditTime: 2024-08-20 08:52:37
 * @FilePath: /UAV_Follow_Env/Webots_Simulation/traffic_project/controllers/drone_ctrl2/json_config_handle.h
 * @Description: 
 * 
 * Copyright (c) 2024 by ${git_name_email}, All Rights Reserved. 
 */
#pragma once

#include <iostream>
#include <fstream>
#include <nlohmann/json.hpp>
#include <webots/Robot.hpp>
#include <webots/Supervisor.hpp>
#include <Eigen/Eigen>
#include "user_public.h"
#include <webots/Accelerometer.hpp>

using json = nlohmann::json;
using namespace webots;
using namespace Eigen;

typedef struct _configData_s{
    std::string simulationMode = "demo";
    bool droneSupervisorCtrl = false;
    int trainTotalStep = 10000;
    int initNoDoneSteps = 100;
    int noRewardDoneSteps = 1000;
    bool customizedReward = false;
    double controlFreq = 10;
    bool lidarEnable = false;
    bool cameraEnable = true;
    struct _droneRange{
        double maxHeight = 50;
        double minHeight = 1;
        double velocity = 30;
        double omiga = 6.283;
        double roll = 1.22;
        double pitch = 1.22;
        double distanceError = 20;
    };
    _droneRange droneRange;
    struct _rewardConfig{
        std::string rewardMode = "discrete";
        double distanceScale = 0.05;
        double rewardRange = 7;
    };
    _rewardConfig rewardConfig;
    // struct _droneRandomConfig{
    //     bool viewPitchRandom = false;
    //     double viewPitchFixed = -1.2;
    //     double viewPitchRandomMax = -1.57;
    //     double viewPitchRandomMin = -0.7;
    // };
    // _droneRandomConfig droneRandomConfig;
    struct _outVideo{
        double fps = 30;
        double startTime = 0;
        double totalTime = 5;
        bool outputCarDir = true;
        bool randomAction = false;
        double forwardSpeed = 0;
        double backwardSpeed = 0;
        double leftSpeed = 0;
        double rightSpeed = 0;
        double cwOmega = 0;
        double ccwOmega = 0;
    };
    _outVideo video;
}configData_s;

class configHandle{
public:
    configHandle(std::string _filepath);
    ~configHandle(){}
    const configData_s *get(){ return &configData; }
    nlohmann::json read_json_file(const std::string& file_path);
    void write_json_file(const std::string& file_path, const nlohmann::json& json_obj);;
    void writeJsonIncrement(std::string& _filepath, std::string _mark, int _value);
    void writeJsonIncrement(std::string& _filepath, std::string _mark, double _reward,double _done);
private:
    std::string filepath;//json file path and name
    configData_s configData;//json file parse data
};


configHandle::configHandle(std::string _filepath):filepath(_filepath){
    std::ifstream ifs(filepath);
    if (!ifs.is_open()) {
        std::cerr << "Error opening json file\n";
        return;
    }
    
    json config;
    try {
        ifs >> config;
    } catch (const std::exception& e) {
        std::cerr << "Error parsing json file: " << e.what() << "\n";
        return;
    }

    configData.simulationMode = config.at("Simulation_Mode");
    configData.droneSupervisorCtrl = config.at("Drone_Supervisor_Ctrl");
    configData.trainTotalStep = config.at("Train_Total_Steps");
    configData.initNoDoneSteps = config.at("Init_No_Done_Steps");
    configData.noRewardDoneSteps = config.at("No_Reward_Done_Steps");
    configData.controlFreq = config.at("Control_Frequence");
    configData.customizedReward = config.at("Customized_Rewards");
    configData.lidarEnable = config.at("Lidar_Enable");
    configData.droneRange.maxHeight = config.at("Done_Range").at("max_height");
    configData.droneRange.minHeight = config.at("Done_Range").at("min_height");
    configData.droneRange.velocity = config.at("Done_Range").at("velocity");
    configData.droneRange.omiga = config.at("Done_Range").at("omiga");
    configData.droneRange.roll = config.at("Done_Range").at("roll");
    configData.droneRange.pitch = config.at("Done_Range").at("pitch");
    configData.droneRange.distanceError = config.at("Done_Range").at("distance_error");
    configData.rewardConfig.rewardMode = config.at("Reward_Config").at("reward_mode");
    configData.rewardConfig.distanceScale = config.at("Reward_Config").at("distance_scale");
    configData.rewardConfig.rewardRange = config.at("Reward_Config").at("reward_range");
    // configData.droneRandomConfig.viewPitchRandom = config.at("Drone_Random_Config").at("view_pitch_random");
    // configData.droneRandomConfig.viewPitchFixed = config.at("Drone_Random_Config").at("view_pitch_fixed");
    // configData.droneRandomConfig.viewPitchRandomMax = config.at("Drone_Random_Config").at("view_pitch_random_max");
    // configData.droneRandomConfig.viewPitchRandomMin = config.at("Drone_Random_Config").at("view_pitch_random_min");
    configData.video.fps = config.at("Out_Video").at("fps");
    configData.video.startTime = config.at("Out_Video").at("start_time");
    configData.video.totalTime = config.at("Out_Video").at("total_time");
    configData.video.outputCarDir = config.at("Out_Video").at("output_car_dir");
    configData.video.randomAction = config.at("Out_Video").at("random_action");
    configData.video.forwardSpeed = config.at("Out_Video").at("forward_speed");
    configData.video.backwardSpeed = config.at("Out_Video").at("backward_speed");
    configData.video.leftSpeed = config.at("Out_Video").at("left_speed");
    configData.video.rightSpeed = config.at("Out_Video").at("right_speed");
    configData.video.cwOmega = config.at("Out_Video").at(("cw_omega"));
    configData.video.ccwOmega = config.at("Out_Video").at("ccw_omega");
    std::cout<< " \n \n"<<std::endl;
    std::cout<< "    Environment config successful!\n \n"<<std::endl;
    std::cout<< "    Simulation_Mode:       " << configData.simulationMode << std::endl;
    std::cout<< "    Drone_Supervisor_Ctrl: " << configData.droneSupervisorCtrl << std::endl;
    std::cout<< "    Train_Total_Steps:     " << configData.trainTotalStep << std::endl;
    std::cout<< "    Control_Frequence:     " << configData.controlFreq << std::endl;
    std::cout<< "    Customized_Rewards:    " << configData.customizedReward << std::endl;
    std::cout<< "    Lidar_Enable:          " << configData.lidarEnable << std::endl;
    std::cout<< "    Done_Range: {\n"
                << "        max_height:      " << configData.droneRange.maxHeight << "\n"
                << "        min_height:      " << configData.droneRange.minHeight << "\n"
                << "        velocity:        " << configData.droneRange.velocity << "\n"
                << "        omiga:           " << configData.droneRange.omiga << "\n"
                << "        roll:            " << configData.droneRange.roll << "\n"
                << "        pitch:           " << configData.droneRange.pitch << "\n"
                << "        distance_error:  " << configData.droneRange.distanceError << std::endl;
    std::cout<< "    Reward_Config: {\n"
                << "        reward_mode:     " << configData.rewardConfig.rewardMode << "\n"
                << "        distance_scale:  " << configData.rewardConfig.distanceScale << "\n"
                << "        reward_range:    " << configData.rewardConfig.rewardRange << std::endl;
    // std::cout<< "    Drone_Random_Config: {\n"
    //             << "        view_pitch_random:     " << configData.droneRandomConfig.viewPitchRandom << "\n"
    //             << "        view_pitch_fixed:      " << configData.droneRandomConfig.viewPitchFixed << "\n"
    //             << "        view_pitch_random_max: " << configData.droneRandomConfig.viewPitchRandomMax << "\n"
    //             << "        view_pitch_rendom_min: " << configData.droneRandomConfig.viewPitchRandomMin << std::endl;
    std::cout<< "    Out_Video: {\n}"
                << "        fps:             " << configData.video.fps << "\n"
                << "        start_time:      " << configData.video.startTime << "\n"
                << "        total_time:      " << configData.video.totalTime << "\n"
                << "        output_car_dir:  " << configData.video.outputCarDir << "\n"
                << "        random_action:   " << configData.video.randomAction << std::endl;
    std::cout<< "    }\n \n \n"<<std::endl;
}

// 读取JSON文件
nlohmann::json configHandle::read_json_file(const std::string& file_path) {
    std::ifstream file(file_path);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << file_path << std::endl;
        return nlohmann::json();
    }

    nlohmann::json json_obj;
    file >> json_obj;
    file.close();

    return json_obj;
}

// 写入JSON文件
void configHandle::write_json_file(const std::string& file_path, const nlohmann::json& json_obj) {
    std::ofstream file(file_path);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << file_path << std::endl;
        return;
    }

    file << json_obj.dump(4); // 使用4个空格缩进格式化输出
    file.close();
}


void configHandle::writeJsonIncrement(std::string& _filepath, std::string _mark, int _value)
{
    json object = read_json_file(_filepath);
    object[_mark] = _value;
    write_json_file(_filepath, object);
}

void configHandle::writeJsonIncrement(std::string& _filepath, std::string _mark, double _reward,double _done)
{
    json object = read_json_file(_filepath);
    double _value[2] = {_reward,_done};
    object[_mark] = _value;
    write_json_file(_filepath, object);
}




// int main() {
//     // 读取JSON配置文件
//     std::ifstream ifs("config.json");
//     if (!ifs.is_open()) {
//         std::cerr << "Error opening config.json file\n";
//         return 1;
//     }

//     json config;
//     try {
//         ifs >> config;
//     } catch (const std::exception& e) {
//         std::cerr << "Error parsing config.json: " << e.what() << "\n";
//         return 1;
//     }

//     // 从JSON对象中获取配置信息
//     std::string name = config["name"];
//     int age = config["age"];
//     bool isStudent = config["isStudent"];

//     std::cout << "Name: " << name << "\n";
//     std::cout << "Age: " << age << "\n";
//     std::cout << "Is Student: " << std::boolalpha << isStudent << "\n";

//     // 修改配置信息
//     config["age"] = 30;

//     // 将修改后的配置信息写入文件
//     std::ofstream ofs("config_updated.json");
//     if (!ofs.is_open()) {
//         std::cerr << "Error opening config_updated.json file\n";
//         return 1;
//     }

//     ofs << std::setw(4) << config << std::endl;
//     std::cout << "Updated config written to config_updated.json\n";

//     return 0;
// }
