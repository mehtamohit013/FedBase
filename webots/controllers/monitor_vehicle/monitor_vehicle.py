from controller import Supervisor
import numpy as np
import time
import os
import math
import scipy.io
import pandas as pd

# Data paths
HOME = os.environ['HOME']
dpath = f'{HOME}/webots_code/data/samples'
lpath = f'{HOME}/webots_code/data/lidar_samples'

os.makedirs(dpath, exist_ok=True)
os.makedirs(lpath, exist_ok=True)

start = time.time()

robot = Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')

gpath = f'{HOME}/webots_code/data/tracking'
os.makedirs(gpath,exist_ok=True)
gpath = os.path.join(gpath,f'gps_pd_{car}.xz')

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
data_timestep = 1280
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
def read_save_data(lidar, gps_val:list,BS:np.ndarray,BS_Range:np.ndarray,
                 car_model:str, car_node,siml_time:float,car_name=car):
    
    lidar_timestep = np.zeros((288000, 3), dtype=np.float32)  # For velodyne
    cloud = lidar.getPointCloud()
    k = 0

    for i in range(0, 288000):
        if np.isfinite(cloud[i].x) and np.isfinite(cloud[i].y) and np.isfinite(cloud[i].z):
            lidar_timestep[k, 0] = float(cloud[i].x)
            lidar_timestep[k, 1] = float(cloud[i].y)
            lidar_timestep[k, 2] = float(cloud[i].z)
            k += 1
    lidar_data = lidar_timestep[:k, :] 

    rotation = car_node.getField('rotation')

    np.savez(lpath + f'/{car}{siml_time:.1f}.npz',
             lidar=lidar_data,
             translation=car_node.getPosition(),
             rotation=rotation.getSFRotation(),
             sites = BS_Range)

    scipy.io.savemat(dpath + f'/{car}{siml_time:.1f}.mat',
                     dict(gps=gps_val, BS=BS,
                          BS_Range = BS_Range,
                          car_model=car_model,
                          car_name=car_name,
                          siml_time = siml_time))

# Saving GPS data at every time instant
# To be used for constructing vehicular objects in MATLAB
# Using pandas to save data in a pickled format
def save_gps(timestep:float,gps_val,car_model:str):
    
    try:
        gps_pd = pd.read_pickle(gpath)
        ind = gps_pd.index.values[-1]+1
    except:
        gps_pd = pd.DataFrame(columns=['timestep','gps','model'])
        ind = 0
    
    gps_pd.loc[ind,'timestep'] = timestep
    gps_pd.loc[ind,'gps'] = gps_val
    gps_pd.loc[ind,'model'] = car_model

    gps_pd.to_pickle(gpath)


while robot.step(timestep) != -1:
    
    gps_cn_val = gps_cn.getValues()
    gps_fr_val = gps_fr.getValues()
    gps_re_val = gps_re.getValues()

    gps_val = [gps_fr_val,gps_cn_val,gps_re_val]

    BS_dist = np.ndarray((BS.shape[0],))
  
    siml_time = robot.getTime() 

    # Saving values of gps for all timesteps
    save_gps(siml_time,gps_val,car_model)

    for i in range(0,BS.shape[0]):
        BS_dist[i] = dist_gps(gps_cn_val,BS[i])

    BS_Range = (BS_dist < antenna_range).astype(int)

    if sum(BS_Range)== 3 :
        if(siml_time-prev_time>(data_timestep/1000.000)):
            print(f'Car {car} is in range of {BS_Range}->[BS1,BS2,BS3]')
            prev_time = siml_time
            if not lidar.isPointCloudEnabled():
                enable_lidar(lidar)
            else:
                read_save_data(lidar, gps_val,BS,BS_Range, car_model, car_node,siml_time)

    else:
        if lidar.isPointCloudEnabled():
            disable_lidar(lidar)

print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
