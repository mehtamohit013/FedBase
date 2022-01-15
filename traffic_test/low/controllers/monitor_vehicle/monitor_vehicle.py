from controller import Supervisor
import numpy as np
import time
import os
import math
import pandas as pd

# Data paths
HOME = os.environ['HOME']
dpath = f'{HOME}/webots_code/data/traffic_test/samples'
lpath = f'{HOME}/webots_code/data/traffic_test/lidar_samples'


os.makedirs(dpath, exist_ok=True)
os.makedirs(lpath, exist_ok=True)

start = time.time()

robot = Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')

dpath = os.path.join(dpath,f'gps_sample_{car}.pkl')

tpath = f'{HOME}/webots_code/data/final/tracking'
os.makedirs(tpath,exist_ok=True)
tpath = os.path.join(tpath,f'gps_pd_{car}.feather')

## Dataframe to store data
tracking = pd.DataFrame(columns=['Time','gps','speed','model'])
gps_sample = pd.DataFrame(columns=['Time','Name','Model','GPS','Speed','Lidar','BS'])

'''
Simulation timestep
    Smaller the simulation timestep, higher the accuracy for calculating power 
    using matlab,but bigger the stored file
    When timestep is greater than world timestep, there can be different value
    of world timestep (normally controller_timstep/world_timestep) for the same
    controller timestep 
Data Collection timestep
'''
timestep = 128
data_timestep = 1920
prev_time = 0

# Extracting the Supervisor Node
car_node = robot.getSelf()

# Base Station location in [Lat,Lon,Height]
# NUmber of Base Stations = 3
sites = np.array([
    [[38.89328,-77.07611,5],
    [38.89380,-77.07590,5],
    [38.89393,-77.07644,5]],
    [[38.89502,-77.07303,5],
    [38.89442,-77.07294,5],
    [38.89452,-77.07358,5]]
])

use_site = 1 # Which site to use for generating data
BS = sites[use_site]
antenna_range = 100

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

# Function for reading and saving data
def read_save_data(lidar, gps_val:list,gps_speed:float,
                    BS:np.ndarray,BS_Range:np.ndarray,
                    car_model:str, car_node,siml_time:float,
                    gps_sample:pd.DataFrame,car_name=car):
    
    lidar_timestep = np.zeros((288000, 3), dtype=np.float32)  # For velodyne
    cloud = lidar.getPointCloud()
    # k = 0

    for i in range(0, 288000):
        # if np.isfinite(cloud[i].x) and np.isfinite(cloud[i].y) and np.isfinite(cloud[i].z):
        lidar_timestep[i, 0] = float(cloud[i].x)
        lidar_timestep[i, 1] = float(cloud[i].y)
        lidar_timestep[i, 2] = float(cloud[i].z)
            # k += 1
    # lidar_data = lidar_timestep[:k, :] 

    rotation = car_node.getField('rotation')

    np.savez(lpath + f'/{car}{siml_time:.1f}.npz',
             lidar=lidar_timestep,
             translation=car_node.getPosition(),
             rotation=rotation.getSFRotation(),
             sites = BS_Range)

    ind = len(gps_sample)
    gps_sample.at[ind,'Time'] = siml_time
    gps_sample.at[ind,'Name'] = car_name
    gps_sample.at[ind,'Model'] = car_model
    gps_sample.at[ind,'GPS'] = gps_val
    gps_sample.at[ind,'Speed'] = gps_speed
    gps_sample.at[ind,'Lidar'] = f'{car}{siml_time:.1f}.npz'
    gps_sample.at[ind,'BS'] = BS

# Saving GPS data at every time instant
# To be used for constructing vehicular objects in MATLAB
# Using pandas to save data in a pickled format
def save_gps(tracking:pd.DataFrame,timestep:float,
            gps_val,gps_speed:float,car_model:str):
    
    ind = len(tracking.index.values)
    tracking.loc[ind,'Time'] = timestep
    tracking.loc[ind,'gps'] = gps_val
    tracking.loc[ind,'speed'] = gps_speed
    tracking.loc[ind,'model'] = car_model


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

    if sum(BS_Range)== 3 :
        if(siml_time-prev_time>(data_timestep/1000.000)):
            prev_time = siml_time
            if not lidar.isPointCloudEnabled():
                enable_lidar(lidar)
            else:
                read_save_data(lidar, gps_val,speed,BS,BS_Range, car_model, car_node,siml_time,gps_sample)

    else:
        if lidar.isPointCloudEnabled():
            disable_lidar(lidar)

tracking.to_feather(tpath)
gps_sample.to_pickle(dpath)
print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
