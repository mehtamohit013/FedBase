import pickle
from controller import Supervisor
import numpy as np
import time
import os
import math
import pandas as pd


start = time.time()

HOME = os.environ['HOME']

robot = Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')

spath = f'{HOME}/webots_code/data/stats'
gpath = f'{HOME}/webots_code/data/stats/gps'
dpath = f'{HOME}/webots_code/data/stats/data'

os.makedirs(spath,exist_ok=True)   
os.makedirs(gpath,exist_ok=True)
os.makedirs(dpath,exist_ok=True)

gpath = os.path.join(gpath,f'gps_pd_{car}.feather')

'''
Simulation timestep
    Smaller the simulation timestep, higher the accuracy for calculating power 
    using matlab,but bigger the stored file
    When timestep is greater than world timestep, there can be different value
    of world timestep (normally controller_timstep/world_timestep) for the same
    controller timestep 
Data Collection timestep
'''
timestep = 256
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

gps_cn = robot.getDevice('gps_center')
gps_cn.enable(timestep)

# Factors to monitor
ovr_sample = 0 # Number of sample per car
avg_speed = 0 #Avg speed of car when in range
cnt=0 #Number of times a vehicle appears in range of three BS

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

def save_data(gps_val:list,speed:float,BS:np.ndarray,
            siml_time:float,car_model:str=car_model,
            car_name:str=car):
    
    with open(dpath+f'/{car}{siml_time:.1f}.pkl','wb') as a:
        pickle.dump(siml_time,a)
        pickle.dump(car_name,a)
        pickle.dump(car_model,a)
        pickle.dump(gps_val,a)
        pickle.dump(speed,a)
        pickle.dump(BS,a)
    

# Saving GPS data at every time instant
# To be used for constructing vehicular objects in MATLAB
# Using pandas to save data in a pickled format
def save_gps(siml_time:float,gps_val,gps_speed:float,car_model:str):
    
    try:
        gps_pd = pd.read_feather(gpath)
        ind = int(gps_pd.index.values[-1])+1
    except:
        gps_pd = pd.DataFrame(columns=['timestep','gps','speed','model'])
        ind = 0

    gps_pd.at[ind,'timestep'] = siml_time
    gps_pd.at[ind,'gps'] = gps_val
    gps_pd.at[ind,'speed'] = gps_speed
    gps_pd.at[ind,'model'] = car_model

    gps_pd.to_feather(gpath)


while robot.step(timestep) != -1:
    siml_time = robot.getTime()

    gps_val = gps_cn.getValues()
    speed = gps_cn.getSpeed()
    save_gps(siml_time,gps_val,speed,car_model) 

    BS_dist = np.ndarray((BS.shape[0],))
    for i in range(0,BS.shape[0]):
        BS_dist[i] = dist_gps(gps_val,BS[i])

    BS_Range = (BS_dist < antenna_range).astype(int)

    if sum(BS_Range)== 3 :
        if(siml_time-prev_time>(data_timestep/1000.000)):
            cnt+=1
            ovr_sample+=1
            avg_speed = (avg_speed*(cnt-1) + speed)/cnt
            save_data(gps_val,speed,BS,siml_time,car_model,car)
            prev_time = siml_time

with open(spath+f'/{car}.txt','wb') as a:
    pickle.dump(ovr_sample,a)
    pickle.dump(avg_speed,a)


print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
