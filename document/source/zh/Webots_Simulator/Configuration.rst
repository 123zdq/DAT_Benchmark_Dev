仿真环境参数配置建议
=======================

    .. raw:: html

        <style>
            #language-switch {
            display: flex; /* Use Flexbox layout */
            justify-content: center; /* Center buttons horizontally */
            align-items: center; /* Center buttons vertically */
            gap: 10px; /* Space between buttons */
            margin-top: 20px;
            margin-bottom: 20px;
        }
        #language-switch button {
            width: 180px;
            height: 40px;
            font-size: 16px;
            padding: 10px;
            margin: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            background-color: #f0f0f0;
            display: flex;
            align-items: center; /* Center text vertically */
            justify-content: center; /* Center text horizontally */
        }
        </style>

        <!-- Language switch buttons -->
        <div id="language-switch" style="background-color: #fae3e3; padding: 15px; border-radius: 5px; border: 2px solid #cb7474;">
            <b style="font-size: 18px;">You can choose language by </b>
            <button onclick="switchLanguage('zh')">中文</button>
            <button onclick="switchLanguage('en')">English</button>
        </div>

        <script>
            function switchLanguage(lang) {
                if (lang === 'zh') {
                    window.location.href = 'Configuration.html';
                } else if (lang === 'en') {
                    window.location.href = '../../en/Webots_Simulator/Configuration.html';
                }
            }
        </script>
        </br>
        <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
        </br>
        </br>


    由于本项目构建地图大小并不一致，因此，建议容纳的智能体数量也不一致。为避免因追踪目标数量过多而出现的智能体学习困难，本文档为用户提供参考的参数配置建议。

simpleway
-----------------------

    .. code:: json

        {
            "Simulation_Mode": "train",
            "Drone_Supervisor_Ctrl": true,
            "Socket_Ip": "127.0.0.1",
            "Config_Agen_Num_Port":7789,
            "Train_Total_Steps": 1500,
            "Init_No_Done_Steps": 100,
            "No_Reward_Done_Steps": 100,
            "Control_Frequence": 100,
            "Customized_Rewards": true,
            "Lidar_Enable": false,
            "Tracking_Object": "SUMO_VEHICLE",
            "Done_Range": {
                    "max_height": 50,
                    "min_height": 2,
                    "velocity": 10000,
                    "omiga": 6.283,
                    "roll": 1.22,
                    "pitch": 1.22,
                    "distance_error": 50
            },
            "Reward_Config": {
                    "reward_mode": "continuous",
                    "distance_scale": 0.01,
                    "reward_range": 7
            },
            "Sumo_Params": {
                    "max_sumo_car": 40,
                    "car_import_interval": 50.0,
                    "car_type": "passenger",
                    "fixed_color": false,
                    "normalize_color": [1,0,0],
                    "max_car_speed": 15,
                    "max_car_accel": 15,
                    "max_car_decel": 15,
                    "max_rou_distance": 7000,
                    "min_rou_distance": 250,
                    "route_num": 100000
            },
            "Other_Params": {
                    "max_obj_num": 10,
                    "obj_import_interval": 0.5,
                    "import_group_num": 4,
                    "obj_edge_distribution_random": false,
                    "obj_edge_distribution_multilateral": false,
                    "obj_edge_distribution_fixed": 0,
                    "obj_edge_distribution_max":10,
                    "obj_edge_distribution_min":-10

            },
            "Out_Video": {
                    "channels": 4,
                    "fps": 50.0,
                    "start_time": 1.0,
                    "total_time": 50.0
            },
            "Drone_Random_Config": {
                    "start_time_bias_ms": 510,

                    "view_pitch_random": true,
                    "view_pitch_fixed": 1,
                    "view_pitch_random_max": 1,
                    "view_pitch_random_min": 0.4,

                    "height_random": true,
                    "height_fixed": 15.0,
                    "height_random_max": 15.0,
                    "height_random_min": 10.0,

                    "direction_random": true,
                    "direction_random_multilateral": false,
                    "direction_fixed": 0,
                    "direction_random_max": 3.1415926535,
                    "direction_random_min": -3.1415926535,

                    "horizon_bias_random": true,
                    "horizon_bias_multilateral": true,
                    "horizon_bias_fixed": 0,
                    "horizon_bias_random_max": 3,
                    "horizon_bias_random_min": 2,
                    
                    "verticle_bias_random": true,
                    "verticle_bias_multilateral": true,
                    "verticle_bias_fixed": 0,
                    "verticle_bias_random_max": 3,
                    "verticle_bias_random_min": 2
            }
        }

