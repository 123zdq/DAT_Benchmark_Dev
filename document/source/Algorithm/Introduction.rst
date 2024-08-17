算法部分介绍
==================

    .. raw:: html

      <div style="background-color: #FDF5E6; padding: 15px; border-radius: 5px; border: 1px solid #EEC591;">
            本项目提供了<b>3种环境类的实现，以及4种baseline算法</b>，可供用户后续进行算法设计和性能比较
            环境类详细文档参考: <a href="Environment.rst">环境封装</a> ；算法类详细文档参考： <a href="Model.rst">环境封装</a> 
      </div>
      </br>

快速开始(运行baseline算法)
---------------------------

Baseline1: :code:`BenchEnv_Multi` 环境 +  :code:`A3CLSTM-E2E` 算法 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        环境代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/environment.py</code>
        算法代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/models/A3CLSTM_E2E/</code>
    </div>
    </br>


可以运行如下代码快速开启算法：

.. code:: bash

    cd Alg_Base/rl_a3c_pytorch_benchmark/
    python ./models/A3CLSTM_E2E/main.py

Baseline2: :code:`Envs` 环境 +  :code:`CVAT` 算法 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        环境代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/gym_envs.py</code>
        算法代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/models/D_VAT/</code>
    </div>
    </br>


可以运行如下代码快速开启算法：

.. code:: bash

    cd Alg_Base/rl_a3c_pytorch_benchmark/
    python ./models/D_VAT/DVAT_main.py

Baseline3: :code:`UAV_VAT/UAV_VAT_Gymnasium` 环境 +  :code:`D-VAT` 算法 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        环境代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/envs_parallel.py</code>
        算法代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/models/Recurrent_PPO/</code>
    </div>
    </br>


可以运行如下代码快速开启算法：

.. code:: bash

    cd Alg_Base/rl_a3c_pytorch_benchmark/
    python ./models/Recurrent_PPO/RPPO.py