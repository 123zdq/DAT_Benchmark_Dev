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
    
    *  :code:`A3CLSTM-E2E` 环境调用了底层环境类 :ref:`BenchEnv_Multi` 
    *  :code:`CVAT` 环境调用了并行环境类( :code:`Envs` :ref:`Parallel` )
    *  :code:`D-VAT` 环境调用了Gym环境类( :code:`UAV_VAT/UAV_VAT_Gymnasium` :ref:`Gymnasium_Gym`)

Baseline1 A3CLSTM-E2E
---------------------------------

    本工程对于 :code:`A3CLSTM-E2E` 方法的复现参考了论文 :code:`AD-VAT+` [4]_ 基于代码仓库 `rl_a3c_pytorch <https://github.com/dgriff777/rl_a3c_pytorch>` 的复现方式。
    
    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/models/A3CLSTM_E2E</code>文件夹
        </div>
        </br>

    上述模型文件夹的目录结构如下：

    .. code-block:: none

        .
        ├── __init__.py
        ├── main.py
        ├── model.py
        ├── num_test.txt
        ├── player_util.py
        ├── runs
        │   └── Benchmark_training
        ├── shared_optim.py
        ├── test.py
        ├── trained_models
        └── train.py

    各文件功能解释如下：

快速运行程序
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    cd Alg_Base/rl_a3c_pytorch_benchmark
    python ./models/A3CLSTM_E2E/main.py


程序入口
~~~~~~~~~~~~~~~~~~~~~~~~~

    :code:`main.py` 为整个程序的入口，主要提供两种运行模式：:code:`train` 和 :code:`test` 。
        
        * 其中， :code:`train` 模式下同样提供了测试进程(例如程序以24进程运行，那么最后一位进程编号23对应的进程为测试进程)， 该进程主要用于训练过程的 :code:`tensorboard` 可视化
        * 而 :code:`test` 模式主要为已经完成训练的模型权重进行测试，该模式同样可以多进程运行，同时对多个模型权重进行测试。
        * 上述模式的配置变量为 :code:`MODE` 变量

    此外， :code:`main.py` 文件还接收用户的参数配置，参数的含义与默认值如下：
    
    * :code:`load(bool)=True` ：是否导入现有模型进行进一步的训练(只有当 :code:`load=True` 而且模型 :code:`A3CLSTM_E2E/trained_models/Benchmark.dat` 存在的时候才会导入)
    * :code:`workers(int)=24` ：环境并行训练的数量数(需要根据实际计算机的内存/显存来决定)
    * :code:`gpu-ids(list)=[-1]` ：用于设置GPU的编号，默认为-1，即不使用GPU
    * :code:`model_type(str)="E2E"` ： 指定当前使用的模型种类，如果用户自主实现了模型可以在此处增加配置。
    * :code:`save-max(bool)=False` ： 是否保存测试进程reward最大时刻的模型权重，默认为 :code:`False` 即仅保存最后一个时刻的模型权重
    * :code:`save-model-dir(str)="./models/A3CLSTM_E2E/trained_models/"` ：模型保存的路径
    * :code:`tensorboard-logger(bool)=True` ：是否使能 :code:`tensorboard` 进行模型的可视化
    * :code:`log-dir(str)="./models/A3CLSTM_E2E/logs/"` ：如果开启了 :code:`tensorboard` ，log文件存储的位置

模型实现
~~~~~~~~~~~~~~~~~~~~~~~~~

    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            模型代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/models/A3CLSTM_E2E/main.py</code>
        </div>
        </br>

    在本工程中提供了两种主干网络，1种是代码仓库 `rl_a3c_pytorch <https://github.com/dgriff777/rl_a3c_pytorch>` 中的实现，另外一种是论文 [1]_ 中的网络结构。

    * 代码仓库 `rl_a3c_pytorch <https://github.com/dgriff777/rl_a3c_pytorch>` 中的网络主干见 :code:`A3Clstm` 类
    * 论文 [1]_ 中的网络结构见 :code:`A3ClstmE2E` 类

