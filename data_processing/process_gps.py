import os
import pandas as pd

def concat_df(dpath:str):
    sample = pd.read_pickle(os.path.join(dpath,os.listdir(dpath)[0]))
    gps = pd.DataFrame(columns=sample.columns)
    for filename in os.listdir(dpath):
        tmp = pd.read_pickle(os.path.join(dpath,filename))
        gps = pd.concat([gps,tmp])

    gps = gps.reset_index()
    del gps['index']
    return gps

class GEngine():
    def __init__(self,dpath) -> None:
        self.dpath = dpath
    
    def __call__(self,spath) -> None:
        gps = concat_df(self.dpath)
        gps.to_pickle(spath)

