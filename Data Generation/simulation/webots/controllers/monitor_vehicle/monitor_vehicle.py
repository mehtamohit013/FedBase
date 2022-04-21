from controller import Supervisor
import numpy as np
import time
import os
import math
import pandas as pd
from lxml import etree as et

# Data paths
HOME = os.environ['HOME']
cpath = os.path.join(HOME,'webots_code','comms_lidar_ML','config.xml')

root = et.parse(cpath).getroot()
data_dir = root[0].text
dpath = os.path.join(data_dir,'samples')
lpath = os.path.join(data_dir,'lidar_samples')
tpath = os.path.join(data_dir,'tracking')

os.makedirs(tpath,exist_ok=True)
os.makedirs(dpath, exist_ok=True)
os.makedirs(lpath, exist_ok=True)

start = time.time()

robot = Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')

dpath = os.path.join(dpath,f'gps_sample_{car}.pkl')
tpath = os.path.join(tpath,f'gps_pd_{car}.feather')


# DataFrames to store both tracking data as well as GPS samples
tracking = pd.DataFrame(columns=['Time','gps','speed','model'])
gps_sample = pd.DataFrame(columns=['Time','Name','Model','GPS','Speed','Lidar','BS'])

# Timesteps
timestep = 128 # Simulation Timestep
data_timestep = 1920 # Data Collection timestep
prev_time = 0

# Extracting the Supervisor Node of the vehicle
car_node = robot.getSelf()

# Base Station location in [Lat,Lon,Height]
# Number of Base Stations = 3
sites = np.array([
    [38.89502,-77.07303,5],
    [38.89442,-77.07294,5],
    [38.89452,-77.07358,5]
])

# use_site = 1 # Which site to use for generating data
# BS = sites[use_site]
BS = sites
antenna_range = 100 #Range of the transmitter antenna, taken as 100m

# Sensors
lidar = robot.getDevice('Velo')
gps_cn = robot.getDevice('gps_center')
gps_fr = robot.getDevice('gps_front')
gps_re = robot.getDevice('gps_rear')
gps_cn.enable(timestep)
gps_fr.enable(timestep)
gps_re.enable(timestep)

# Enabling Lidar
def enable_lidar(lidar):
    lidar.enable(timestep)
    lidar.enablePointCloud()

# Disabling lidar
def disable_lidar(lidar):
    lidar.disablePointCloud()
    lidar.disable()

# Determining the distance between car and transmitter in meter
# TO-DO : Consider height while calculating distance
def dist_gps(gps1, gps2):
    lat1, lon1, _ = gps1
    lat2, lon2, _ = gps2
    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Function for reading and saving data, both LiDAR and GPS
def read_save_data(lidar, gps_val:list,gps_speed:float,
                    BS:np.ndarray,BS_Range:np.ndarray,
                    car_model:str, car_node,siml_time:float,
                    gps_sample:pd.DataFrame,car_name=car):
    
    lidar_timestep = np.zeros((288000, 3), dtype=np.float32)  # For Velodyne HDL 64E
    cloud = lidar.getPointCloud()

    for i in range(0, 288000):
        lidar_timestep[i, 0] = float(cloud[i].x)
        lidar_timestep[i, 1] = float(cloud[i].y)
        lidar_timestep[i, 2] = float(cloud[i].z)
        
    rotation = car_node.getField('rotation')    # Getting Angular Position of the vehicle

    # Saving LiDAR data in .npz file
    np.savez(lpath + f'/{car}{siml_time:.1f}.npz', 
             lidar=lidar_timestep,
             translation=car_node.getPosition(),
             rotation=rotation.getSFRotation(),
             sites = BS_Range)

    # Adding the GPS data to the dataframe
    ind = len(gps_sample)
    gps_sample.at[ind,'Time'] = siml_time
    gps_sample.at[ind,'Name'] = car_name
    gps_sample.at[ind,'Model'] = car_model
    gps_sample.at[ind,'GPS'] = gps_val
    gps_sample.at[ind,'Speed'] = gps_speed
    gps_sample.at[ind,'Lidar'] = f'{car}{siml_time:.1f}.npz'
    gps_sample.at[ind,'BS'] = BS

# Saving GPS data at every timestep for accurate tracking of the vehicle
# To be used for constructing vehicular objects in MATLAB
def save_gps(tracking:pd.DataFrame,timestep:float,
            gps_val,gps_speed:float,car_model:str):
    
    ind = len(tracking.index.values)
    tracking.loc[ind,'Time'] = timestep
    tracking.loc[ind,'gps'] = gps_val
    tracking.loc[ind,'speed'] = gps_speed
    tracking.loc[ind,'model'] = car_model

# Main Loop
while robot.step(timestep) != -1:
    
    gps_cn_val = gps_cn.getValues()
    gps_fr_val = gps_fr.getValues()
    gps_re_val = gps_re.getValues()

    speed = gps_cn.getSpeed() 

    gps_val = [gps_fr_val,gps_cn_val,gps_re_val]

    BS_dist = np.ndarray((BS.shape[0],))
  
    siml_time = robot.getTime() 

    # Saving values of gps for all timesteps
    save_gps(tracking,siml_time,gps_val,speed,car_model)

    for i in range(0,BS.shape[0]):
        BS_dist[i] = dist_gps(gps_cn_val,BS[i])

    BS_Range = (BS_dist < antenna_range).astype(int)

    # When the vehcile is in range of all base stations
    # while also ensuring proper data collection time
    if sum(BS_Range)== 3 :
        if(siml_time-prev_time>(data_timestep/1000.000)):
            prev_time = siml_time

            # Enabling lidar point cloud
            # Not globally enabled because consumes a lot resources
            if not lidar.isPointCloudEnabled():
                enable_lidar(lidar)
            else:
                read_save_data(lidar, gps_val,speed,BS,BS_Range, car_model, car_node,siml_time,gps_sample)

    else:
        # Disabling lidar for better performance
        if lidar.isPointCloudEnabled():
            disable_lidar(lidar)

# Saving both tracking and GPS data at the end of simulation.
# Data is also saved even if the simulation is restarted
tracking.to_feather(tpath)
gps_sample.to_pickle(dpath)
print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
