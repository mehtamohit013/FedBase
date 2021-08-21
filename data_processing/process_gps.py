import os
import pandas as pd
import scipy.io as io
import multiprocessing as mp

import tqdm

class GEngine():
    def __init__(self,gpath,matpath) -> None:
        self.gpath = gpath
        self.matpath = matpath
        os.makedirs(self.matpath,exist_ok=True)
    
    def concat_df(self):
        sample = pd.read_pickle(os.path.join(self.gpath,os.listdir(self.gpath)[0]))
        gps = pd.DataFrame(columns=sample.columns)
        for filename in os.listdir(self.gpath):
            tmp = pd.read_pickle(os.path.join(self.gpath,filename))
            gps = pd.concat([gps,tmp])

        gps = gps.reset_index()
        del gps['index']
        return gps


    def create_mat(self,ind):
        filename = self.gps.at[ind,'Lidar'][:-3]+'mat'
        filename = os.path.join(self.matpath,filename)
        io.savemat(
            filename,
            dict(
                gps=self.gps.at[ind,'GPS'],
                car_model = self.gps.at[ind,'Model'],
                car_name = self.gps.at[ind,'Name']
            )
        )

    def __call__(self,spath) -> None:
        self.gps = self.concat_df()
        self.gps.to_pickle(spath)

        print(f'Forming .mat files')

        with mp.Pool() as p:
            for _ in tqdm.tqdm(p.imap_unordered(self.create_mat,self.gps.index.values),total = len(self.gps.index.values)):
                pass

