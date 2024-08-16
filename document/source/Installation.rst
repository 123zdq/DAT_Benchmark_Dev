安装
=============

.. raw:: html

    <div style="background-color: #FDF5E6; padding: 15px; border-radius: 5px; border: 1px solid #EEC591;">
        本文档主要提供 <code>Linux</code>系统(<code>Ubuntu22.04</code>)以及<code>Windows</code>系统下的工程安装指引
    </div>
    </br>

Linux(Ubuntu22.04)
------------------------

.. raw:: html

      <div style="background-color: #e5f1fe; padding: 15px; border-radius: 5px; border: 1px solid #1874CD;">
            选择<code>Ubuntu22.04</code>是由于我们使用的仿真引擎<code>webots2023b</code>适配的Linux系统版本为<code>Ubuntu22.04</code>
            如果安装了其他版本的Linux系统，可以参考 <a href="https://github.com/cyberbotics/webots">webots</a>的代码仓库下载配置合适的版本
      </div>
      </br>

Step1 安装webots仿真软件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    从 `webots <https://github.com/cyberbotics/webots>`_ 下载webots2023b版本软件(例如： :code:`webots-R2023b-x86-64.tar.bz2` )和资产文件( :code:`assets-R2023b.zip` )，可以用如下命令解压和安装

    **webots解压与安装**

    .. code:: bash
        
        ## unpack
        sudo tar -jxvf webots-R2023b-x86-64.tar.bz2 -C /opt
        
        ## config
        gedit ~/.bashrc
        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/webots/lib/webots

        ## run
        cd /opt/webot/bin
        ./webots-bin

    **assets解压**

    .. code:: bash
        
        cp ~/Downloads/assets-R2023b.zip ~/.cache/Cyberbotics/Webots/assets/
        
        ## unzip
        cd ~/.cache/Cyberbotics/Webots/assets/
        unzip ./assets-R2023b.zip

Step2 创建虚拟环境与库安装
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    **虚拟环境创建**

    .. code:: bash

        conda create -n uav_follow39 python=3.9
        conda activate uav_follow39

    **算法端**

    .. code:: bash

        ## Alg requirements
        pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu121
        pip install opencv-python==4.9.0.80
        pip install gym==0.25.1
        pip install setproctitle==1.3.3
        pip install tensorboard
        pip install tqdm
        pip install stable-baselines3==2.3.0
        pip install sb3_contrib==2.3.0
        pip install gymnasium==0.29.1
        pip install wandb==0.17.6

    **仿真器端**

    .. code:: bash

        ## Simulator requirements
        sudo apt-get install libeigen3-dev
        sudo apt-get install nlohmann-json3-dev

        sudo apt install sumo sumo-tools sumo-doc
        pip install lxml pyproj shapely webcolors configparser --user
        pip install transform3d

        ## config
        gedit ~/.bashrc
        # Change dir according to your installation
        export SUMO_HOME=/usr/share/sumo
        export WEBOTS_HOME=/opt/webots

Step3 修改webots运行python环境
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

    <span style="background-color: yellow;">To Do：补充一下软链接和webots配置的图文</span>
    

Windows
------------------------
.. raw:: html

    <span style="background-color: yellow;">To Do</span>