log文件
~~~~~~~~~~~~~~~~~~~~~~~~~

    本工程提供了两种log记录方式，第一种是直接输出log文件，另外一种是利用tensorboard记录训练过程的性能变化。

    **模式1：直接输出log文件**

    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            log文件见文件夹 <code>Alg_Base/rl_a3c_pytorch_benchmark/logs</code>
        </div>
        </br>

    * 本模式主要用于程序的调试和数据传输验证，相当于是终端 :code:`print` 函数的替代
    * 在上述文件夹主要包含两种类型的log文件： :code:`Agent_train${n}.log` 和 :code:`Agent${n}.log`
    *  :code:`Agent_train${n}.log` 主要保存训练过程中的参数情况，例如用于希望观测gae值变化，则可以在 :code:`Agent_train${n}.log` 进行观测
    *  :code:`Agent${n}.log` 主要用于保存环境端传输的数据，例如希望观测环境端获取的自定义奖励参数 :code:`RewardParams` ，则可以在该文件观测

    **模式2：直接输出tensorboard-logger文件**

    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            tensorboard-logger文件见文件夹 <code>Alg_Base/rl_a3c_pytorch_benchmark/models/A3CLSTM_E2E/runs/Benchmark_training</code>
        </div>
        </br>

    * :code:`tensorboard` 是神经网络训练过程中的常用可视化平台，因此，本工程也提供了响应的支持
    * 本工程在进行多进程训练的时候会预留一个进程进行测试，例如：用户选择并行智能体数量为24,则实际训练的过程中会有23个训练进程以及1个测试进程，测试进程在每条Episode开始的时候同步shared_model的权值，并进行测试。
    * 而 :code:`tensorboard-logger` 文件中记录的就是测试进程的数据，主要是训练过程中的 :code:`value` ，用于评估智能体训练的情况
    * 此外，如果程序因为外部原因中断，本工程提供了 :code:`tensorboard-logger` 不中断功能，利用 :code:`num_test.txt` 存储当前数据条目数，并在新训练开始时继续进行记录。
    * **注意：** 如果用户希望重新记录训练曲线，需要将 :code:`num_test.txt` 中的数据手动写为0,或者直接删除 :code:`num_test.txt` 文件。
    * 完成所有配置之后，直接运行如下代码，即可在 :code:`localhost:xxxx` 查看 :code:`tensorboard` 可视化记录
    
    .. code:: bash

        cd Alg_Base/rl_a3c_pytorch_benchmark/models/A3CLSTM_E2E/runs
        tensorboard --logdir Benchmark_training

其他
~~~~~~~~~~~~~~~~~~~~~~~~~

    * :code:`train.py` 文件为A3C训练脚本， :code:`test.py` 为测试脚本，而 :code:`player_util.py` 则定义了智能体类别
    * :code:`shared_optim.py` 定义了优化函数

.. raw:: html

    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>

Baseline2 CVAT
---------------------------------


.. raw:: html

    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>

Baseline3 D-VAT
---------------------------------

.. raw:: html

    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>

引用：

.. [1] Luo, Wenhan, et al. "End-to-end active object tracking and its real-world deployment via reinforcement learning." IEEE transactions on pattern analysis and machine intelligence 42.6 (2019): 1317-1332.
.. [2] Devo, Alessandro, Alberto Dionigi, and Gabriele Costante. "Enhancing continuous control of mobile robots for end-to-end visual active tracking." Robotics and Autonomous Systems 142 (2021): 103799.
.. [3] Dionigi, Alberto, et al. "D-VAT: End-to-End Visual Active Tracking for Micro Aerial Vehicles." IEEE Robotics and Automation Letters (2024).
.. [4] Zhong, Fangwei, et al. "Ad-vat+: An asymmetric dueling mechanism for learning and understanding visual active tracking." IEEE transactions on pattern analysis and machine intelligence 43.5 (2019): 1467-1482.

