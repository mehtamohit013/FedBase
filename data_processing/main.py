import os
import numpy as np
import pandas as pd
import pickle
import time
import multiprocessing as mp

from process_gps import GEngine
from process_lidar import LEngine
from process_OSM import HOME, OSMEngine

HOME = os.environ['HOME']
lpath = os.path.join(HOME,'webots_code','data','final','lidar_samples')
gpath = os.path.join(HOME,'webots_code','data','final','samples')
tpath = os.path.join(HOME,'webots_code','data','final','tracking')
opath = os.path.join(HOME,'webots_code','data','final','OSM')
matpath = os.path.join(HOME,'webots_code','data','final','MAT')
gspath = os.path.join(HOME,'webots_code','data','final','gps.pkl')

os.makedirs(opath,exist_ok=True)

timestep = 0.128

use_site = 1
site_origin = np.array([
    [[-170,5,-113],
    [-112,5,-95],
    [-97.7,5,-139]],
    [[18.3,5,162],
    [-51.1,5,169],
    [-44.4,5,117]]
])
origins = site_origin[use_site]
n_sites = origins.shape[0]

steps = np.array([1.0, 0.5, 1.0]) #Step size (x,y,z) #For Quantization
cube = [-1, 1, -5, 5, -3, 3] # cube to remove, centered at lidar, before origin shift

print(f'Starting Lidar preprocessing'+'.'*10)
lidar = LEngine(lpath,cube,steps,origins)
with mp.Pool() as p:
    p.map(lidar,os.listdir(lpath))
print(f'Lidar Preprocessing ended')

print(f'Starting GPS preprocessing'+'.'*10)
gps = GEngine(gpath,matpath)
gps(gspath)
print('GPS preprocessing finished')

print(f'Starting OSM preprocessing'+'.'*10)
osm = OSMEngine(gspath,tpath,opath,timestep)
gps_pd = pd.read_pickle(gspath)

start = time.time()
for count,index in enumerate(gps_pd.index.values):
    osm(index)
    if count%100 == 0 :
        print(f'{count+1} osm files formed.',f'Time: {time.time()-start}')

print(f'OSM preprocessing ended')

print('*'*10+'Preprocessing Ended'+'*'*10)
