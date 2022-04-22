import os
import numpy as np
import pandas as pd
import time
import multiprocessing as mp
import tqdm
from lxml import etree as et

from process_gps import GEngine
from process_lidar import LEngine
from process_OSM import OSMEngine


# Data Paths
HOME = os.environ['HOME']

cpath = os.path.join(HOME,'webots_code','comms_lidar_ML','config.xml')
root = et.parse(cpath).getroot()
data_dir = root[0].text
mpath = root[1].text

lpath = os.path.join(data_dir,'lidar_samples')
gpath = os.path.join(data_dir,'samples')
tpath = os.path.join(data_dir,'tracking')
opath = os.path.join(data_dir,'OSM')
matpath = os.path.join(data_dir,'MAT')
gspath = os.path.join(data_dir,'gps.pkl')

os.makedirs(opath,exist_ok=True)


# Simulation Timestep
timestep = 0.128


# Buggy, Not using currently
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


# Parameters
steps = np.array([1.0, 0.5, 1.0]) #Step size (x,y,z) #For Quantization
cube = [-1, 1, -5, 5, -3, 3] # cube to remove, centered at lidar, before origin shift


# Process Pool: For multiprocessing
p = mp.Pool()

# Lidar Preprocessing
print(f'Starting Lidar preprocessing'+'.'*10)
lidar = LEngine(lpath,cube,steps,origins)
for _ in tqdm.tqdm(p.imap_unordered(lidar,os.listdir(lpath)),total=len(os.listdir(lpath))):
    pass
print(f'Lidar Preprocessing ended')

# GPS Preprocessing
print(f'Starting GPS preprocessing'+'.'*10)
gps = GEngine(gpath,matpath)
gps(gspath)
print('GPS preprocessing finished')

# OSM Preprocessing
print(f'Starting OSM preprocessing'+'.'*10)
osm = OSMEngine(gspath,tpath,opath,timestep,mpath)
gps_pd = pd.read_pickle(gspath)
for _ in tqdm.tqdm(p.imap_unordered(osm,gps_pd.index.values),total=len(gps_pd.index.values)):
    pass
print(f'OSM preprocessing ended')


print('*'*10+'Preprocessing Ended'+'*'*10)
