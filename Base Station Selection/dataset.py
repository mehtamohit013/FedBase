import numpy as np
from torch.utils.data import Dataset
import pandas as pd
import scipy.io as io
import os

class bs_dataset(Dataset):
    def __init__(self,gps_pd:pd.DataFrame,
                lpath:str,label_path:str,
                num_BS:int = 3):
    
        self.gps = gps_pd
        self.lpath = lpath
        self.label_path = label_path
        self.num_BS = num_BS
        
    def __getitem__(self,index):
        filename = self.gps.at[index,'Lidar']
        sample = dict() 

        sample['lidar'] = dict(np.load(os.path.join(self.lpath,filename)))['lidar'] #[10,240,240]
        sample['lidar'] = sample['lidar'].astype('float32')
        sample['gps'] = np.array(self.gps.at[index,'GPS'])[1].astype('float32') # Central GPS coord
        sample['BS'] = self.gps.at[index,'BS'].reshape((3*self.num_BS,)).astype('float32') #[num_BS*3,]
        sample['label'] = io.loadmat(self.label_path+f'/{filename[:-3]}mat')['ss']
        
        
        #Return the index of maximum element 
        sample['label'] = np.argmax(sample['label'].astype('float32')) 
        
        return sample
    
    def __len__(self):
        return len(self.gps)
