import pandas as pd
import os
import tqdm

HOME = os.environ['HOME']

lpath = f'{HOME}/webots_code/data/chicago_ml/lidar_samples'
gpath = f'{HOME}/webots_code/data/chicago_ml/gps.pkl'
# tpath = f'{HOME}/webots_code/data//tracking'
labpath = f'{HOME}/webots_code/data/chicago_ml/labels'

gps_pd = pd.read_pickle(gpath)

rm = list()
for i in gps_pd.index.values:
    name = gps_pd.at[i,'Lidar'][:-3]+'mat'
    if not(name in os.listdir(labpath)):
        rm.append(i)

print(len(gps_pd),len(rm))

gps_pd = gps_pd.drop(index = rm).reset_index()

gps_pd.to_pickle(gpath)
