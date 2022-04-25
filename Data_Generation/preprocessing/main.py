import os
import numpy as np
import pandas as pd
import multiprocessing as mp
import tqdm
import json

from process_gps import GEngine
from process_lidar import LEngine
from process_OSM import OSMEngine


# Data Paths
HOME = os.environ['HOME']

cpath = os.path.join(HOME,'webots_code','comms_lidar_ML','config.xml')
config = json.load(open('./config.json'))
data_dir = config['dpath']
mpath = config[config['use_map']]['mpath']

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
# use_site = 1
# site_origin = np.array([
#     [[-170,5,-113],
#     [-112,5,-95],
#     [-97.7,5,-139]],
#     [[18.3,5,162],
#     [-51.1,5,169],
#     [-44.4,5,117]]
# ])
# origins = site_origin[use_site]
n_sites = len(config[config['use_map']][config['use_BS']])


# Parameters
steps = np.array([1.0, 0.5, 1.0]) #Step size (x,y,z) #For Quantization
cube = [-1, 1, -5, 5, -3, 3] # cube to remove, centered at lidar, before origin shift


# Process Pool: For multiprocessing
p = mp.Pool()

# Lidar Preprocessing
print(f'Starting Lidar preprocessing'+'.'*10)
lidar = LEngine(lpath,cube,steps)
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

# Splitting data into train, val and test
# in (0.8,0.2,0.2) ratio
df = pd.read_pickle(gspath)

train_len = int(len(df)*0.8)
val_len = train_len + int(len(df)*0.2)
df = df.sample(frac=1).reset_index(drop=True) #Shuffling the df and reseting index

train_df = df[:train_len]
val_df = df[train_len:val_len]
test_df = df[val_len:]

train_df.to_pickle(os.path.join(data_dir,'train.pkl'))
val_df.to_pickle(os.path.join(data_dir,'val.pkl'))
test_df.to_pickle(os.path.join(data_dir,'test.pkl'))

print('Dataframe has been split into train, val and test')
print('*'*10+' Preprocessing Successfully Ended '+'*'*10)
