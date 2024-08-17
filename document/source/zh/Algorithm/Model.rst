模型搭建
==================

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
                    window.location.href = 'Model.html';
                } else if (lang === 'en') {
                    window.location.href = '../../en/Algorithm/Model.html';
                }
            }
        </script>  
        </br>
        <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
        </br>
        </br>


    本工程提供了4种baseline方法的算法实现，分别是 :code:`A3CLSTM-E2E` [1]_ , :code:`CVAT` [2]_ , :code:`D-VAT` [3]_ 以及 （我们的方法）

    其中，上述baseline方法中 [1]_ [2]_ [3]_ 分别调用了本工程实现的3种环境 :doc:`Environment` ，为不同需求的算法实现提供了模板
    
    *  :code:`A3CLSTM-E2E` 环境调用了底层环境类:ref:`BenchEnv_Multi` 
    *  :code:`CVAT` 环境调用了并行环境类( :code:`Envs` :ref:`Parallel` )
    *  :code:`D-VAT` 环境调用了Gym环境类( :code:`UAV_VAT/UAV_VAT_Gymnasium` :ref:`Gymnasium_Gym`)

Baseline1 A3CLSTM-E2E
---------------------------------

Baseline2 CVAT
---------------------------------

Baseline3 D-VAT
---------------------------------

.. [1] Luo, Wenhan, et al. "End-to-end active object tracking and its real-world deployment via reinforcement learning." IEEE transactions on pattern analysis and machine intelligence 42.6 (2019): 1317-1332.
.. [2] Devo, Alessandro, Alberto Dionigi, and Gabriele Costante. "Enhancing continuous control of mobile robots for end-to-end visual active tracking." Robotics and Autonomous Systems 142 (2021): 103799.
.. [3] Dionigi, Alberto, et al. "D-VAT: End-to-End Visual Active Tracking for Micro Aerial Vehicles." IEEE Robotics and Automation Letters (2024).
