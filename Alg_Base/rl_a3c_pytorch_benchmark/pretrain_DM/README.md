### Use For Pretraining Dynamics Model
1. Model Structure
   * Backbone: Load Resnet18 pertrained on ResNet as Backbone
   * Train Mode: Dynamics Model head train in supervised mode
   1. Setting 1: Just train Dynamics Model head
   2. Setting 2: Simultaneously train Dynamics Model head and backbone
2. Data Collection
   * Collect Data in Created Environment in Webots
3. Configuration
   * Config file: **pretrain_cfg.json**
   * Attribute:
     * **Mode:** Training Mode
       * "Head_only": Train Dynamics Model Head Only
       * "Head_backbone": Train Dynamics Model Head and Backbone simultaneously
     * **State_Buffer:** Number of Frame use as Input
     * **Action_Buffer:** Number of Action use as Input
     * **Model_Type:** Pretrained Model Type
       * "resnet18": 'https://download.pytorch.org/models/resnet18-5c106cde.pth',
       * "resnet34": 'https://download.pytorch.org/models/resnet34-333f7ec4.pth',
     * **State_size:** Input image size
     * **State_channel:** use Grayscale or RGB image as state 
