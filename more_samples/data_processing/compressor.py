import numpy as np
import multiprocessing as mp
import os
import tqdm

HOME = os.environ['HOME']
dpath = f'{HOME}/webots_code/data/final/lidar_samples'
spath = f'{HOME}/webots_code/data/final/lidar_compressed'
os.makedirs(spath,exist_ok=True)

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

if __name__=='__main__':
    files = os.listdir(dpath)
    print(len(files))
    pool = mp.Pool()
    for _ in tqdm.tqdm(pool.imap_unordered(data_compress,files), total=len(files)):
        pass
    # pool.join()
    pool.close()
