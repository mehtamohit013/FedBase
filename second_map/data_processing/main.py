import os
import numpy as np
import pandas as pd
import time
import multiprocessing as mp
import tqdm

from process_gps import GEngine
from process_lidar import LEngine
from process_OSM import HOME, OSMEngine

HOME = os.environ['HOME']
lpath = os.path.join(HOME,'webots_code','data','chicago','lidar_samples')
gpath = os.path.join(HOME,'webots_code','data','chicago','samples')
tpath = os.path.join(HOME,'webots_code','data','chicago','tracking')
opath = os.path.join(HOME,'webots_code','data','chicago','OSM')
matpath = os.path.join(HOME,'webots_code','data','chicago','MAT')
gspath = os.path.join(HOME,'webots_code','data','chicago','gps.pkl')

os.makedirs(opath,exist_ok=True)

timestep = 0.128

# use_site = 1
site_origin = np.array(
    [[134,5,-266],
    [145,5,-316],
    [210,5,-268]])
origins = site_origin
n_sites = origins.shape[0]

steps = np.array([1.0, 0.5, 1.0]) #Step size (x,y,z) #For Quantization
cube = [-1, 1, -5, 5, -3, 3] # cube to remove, centered at lidar, before origin shift

p = mp.Pool()

print(f'Starting Lidar preprocessing'+'.'*10)
lidar = LEngine(lpath,cube,steps,origins)

for _ in tqdm.tqdm(p.imap_unordered(lidar,os.listdir(lpath)),total=len(os.listdir(lpath))):
    pass
print(f'Lidar Preprocessing ended')

print(f'Starting GPS preprocessing'+'.'*10)
gps = GEngine(gpath,matpath)
gps(gspath)
print('GPS preprocessing finished')

print(f'Starting OSM preprocessing'+'.'*10)
osm = OSMEngine(gspath,tpath,opath,timestep)
gps_pd = pd.read_pickle(gspath)

start = time.time()
for _ in tqdm.tqdm(p.imap_unordered(osm,gps_pd.index.values),total=len(gps_pd.index.values)):
    pass

print(f'OSM preprocessing ended')

print('*'*10+'Preprocessing Ended'+'*'*10)
