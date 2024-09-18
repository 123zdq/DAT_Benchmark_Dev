Overview
=================

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
                window.location.href = '../zh/Overview.html';
            } else if (lang === 'en') {
                window.location.href = '../en/Overview.html';
            }
        }
    </script>
    </br>
    <hr style="border: 2px solid #d3d3d3; width: 95%; margin: 10px auto;">
    </br>
    </br>


1 Visual Active Tracking
------------------------------------

VAT Task
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Real-world Task**: A real-world visual task where the target exhibits high dynamic characteristics. The main challenge is actively controlling the camera to improve visual accuracy.
* **Existing Methods**: Existing PVT (Passive Visual Tracking) methods are based on the assumption that the target remains within a preset frame, only tracking in the video dimension.
* **VAT Task**: VAT (Visual Active Tracking) simultaneously models visual tracking and control, achieving active camera control to track dynamic targets, making it more realistic.


.. figure:: ./_static/image/VisualActiveTracking.png
   :alt: Visual Active Tracking
   :width: 600px
   :align: center

   Differences between VAT Tasks and PVT Settings

.. raw:: html

    </br>

VAT Scheme
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Existing VAT Scheme**: Directly connect the VT model and the control model for VAT (e.g., siamask+PID)

   **Limitation 1**: The visual model requires a lot of manual labeling

   **Limitation 2**: The control model is sensitive to parameters and requires parameter fine-tuning for each different scenario

* **This Project's VAT Scheme**: Use MDP (Markov Decision Process) to model both visual and control tasks simultaneously, solving visual and control tasks with a single model

   **Advantage**: End-to-end RL is more efficient and better suited for cross-scenario tasks

.. figure:: ./_static/image/1_2stages.png
   :alt: VAT Model
   :width: 600px
   :align: center

   Single-Stage and Two-Stage VAT Scheme Illustration

2 Benchmark Presentation
------------------------------------

* **Diversity**：

   * **Scenario Diversity**: Equipped with 6 scenarios and 4 weather conditions, totaling 24 environments

   * **Target Diversity**: Preset 24 selectable targets, supporting the integration of custom models

   * **Task Diversity**: Equipped with 6 common vision and motion sensors

* **Complexity**：

   * **Complex Scene Elements**: The scene elements are complex, covering common elements such as tree occlusion, tunnels, traffic lights, sidewalks, etc.

   * **Complex Dynamic Models**: Utilizing Webots' highly realistic dynamic engine to achieve dynamic simulation in the virtual environment

   * **Complex Target Behavior Management**: Integrating the traffic simulator SUMO for unified vehicle management, ensuring the realism and randomness of Target actions in the environment

Diverse Simulation Scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For detailed scenarios, see: :ref:`Environment Introduction`


.. figure:: ./_static/image/24Scene_Colorful2.png
   :alt: 24 Scenes
   :width: 600px
   :align: center

   24 Complex Scene Examples


Diverse Tracking Targets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


For details on tracking target objects, see: :ref:`Tracked Objects`


.. figure:: ./_static/image/24Target.png
   :alt: 24 Targets
   :width: 600px
   :align: center

   24 Different Targets

Diverse Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Task Diversity**: The state provides sensors commonly found in real-world scenarios, such as IMU, accelerometer, gyroscope, LiDAR, etc.

For diverse task configurations, see: :ref:`customized parameter interface`

.. figure:: ./_static/image/sensor_list.png
   :alt: Sensor list
   :width: 600px
   :align: center

   6 Common Sensors
