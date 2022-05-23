# Project Name

## Installation and Setup


We recommend using **Ubuntu 18.04** for this project

>   All the following commands assume that the github repo is located at home folder of the system.

*   ### Webots - Robotic Simulation
    For simulation Webots R2021a has been used. Official download links and installation guide can be found [here](https://github.com/cyberbotics/webots/releases/tag/R2021a), [here](https://cyberbotics.com/doc/guide/installing-webots) and [here](https://cyberbotics.com/doc/guide/using-python)
   
    
    Also, install the following libraries for SUMO
    
    ```bash
    sudo apt-get install libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev
    ```

    Please add the following lines to bashrc/zshrc file or update the env accordingly. The following lines assume that webots has been installed in default location

    ```bash
    WEBOTS_HOME="/usr/local/webots"; export WEBOTS_HOME
    LD_LIBRARY_PATH=${WEBOTS_HOME}/lib/controller;  export LD_LIBRARY_PATH
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${WEBOTS_HOME}/lib;  export LD_LIBRARY_PATH
    ```
        
    Also, for the project we are using python 3.7, so add the following line to your bashrc/zshrc file or to the env.

    ```bash
    PYTHONPATH=${WEBOTS_HOME}/lib/controller/python37; export PYTHONPATH
    ```
    
    Please also note that, for running webots change "python" to "python3" in preferences menu of webots.

*   ### Simulation of Urban Mobility (SUMO)
    For simulation SUMO 1.12.0 has been used. Official installation guide can be found [here](https://sumo.dlr.de/docs/Downloads.php)

    Also add the following lines to bashrc/zshrc accordingly:

    ```bash
    SUMO_HOME="/usr/share/sumo"; export SUMO_HOME
    LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:"/usr/share/sumo/bin";
    ```

*   ### MATLAB
    For simulation MATLAB R2021a has been used. Official release page can be found [here](https://in.mathworks.com/products/new_products/release2021a.html)

*   ### Python Libraries
    In order to ensure all the libraries are working correctly, we recommend either creating a virtual environment using Pyenv (or any other virtual env tool)  or anaconda.

    *   Using PIP and virtual environment
    
        Pyenv Installation Guide: [Link](https://github.com/pyenv/pyenv#installation)

        Pyenv virtualenv installation guide: [Link](https://github.com/pyenv/pyenv-virtualenv#installation)
        
        Create a virtual environment using the following commands
        
        ```bash
        cd ~/comms_lidar_ML
        pyenv install 3.7.11
        pyenv virtualenv 3.7.11 webots_ml
        pyenv local webots_ml
        pip install -r requirements.txt
        ```
    *   Using Anaconda/conda [Installation Guide](https://docs.anaconda.com/anaconda/install/index.html)

        ```bash
        conda env create -f requirements.yml
        conda activate webots_release37
        ```



## Config File and data paths
All the data paths, save paths and log paths are stored in ```./config.json```. In order to modify the above paths, please edit ```./config.json``` accordingly.

*   In order to change the map, change the attribute ```use_map``` to either ```Rossyln``` or ```Chicago```
*   In order to change number of base stations, change the attribute ```use_BS``` to ```BS_3``` or ```BS_5``` accordingly.

## Instructions to Run Simulation and Generate Data
*   Firstly, initiliaze webots simulation by running ```./Data_Generation/simulation/webots/worlds/osm.wbt``` in webots

    ```bash   
    webots ./Data_Generation/simulation/webots/worlds/Rossyln.wbt
    ```
     OR
     
    ```bash   
    webots ./Data_Generation/simulation/webots/worlds/Chicago.wbt
    ```
    
    
*   After running the webots simulation for the required time, **please reset the simulation and then exit webots**. 
The data will be stored at the path specified in config.xml

*   Then run the preprocessing
    ```bash
    python ./Data_Generation/preprocessing/main.py
    ```    
    This will apply necessary preprocessing techniques to LiDAR and constrcut the required OSM files of each data points, which then can be used to accurately calculate power using MATLAB.

*   Now, for final step, run the ```./Data_Generation/simulation/matlab/ray_power.m```

    ```bash
    matlab ./Data_Generation/simulation/matlab/ray_power.m
    ```

## Instructions to run Base station selection
*   To run deep neural network mentioned in the paper, pleas run ```./Base_Station_Selection/main.py```
    ```
    python ./Base_Station_Selection/main.py
    ```
