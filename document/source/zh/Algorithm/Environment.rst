环境封装
============

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
                window.location.href = 'Environment.html';
            } else if (lang === 'en') {
                window.location.href = '../../en/Algorithm/Environment.html';
            }
        }
    </script>
    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>

  本项目提供3种形式的Environment(路径： :code:`Alg_Base/rl_a3c_pytorch_benchmark/envs` ): 底层Environment类，OpenAI Gym(Gynasium)封装的Environment类，以及我们自主实现的异步并行框架Environment类
  
  上述3种Environment的关系如下图所示：

    .. figure:: ../_static/image/Environment3Types.png
      :alt: 3种环境类关系图                                 
      :width: 600px                                              
      :align: center

      3种环境类示意图

.. _BenchEnv_Multi:
    
1 底层环境类(BenchEnv_Multi)
-------------------------------------

Part 1 接口详解
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. raw:: html

      <div style="background-color: #FDF5E6; padding: 15px; border-radius: 5px; border: 1px solid #EEC591;">
            底层环境类是<b>算法端与仿真器端进行直接通信的类</b>，主要承担与仿真器进行多进程通信与数据传输的功能。
            如果仅调用类进行测试，可以直接跳转至： <a href="#config">配置文件</a>以及<a href="#makeenv">构造函数</a>
      </div>
      </br>
    
    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/environment.py</code>中的<code>BenchEnv_Multi()</code>
        </div>
        </br>
    

    .. raw:: html

      <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
            1. <code>__init__</code> ：用于初始化通信接口，进程数等环境必备参数
      </div>
      </br>

    * :code:`Action_dim(int)` ：智能体动作维度
    * :code:`action_list(list)` ：用于将离散的动作指令转化成连续的运动指令
        
      * :code:`action_list` 的存储顺序为： :code:`[Forward,Backward,Left,Right,CCW,CW]`，即分别代表“前后左右逆顺”的运动指令

    * :code:`process_state(function)` ：用于对图像进行后处理的函数
    * :code:`arg_worker(int)` ： 系统并行数
    * :code:`process_idx(int)` ：当前环境的并行编号
    * :code:`Other_State(bool)` ：是否启用仿真器端的其他状态选项 :code:`Other_State`
    * :code:`CloudPoint(bool)` ： 是否启用仿真器端的点云选项 :code:`CloudPoint`
    * :code:`RewardParams(bool)` ： 是否启用仿真器端的其他奖励参数选项 :code:`RewardParams`
    * :code:`port_process(int)` ： 指定用于传输进程数的端口
    * :code:`end_reward(bool)` ： 是否开启追加结束奖励
    * :code:`end_reward_list(list)` ： 追加结束奖励列表（在 :code:`end_reward` 开启时才有效）
    * :code:`scene(str)` ： 确定当前的实验场景(在 :code:`auto_start` 开启时才有效)

      * 合法场景包括： :code:`["citystreet","downtown","lake","village","desert","farmland",None]`

    * :code:`weather(str)` ： 确定当前实验场景的天气(在 :code:`auto_start` 开启时才有效)

      * 合法天气包括： :code:`["day","night","foggy","snow",None]`

    * :code:`auto_start(bool)` ： 是否自动启动仿真端
    * :code:`Control_Frequence(int)` ： 指定系统控制频率
    * :code:`reward_type(str)` ： 指定reward类别(可以选择不同baseline算法的reward)
    
    .. raw:: html

      <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
            2. <code>step</code> ：用于环境的推演
      </div>
      </br>
        
    **输入参数：**

    * :code:`action(numpy.int64)` ： 智能体采取的动作

    .. raw:: html

        </br>

    **返回参数：**

    * :code:`image(numpy.ndarray)` ：返回的下一时刻图像(已经利用 :code:`process_state` 进行后处理)
    * :code:`reward(float)` ：当前时间步奖励
    * :code:`done(bool)` ： 当前环境是否结束
    * :code:`self.SuppleInfo(list)` ：补充信息(如果启用了:code:`Other_State` 或 :code:`CloudPoint` 或 :code:`RewardParams` ，就在此取出)

    .. raw:: html

      <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
            2. <code>reset</code> 用于环境的重启
      </div>
      </br>

    **输入参数：**

    None

    **返回参数：**

    * :code:`image(numpy.ndarray)` ：解释同上
    * :code:`self.SuppleInfo(list)` ：解释同上
    
