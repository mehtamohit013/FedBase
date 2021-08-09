from controller import Supervisor
import numpy as np
import time
import os
import math


start = time.time()

HOME = os.environ['HOME']

robot = Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')

spath = f'{HOME}/webots_code/data/stats'
os.makedirs(spath,exist_ok=True)   

'''
Simulation timestep
    Smaller the simulation timestep, higher the accuracy for calculating power 
    using matlab,but bigger the stored file
    When timestep is greater than world timestep, there can be different value
    of world timestep (normally controller_timstep/world_timestep) for the same
    controller timestep 
Data Collection timestep
'''
timestep = 1920
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

while robot.step(timestep) != -1:

    gps_val = gps_cn.getValues()
    speed = gps_cn.getSpeed() 

    BS_dist = np.ndarray((BS.shape[0],))
    for i in range(0,BS.shape[0]):
        BS_dist[i] = dist_gps(gps_val,BS[i])

    BS_Range = (BS_dist < antenna_range).astype(int)

    if sum(BS_Range)== 3 :
        cnt+=1
        ovr_sample+=1
        avg_speed = (avg_speed*(cnt-1) + speed)/cnt

with open(spath+f'/{car}.txt','w') as a:
    a.write(str(ovr_sample))


print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
