import os
import numpy as np
import math

def elim_inf(data:np.ndarray):
    lidar = np.zeros((288000, 3), dtype=np.float32)
    k = 0
    for i in range(data.shape[0]):
        try:
            if np.isfinite(data[i,0]) and np.isfinite(data[i,1]) and np.isfinite(data[i,2]):
                lidar[k,0] = data[i,0]
                lidar[k,1] = data[i,1]
                lidar[k,2] = data[i,2]
                k+=1
        except:
            print(data.shape)
    return lidar[:k,:]


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

def lidar_array(steps:np.ndarray,data:np.ndarray,
                translation:np.ndarray,origins:np.ndarray,
                oshift:bool=False) -> np.ndarray:
    
    #Obstacles = 1, transmitter = 2, receiver = 3
    #Eliminate for loop

    lidar = np.zeros((10,240,240)) # [y,z,x]
    data = data / steps
    for i in range(0,data.shape[0]):
        x,y,z =0,0,0
        x,y,z = data[i].astype(int)
        if oshift:
            x+=120
            z+=120
        lidar[y,x,z] = 1 #1 is for obstacles
    
    if oshift:
        lidar[10,120,120] = 2 #TX
        lidar[4,int(translation[0]-origins[0]+120),int(translation[2]-origins[2]+120)] = 3 #RX
    else:
        lidar[4,0,0] = 3

    return lidar

class LEngine():
    def __init__(self,lpath:str,cube:np.ndarray,step:np.ndarray,
                origins:np.ndarray,oshift:bool=False,) -> None:
        self.lpath = lpath
        self.data_pp = np.array([1])
        self.cube = cube
        self.steps = step
        self.oshift = oshift
        self.origins = origins
        self.n_sites = self.origins.shape[0]
    
    def __call__(self, filename:str) -> None:
        ldata = dict(np.load(os.path.join(self.lpath,filename)))
        if not('data_pp' in ldata.keys()):
            if self.oshift:
                sites_in = ldata['sites'] #Sites in range
                lidar = list()
                for i in range(0,self.n_sites):
                    if sites_in[i]:
                        lidar_origin = shift_origin(ldata,self.origins[i])
                        lidar_quantize = quantize(lidar_origin,self.steps)
                        lidar_ML = lidar_array(self.steps,lidar_quantize,
                                                ldata['translation'],
                                                self.origins[i],self.oshift) #Preparing data for ML
                        lidar.append(lidar_ML)
                ldata['lidar'] = np.array(lidar)
            else:
                ldata['lidar'] = elim_inf(ldata['lidar'])
                ldata['lidar'] = quantize(ldata['lidar'],self.steps)
                ldata['lidar'] = pts_around_cube(ldata['lidar'],self.cube)
                ldata['lidar'] = lidar_array(self.steps, ldata['lidar'],ldata['translation'], self.origins)
            np.savez_compressed(os.path.join(self.lpath,filename),
                        lidar = ldata['lidar'],
                        translation = ldata['translation'],
                        rotation = ldata['rotation'],
                        sites = ldata['sites'],
                        data_pp = self.data_pp)