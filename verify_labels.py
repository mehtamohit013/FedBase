import pandas as pd
import os
import tqdm

HOME = os.environ['HOME']

#lpath = f'{HOME}/webots_code/data/chicago_ml/lidar_samples'
gpath = f'{HOME}/webots_code/data/data/train.pkl'
# tpath = f'{HOME}/webots_code/data//tracking'
labpath = f'{HOME}/webots_code/data/data'

gps_pd = pd.read_pickle(gpath)

rm = list()
for i in tqdm.tqdm(gps_pd.index.values):
    tmp = os.path.join(labpath,gps_pd.at[i,'Folder'],'labels')
    name = gps_pd.at[i,'Lidar'][:-3]+'mat'
    if not(name in os.listdir(tmp)):
        rm.append(i)

print(len(gps_pd),len(rm))

gps_pd = gps_pd.drop(index = rm).reset_index()

gps_pd.to_pickle(gpath)
