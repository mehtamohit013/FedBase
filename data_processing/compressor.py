from data_processing.process_data import HOME
import numpy as np
import multiprocessing as mp
import os
import tqdm

dpath = f'{HOME}/webots_code/data/final_data/lidar_samples'
spath = f'{HOME}/webots_code/data/final_data/lidar_compressed'

def data_compress(filename):    
    data = dict(np.load(os.path.join(dpath,filename)))
    np.savez_compressed(
        os.path.join(spath,filename),
        lidar = data['lidar'],
        translation = data['translation'],
        rotation = data['rotation'],
        sites = data['sites'],
        data_pp = data['data_pp']
    )

if __name__=='main':
    HOME = os.environ['HOME']
    files = os.listdir(dpath)

    pool = mp.Pool()
    for _ in tqdm.tqdm(pool.imap_unordered(data_compress,files), total=len(files)):
        pass
