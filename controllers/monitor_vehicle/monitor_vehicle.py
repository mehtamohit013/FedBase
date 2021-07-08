from controller import  Supervisor
import numpy as np
import time
import os
import math
import scipy.io

#Data paths
HOME = os.environ['HOME']
dpath = f'{HOME}/webots_code/data/samples'
lpath = f'{HOME}/webots_code/data/lidar_samples'
os.makedirs(dpath,exist_ok=True)
os.makedirs(lpath, exist_ok=True)

start = time.time()

robot =Supervisor()
car = robot.getName()
car_model = robot.getModel()
print(f'Starting subprocess for car {car}')
timestep = 1280

#Extracting the Supervisor Node
car_node = robot.getSelf()

#Location of transmitter in lat and lon
tx1 = np.array([38.8939600,-77.0782300,5])
tx2 = np.array([38.8946400,-77.0784600,5])

lidar = robot.getDevice('Velo')
gps = robot.getDevice('gps')
gps.enable(timestep)

#Enabling Lidar
def enable_lidar(lidar):
    lidar.enable(timestep)
    lidar.enablePointCloud()

#Disabling lidar
def disable_lidar(lidar):
    lidar.disablePointCloud()
    lidar.disable()

#Determining the distance between car and transmitter in meter
def dist_gps(gps1,gps2):
    lat1,lon1,_ = gps1
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
    return R*c

# Function for reading and saving data
def read_save_data(lidar,gps_val,tx1,tx2,car_model,car_node):
    lidar_timestep = np.zeros((288000,3),dtype=np.float32) # For velodyne
    cloud = lidar.getPointCloud()
    k = 0
    
    for i in range(0, 288000):
        if np.isfinite(cloud[i].x) and np.isfinite(cloud[i].y) and np.isfinite(cloud[i].z):
            lidar_timestep[k, 0] = float(cloud[i].x)
            lidar_timestep[k, 1] = float(cloud[i].y)
            lidar_timestep[k, 2] = float(cloud[i].z)
            k += 1
    lidar_data = lidar_timestep[:k, :]
    
    siml_time = robot.getTime()
    rotation = car_node.getField('rotation')

    np.savez(lpath + f'/{car}{siml_time:.1f}.npz',
            lidar=lidar_data,
            translation=car_node.getPosition(),
            rotation=rotation.getSFRotation())

    scipy.io.savemat(dpath+f'/{car}{siml_time:.1f}.mat',
                        dict(gps = gps_val,tx1 = tx1,
                        tx2 = tx2,car_model = car_model))
   

while robot.step(timestep)!=-1:
    gps_val = gps.getValues()
    dist1 = dist_gps(gps_val,tx1)
    dist2 = dist_gps(gps_val,tx2)

    if dist1 <= 100 < dist2:
        print(f'Car {car} is in range of tx1')
        if not lidar.isPointCloudEnabled():
            enable_lidar(lidar)
        else:
            read_save_data(lidar,gps_val,tx1,np.array([]),car_model,car_node)
            
    elif dist2 <= 100 < dist1:
        print(f'Car {car} is in range of tx2')
        if not lidar.isPointCloudEnabled():
            enable_lidar(lidar)
        else:
            read_save_data(lidar,gps_val,np.array([]),tx2,car_model,car_node)
    elif dist1 <= 100 and dist2 <= 100:
        print(f'Car {car} is in range of tx1 and tx2')
        if not lidar.isPointCloudEnabled():
            enable_lidar(lidar)
        else:
            read_save_data(lidar,gps_val,tx1,tx2,car_model,car_node)
    else:
        if lidar.isPointCloudEnabled():
            disable_lidar(lidar)

print(f'Subprocess ended for car {car} after time {(time.time()-start):.2f}')