.. raw:: html

    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>

.. _config:

Part 2 配置文件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. raw:: html

      <div style="background-color: #FDF5E6; padding: 15px; border-radius: 5px; border: 1px solid #EEC591;">
            上述环境接口较多，因此，为了便于后期的封装调用，<b>本工程提供了配置文件</b>，简化配置流程。配置文件内容如下：
      </div>
      </br>
    
    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/config.json</code>
        </div>
        </br>

    .. code:: json

        {
            "Benchmark":{
                "Need_render":0,
                "Action_dim":7,
                "State_size":84,
                "State_channel":3,
                "Norm_Type":0,
                "Forward_Speed":40,
                "Backward_Speed":-40,
                "Left_Speed":40,
                "Right_Speed":-40,
                "CW_omega":0.2,
                "CCW_omega":-0.2,
                "Control_Frequence":100,
                "port_process":7789,
                "end_reward":false,
                "end_reward_list":[-20,20],
                "scene":"farmland",
                "weather":"day",
                "auto_start":false,
                "Other_State":false,
                "CloudPoint":false,
                "RewardParams":true,
                "RewardType":"default"
            },
            "LunarLander":{
                "Need_render":1,
                "Action_dim":4,
                "State_size":84,
                "State_channel":3,
                "Norm_Type":0
            }
        }

    * 其中， :code:`"Benchmark"` ：对应的参数即为本工程提出的仿真环境的配置参数
    *  :code:`"LunarLander"` ：对应Gym环境 :code:`LunarLander` 的参数配置，仅作兼容性测试用途使用
    *  :code:`"Need_render"` ：选择渲染模式(gym的环境需要选择渲染模式， **本工程环境默认为0即可** )
    *  :code:`"Action_dim"` ：智能体动作空间维度
    *  :code:`"State_size"` ：环境输出的图像大小
    *  :code:`"State_channel"` ：环境输出的图像通道数目(=3:RGB图，=1:灰度图)
    *  :code:`"Norm_Type"` ：图像归一化方式(默认归一化到 :code:`[0,1]``)
    *  :code:`"Forward_Speed"` ：智能体输出前进动作时对应的速度(m/s)
    *  :code:`"Backward_Speed"` ：智能体输出后退动作时对应的速度(m/s)
    *  :code:`"Left_Speed"` ：智能体输出左移动作时对应的速度(m/s)
    *  :code:`"Right_Speed"` ：智能体输出右移动作时对应的速度(m/s)
    *  :code:`"CW_omega"` ：智能体输出顺时针动作时对应的速度(rad/s)
    *  :code:`"CCW_omega"` ：智能体输出逆时针动作时对应的速度(rad/s)
    *  :code:`"Control_Frequence"` ：智能体运行的频率(仿真器以500Hz运行，算法端一般以50/100Hz运行)
    *  :code:`"port_process"` ：指定用于传输进程数的端口
    *  :code:`"end_reward"` ：是否开启追加结束奖励
    *  :code:`"end_reward_list"` ：追加结束奖励列表（在 :code:`end_reward` 开启时才有效）
    *  :code:`"scene"` ：确定当前的实验场景(在 :code:`auto_start` 开启时才有效)
    *  :code:`"weather"` ：确定当前实验场景的天气(在 :code:`auto_start` 开启时才有效)
    *  :code:`"auto_start"` ： 是否自动启动仿真端
    *  :code:`"Other_State"` ：是否启用仿真器端的其他状态选项
    *  :code:`"CloudPoint"` ：是否启用仿真器端的点云选项
    *  :code:`"RewardParams"` ：是否启用仿真器端的其他奖励参数选项
    *  :code:`"RewardType"` ：指定reward类别(可以选择不同baseline算法的reward)

.. raw:: html

    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>

.. _makeenv:

Part 3 构造函数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    .. raw:: html

      <div style="background-color: #FDF5E6; padding: 15px; border-radius: 5px; border: 1px solid #EEC591;">
            基于上述配置文件，<b>本工程直接提供了构造函数，获取初始化好的环境</b>，该函数使用方法如下：
      </div>
      </br>

    .. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/environment.py</code>中的<code>general_env()</code>
        </div>
        </br>

    .. code:: python

        # 生成单进程的环境(env_conf为config.json的路径)
        env,_ = general_env(env_id="Benchmark",env_conf=env_conf,arg_worker=1,process_idx=0)
    
    .. raw:: html

      <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
            <code>general_env</code> ：根据config.json文件生成初始化好的环境
      </div>
      </br>

    **输入参数：**

    *  :code:`env_id(str)` ：当前环境的名称(:code:`"Benchmark"` 或 :code:`"LunarLander"` )
    *  :code:`env_conf(str)` ：配置文件 :code:`config.json` 的路径
    *  :code:`arg_worker(int)` ：环境总进程数
    *  :code:`process_idx(int)` ：当前环境的进程编号

    **返回参数：**

    *  :code:`env` ：环境类
    *  :code:`process_func` ：环境后处理函数(对于 :code:`"Benchmark"` 而言，无后处理操作)

    .. raw:: html

        </br>


.. _Gymnasium_Gym:


2 Gym环境类(UAV_VAT/UAV_VAT_Gymnasium)
-------------------------------------------------

  考虑到用户常常基于 `Gym <https://github.com/openai/gym>`_ 和 `Gymnasium <https://github.com/openai/gym>`_ 环境接口搭建强化学习算法，或利用如 `stable-baselines3 <https://github.com/DLR-RM/stable-baselines3>`_ 库进行算法验证，本工程将上述底层环境类进行封装，提供完全适配 `Gym <https://github.com/openai/gym>`_ 和 `Gymnasium <https://github.com/openai/gym>`_ 的环境类

.. raw:: html

      <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
          具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/envs_parallel.py</code>
      </div>
      </br>

Part1 UAV_VAT(适配Gym库)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

        <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
            具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/gym_envs.py</code>中的<code>UAV_VAT(gym.Env)</code>类
        </div>
        </br>

.. raw:: html

  <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        1. <code>__init__</code> ：初始化gym环境(包括 <code>action_space</code> 和 <code>observation_space</code>的初始化)
  </div>
  </br>

**输入参数：**

* :code:`arg_worker(int)` ：进程数
* :code:`conf_path(list)` ：环境端配置文件路径
* :code:`env_conf_path(list)` ：仿真器端配置文件路径
* :code:`process_idx(list)` ：当前进程序号

.. raw:: html 

  <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        2. <code>reset</code> ：重置环境,返回初始状态
  </div>
  </br>

**返回参数：**

* :code:`state(np.ndarray)` ：返回状态(图像)

.. raw:: html 

  <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        3. <code>step</code> ：环境交互,输入动作，获取状态信息
  </div>
  </br>

**输入参数：**

* :code:`action(torch.tensor)` ：动作

**返回参数：**

* :code:`state(np.ndarray)` ：返回状态(图像)
* :code:`reward(float)` ：奖励
* :code:`done(int)` ：环境是否结束
* :code:`info(dict)` ：信息，其中包括 :code:`info["TimeLimit.truncated"]` 说明是否由于step结束带来的reset

Part2 UAV_VAT_Gymnasium(适配Gymnasium库)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Gymnasium环境与Gym环境大体兼容，以下说明与gym环境的 **区别**

.. raw:: html

  <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
      具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/gym_envs.py</code>中的<code>UAV_VAT_Gymnasium(gymnasium.Env)</code>类
  </div>
  </br>

.. raw:: html 

  <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        1. <code>reset</code> ：重置环境,返回初始状态
  </div>
  </br>

**输入参数：**

* :code:`seed(int)` ：随机种子

**返回参数：**

* :code:`reset_info(dict)` ：重置环境信息(默认为空)

.. raw:: html 

  <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
        2. <code>step</code> ：环境交互,输入动作，获取状态信息
  </div>
  </br>

**返回参数：**

* :code:`truncated(bool)` ：是否由于step结束带来的reset(相当于gym环境中的 :code:`info["TimeLimit.truncated"]` )

Part3 调用接口
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

  <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
      具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/envs_parallel.py</code>中的<code>make_env()</code>函数
  </div>
  </br>

.. raw:: html 

  <div style="background-color: #FDF5E6; padding: 15px; border-radius: 5px; border: 1px solid #EEC591;">
        <code>make_env</code> ：初始化多个gym环境
  </div>
  </br>

**输入参数：**

* :code:`n_envs(int)` ：环境数量
* :code:`rank(int)` ：当前环境序号
* :code:`gym(bool)` ： 如果为:code:`True` 则生成gym库的环境； 如果为:code:`False` 则生成gymnasium库的环境
* :code:`monitor(bool)` ：是否需要封装成 :code:`stable_baselines3.common.monitor.Monitor` 类

**测试代码：**

.. raw:: html

  <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
      具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/envs_parallel.py</code>中的<code>gym_test()</code>函数和<code>stableparallel_test()</code>函数
  </div>
  </br>

如果希望快速测试对上述环境类的改写是否成功，可以用如下的代码：

1. 单进程(仅使用gym环境)

  .. code:: python

    from gym.envs.registration import register

    register(
        id='UAVVAT-v0',
        entry_point='gym_envs:UAV_VAT',
    )

    gym_test()

  2. 利用stable-baselines3进行算法测试

  .. code:: python

    stableparallel_test(n_envs=16,gym=False)


.. raw:: html

    <span style="background-color: yellow;">To Do: 冬青Parallel类书写</span>

.. _Parallel:


3 并行环境类(Envs)
-------------------------------------------------

  .. raw:: html 

    <div style="background-color: #fce6ea; padding: 15px; border-radius: 5px; border: 2px solid #FF6A6A">
      &nbsp;&nbsp;&nbsp;&nbsp;上述底层环境类(BenchEnv_Multi)设计目标是<b>多进程异步计算</b>(例如A3C算法)，在单独进程内调用环境类获取数据</br>
      &nbsp;&nbsp;&nbsp;&nbsp;为了更好利用显卡并行加速，将上述类数据同步、同指令并行，使算法可以<b>单进程工作在同步并行的数据流上</b>，引申出本类(Envs)</br>
      &nbsp;&nbsp;&nbsp;&nbsp;本环境主要适配<b>用户的自主算法设计需求</b>(不使用stable-baselines3等基于Gym环境进行算法实现的情况)
    </div>
    </br>
  

  .. raw:: html

    <div style="border-left: 4px solid #d3d3d3; padding-left: 10px; margin-left: 0;">
        具体代码见 <code>Alg_Base/rl_a3c_pytorch_benchmark/envs/envs_parallel.py</code>中的<code>Envs</code>类
    </div>
    </br>

  **数据格式对比：**
  
  * 封装前(BenchEnv_Multi): 

    数据采样： :code:`state:ndarray,reward:float,done:float= env.step(action:int)` 

    环境重置： :code:`state:ndarray = env.reset()`

  * 封装后(Envs),设并行数n： 

    数据采样： :code:`states:ndarray(n,),rewards:ndarray(n),done:ndarray(n)= env.step(action:ndarray(n))` 

    环境重置： :code:`states:ndarray(n,) = envs.reset()`