cityStreet
-----------------------

    .. code:: json

        {
            "Simulation_Mode": "train",
            "Drone_Supervisor_Ctrl": true,
            "Socket_Ip": "127.0.0.1",
            "Config_Agen_Num_Port": 7789,
            "Train_Total_Steps": 1500,
            "Init_No_Done_Steps": 100,
            "No_Reward_Done_Steps": 100,
            "Control_Frequence": 125,
            "Customized_Rewards": true,
            "Lidar_Enable": false,
            "Tracking_Object": "SUMO_VEHICLE",
            "Verbose": false,
            "Done_Range": {
                "max_height": 50,
                "min_height": 2,
                "velocity": 10000,
                "omiga": 6.283,
                "roll": 1.22,
                "pitch": 1.22,
                "distance_error": 50
            },
            "Reward_Config": {
                "reward_type": "distance",
                "reward_mode": "continuous",
                "distance_scale": 0.01,
                "reward_range": 7,
                "view_scale": 4
            },
            "Sumo_Params": {
                "max_sumo_car": 28,
                "car_import_interval": 75.0,
                "car_type": "passenger",
                "fixed_color": false,
                "normalize_color": [1,0,0],
                "max_car_speed": 20,
                "max_car_accel": 25,
                "max_car_decel": 25,
                "max_rou_distance": 7000,
                "min_rou_distance": 500,
                "route_num": 100000
            },
            "Other_Params": {
                "max_obj_num": 10,
                "obj_import_interval": 0.5,
                "import_group_num": 4,
                "obj_edge_distribution_random": false,
                "obj_edge_distribution_multilateral": false,
                "obj_edge_distribution_fixed": 0,
                "obj_edge_distribution_max": 10,
                "obj_edge_distribution_min": -10
            },
            "Out_Video": {
                "channels": 4,
                "fps": 50.0,
                "start_time": 1.5,
                "total_time": 50.0,
                "warm_up_steps": 30,
                "output_car_dir": false,
                "random_action": true,
                "forward_speed": 40,
                "backward_speed": -40,
                "left_speed": 40,
                "right_speed": -40,
                "cw_omega": 2,
                "ccw_omega": -2
            },
            "Drone_Random_Config": {
                "start_time_bias_ms": 510,
                "view_pitch_random": false,
                "view_pitch_fixed": 1.37,
                "view_pitch_random_max": 0.6,
                "view_pitch_random_min": 0.2,
                "height_random": false,
                "height_fixed": 22,
                "height_random_max": 15.0,
                "height_random_min": 10.0,
                "direction_random": true,
                "direction_random_multilateral": false,
                "direction_fixed": 0,
                "direction_random_max": 3.1415926535,
                "direction_random_min": -3.1415926535,
                "horizon_bias_random": true,
                "horizon_bias_multilateral": true,
                "horizon_bias_fixed": 0,
                "horizon_bias_random_max": 4.5,
                "horizon_bias_random_min": 3.6,
                "verticle_bias_random": true,
                "verticle_bias_multilateral": true,
                "verticle_bias_fixed": 0,
                "verticle_bias_random_max": 4.5,
                "verticle_bias_random_min": 3.6
            }
        }
        