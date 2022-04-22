# Project Name

## Installation and Setup

*   ### Webots - Robotic Simulation
    For simulation Webots R2021a has been used. Official download links can be found [here](https://github.com/cyberbotics/webots/releases/tag/R2021a)

*   ### Simulation of Urban Mobility (SUMO)
    For simulation SUMO 1.12.0 has been used. Official installation guide can be found [here](https://sumo.dlr.de/docs/Downloads.php)

*   ### MATLAB
    For simulation MATLAB R2021a has been used. Official release page can be found [here](https://in.mathworks.com/products/new_products/release2021a.html)

*   ### Python Libraries
    *   Using PIP and virtual environment
    *   Using Anaconda/conda


## Config File and data paths
all the data paths, save paths and log paths are stored in ```./config.xml```. In order to modify the above paths, please edit ```./config.xml``` accordingly.

## Instructions to Run
*   Firstly, initiliaze webots simulation by running ```./Data_Generation/simulation/webots/worlds/osm.wbt``` in webots

    ```bash   
    webots ./Data_Generation/simulation/webots/worlds/osm.wbt
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