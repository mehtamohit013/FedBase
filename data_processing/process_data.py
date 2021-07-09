import os
import numpy as np
import math

def quantize(data: np.ndarray, steps: np.ndarray) -> np.ndarray:
    data = np.around(data/steps)
    data = data*steps
    data = np.unique(data, axis=0)
    return data

def pts_around_cube(data: np.ndarray, cube: list) -> np.ndarray:
    x_ind = np.where(cube[0] < data[:, 0], 1, 0) * \
        np.where(data[:, 0] < cube[1], 1, 0)
    y_ind = np.where(cube[2] < data[:, 1], 1, 0) * \
        np.where(data[:, 1] < cube[3], 1, 0)
    z_ind = np.where(cube[4] < data[:, 2], 1, 0) * \
        np.where(data[:, 2] < cube[5], 1, 0)
    cube_ind = x_ind*y_ind*z_ind
    data = data - data*cube_ind[:, None]
    return np.unique(data, axis=0)

def shift_origin(data:dict,origin:np.ndarray) -> np.ndarray :
    
    lidar_data = data['lidar']
    translation = data['translation']
    rotation = data['rotation']

    lidar_origin = np.copy(lidar_data)
    theta = rotation[-1]
    lidar_origin[:,0] = lidar_data[:,0]*math.cos(theta) + lidar_data[:,2]*math.sin(theta) \
                         + translation[0] - origin[0]
    lidar_origin[:,2] = lidar_data[:,2]*math.cos(theta) - lidar_data[:,0]*math.sin(theta) \
                         + translation[2] - origin[2]
    lidar_origin[:,1] += 2.2
    
    return lidar_origin

def lidar_array(steps:np.ndarray,data:np.ndarray) -> np.ndarray:
    #Add Support for transmitter and receiver
    #Eliminate for loop
    lidar = np.zeros((20,440,440)) # [y,z,x]
    data = data / steps
    for i in range(0,data.shape[0]):
        x,y,z =0,0,0
        x,y,z = data[i].astype(int)
        x+=120
        z+=120
        lidar[y,x,z] = 1 #1 is for obstacles
    
    return lidar

def rename(dpath:str,lpath:str):
    for count, filename in enumerate(os.listdir(dpath)):
        dst1 = dpath +'/' + str(count) + ".mat"
        src1 = dpath +'/'+ filename

        dst2 = lpath + '/' + str(count)+".npz"
        src2 = lpath + '/' + filename[:-3]+ "npz"

        # rename() function will
        # rename all the files
        os.rename(src1, dst1)
        os.rename(src2, dst2)

if __name__ == '__main__':

    HOME = os.environ['HOME']
    dpath = f'{HOME}/webots_code/data/samples'
    lpath = f'{HOME}/webots_code/data/lidar_samples'

    #Renaming
    # rename(dpath,lpath)
    
    steps = np.array([1.0, 0.5, 1.0]) #Step size (x,y,z)
    cube = [-1, 1, -5, 5, -3, 3] # cube to remove, centered at lidar, before origin shift
    origins = np.array([[-128.22,0,-274.59],[-9.11,0,-338.14]]) #Coords of transmitter
    n_sites = origins.shape[0]
    range_site = 100 #Range of a transmitter
    data_pp = np.array([1]) # Indicator whether preprocessing done or not


    for count,filename in enumerate(os.listdir(lpath)):
        data = dict(np.load(os.path.join(lpath,filename)))

        # Checking if the data is already pre-processed 
        if ('data_pp' in data):
            print('Data already pre-processed.\nEdit the code for further processing.\nExiting.........')
            exit(0)

        #Purging points around the car
        data['lidar'] = pts_around_cube(data['lidar'],cube)

        sites_in = list() #Sites in range
        lidar = list()

        for i in range(0,n_sites):
            if math.sqrt(sum((data['translation']-origins[i])**2)) < range_site:
                sites_in.append(i)
                lidar_origin = shift_origin(data,origins[i])
                lidar_quantize = quantize(lidar_origin,steps)
                lidar_ML = lidar_array(steps,lidar_quantize) #Preparing data for ML
                lidar.append(lidar_ML) 
        
        data['lidar'] = np.array(lidar)

        #Saving data
        np.savez_compressed(os.path.join(lpath,filename),
                lidar = data['lidar'],
                translation = data['translation'],
                rotation = data['rotation'],
                sites = np.array(sites_in),
                data_pp = data_pp)
        
        if count%5 == 0:
            print(f'files done: {count}')