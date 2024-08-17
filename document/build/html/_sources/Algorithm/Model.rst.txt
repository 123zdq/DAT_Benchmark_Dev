模型搭建
==================

    本工程提供了4种baseline方法的算法实现，分别是 :code:`A3CLSTM-E2E` [1]_ , :code:`CVAT` [2]_ , :code:`D-VAT` [3]_ 以及 （我们的方法）

    其中，上述baseline方法中 [1]_ [2]_ [3]_ 分别调用了本工程实现的3种环境 :doc:`Environment` 
    
    *  :code:`A3CLSTM-E2E` 环境调用了底层环境类 :code:`BenchEnv_Multi` :ref:`BenchEnv_Multi` 
    *  :code:`CVAT` 环境调用了底层环境类(BenchEnv_Multi)
    *  :code:`D-VAT` 环境调用了底层环境类(BenchEnv_Multi)

.. [1] Luo, Wenhan, et al. "End-to-end active object tracking and its real-world deployment via reinforcement learning." IEEE transactions on pattern analysis and machine intelligence 42.6 (2019): 1317-1332.
.. [2] Devo, Alessandro, Alberto Dionigi, and Gabriele Costante. "Enhancing continuous control of mobile robots for end-to-end visual active tracking." Robotics and Autonomous Systems 142 (2021): 103799.
.. [3] Dionigi, Alberto, et al. "D-VAT: End-to-End Visual Active Tracking for Micro Aerial Vehicles." IEEE Robotics and Automation Letters (2024).
