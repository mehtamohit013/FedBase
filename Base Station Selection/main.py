# Imports
import torch

import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import random
import getpass
import argparse
from lxml import etree as et

import pytorch_lightning as pl
from pytorch_lightning.loggers import TensorBoardLogger

from utilities import *
from dataset import *
from models import *
from lightning import * 
from federated import *


# Setting Seed
seed = 0

random.seed(seed)
torch.manual_seed(seed)
np.random.seed(seed)
pl.seed_everything(seed)


# Using deterministic training
torch.backends.cudnn.deterministic = True


# Data Path
user = getpass.getuser()

# if user == 'root':  #For google colab
#     data_dir = '.'
#     save_dir = './model_state_dict'
# elif user == 'mohit':
#     data_dir = os.environ['HOME'] + '/webots_code/data'
#     save_dir = os.path.join(os.environ['HOME'],'webots_code/model_state_dict')
# elif user == 'iiti':
#     data_dir = os.environ['HOME'] + '/webots_code/comms_lidar_ML/data'
#     save_dir = os.path.join(os.environ['HOME'],'webots_code/comms_lidar_ML/BS_Selection/model_state_dict')
# else:
#     print(f'User {user} not present.\n Exiting.....')
#     exit(0)

root = et.parse('/home/mohit/webots_code/comms_lidar_ML/config.xml').getroot()
data_dir = root[0].get('dpath')
save_dir = root[0].get('save_path')
log_dir = root[1].get('log_dir')

os.makedirs(save_dir,exist_ok=True)


#Reading data
train_gps = pd.read_pickle(os.path.join(data_dir,'train.pkl')).reset_index(drop=True)
val_gps = pd.read_pickle(os.path.join(data_dir,'val.pkl')).reset_index(drop=True)
test_gps = pd.read_pickle(os.path.join(data_dir,'test.pkl')).reset_index(drop=True)

len_train = len(train_gps)
len_val = len(val_gps)
len_test = len(test_gps)


lpath = os.path.join(data_dir,'lidar_compressed')
labpath = os.path.join(data_dir,'labels')



BS = np.array([
    [38.89502,-77.07303,5],
    [38.89442,-77.07294,5],
    [38.89452,-77.07358,5]
])
num_BS = int(BS.shape[0])


# HyperParams
BATCH_SIZE = 64

if (user=='root'):
    n_worker = 2
else:
    n_worker = 8

# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
device = torch.device('cpu')
# print(device)

#Dataset
train_dataset = bs_dataset(train_gps,lpath,labpath)
val_dataset = bs_dataset(val_gps,lpath,labpath)
test_dataset = bs_dataset(test_gps,lpath,labpath)

#Dataloader
train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    pin_memory=True,
    num_workers = n_worker,
    drop_last = True,
    shuffle = True
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    pin_memory=True,
    num_workers = n_worker,
    drop_last = True
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    pin_memory=True,
    num_workers = n_worker,
    drop_last = True
)

gps_model = gps_trainer(learning_rate = 1e-3,
                        BATCH_SIZE = BATCH_SIZE,
                        num_BS = num_BS)

logger = TensorBoardLogger(log_dir, name="GPS",log_graph=True,default_hp_metric=False)
gps_pl_trainer = pl.Trainer(
                    gpus=0,
                    max_epochs = 20,
                    logger = logger,
                    deterministic = True,
                    auto_lr_find = False
                     )

# gps_pl_trainer.tune(gps_model,train_loader,val_loader)
gps_pl_trainer.fit(gps_model,train_loader,val_loader)
gps_pl_trainer.test(gps_model,test_loader)

#Lidar
lidar_model = lidar_trainer(drop_prob=0.3,drop_prob_fc=0.2,
                            weight_decay=1e-4,learning_rate=3.63e-4,
                            BATCH_SIZE=BATCH_SIZE, num_BS=num_BS)

logger = TensorBoardLogger(log_dir, name="lidar",log_graph=True,default_hp_metric=False)
lidar_pl_trainer = pl.Trainer(
                     gpus=0,
                     max_epochs = 20,
                     precision = 16,
                     logger = logger,
                     amp_backend = 'native',
                     deterministic = True,
                     auto_lr_find = False
                     )

# lidar_pl_trainer.tune(lidar_model,train_loader,val_loader)
lidar_pl_trainer.fit(lidar_model,train_loader,val_loader)
lidar_pl_trainer.test(lidar_model,test_loader)

y_pred = list()
pos = 0
ovr = 0 
for i in tqdm.tqdm(range(0,len_train),desc='Training Shortest dist'):
    data = train_dataset[i]
    dist1 = dist_gps(data['gps'],data['BS'][:3])
    dist2 = dist_gps(data['gps'],data['BS'][3:6])
    dist3 = dist_gps(data['gps'],data['BS'][6:9])

    # print(dist1,dist2,dist3)
    
    index = np.argmax(np.array([dist1,dist2,dist3]))

    # print(index,data['label'])

    if index == data['label']:
        pos+=1
    ovr+=1
    # if((i+1)%10==0):
    #     break
print(f'Accuracy based on shortest distance on train is {pos/ovr}')


y_pred = list()
pos = 0
ovr = 0 
for i in tqdm.tqdm(range(0,len_val),desc='Validation Shortest Dist'):
    data = val_dataset[i]
    dist1 = dist_gps(data['gps'],data['BS'][:3])
    dist2 = dist_gps(data['gps'],data['BS'][3:6])
    dist3 = dist_gps(data['gps'],data['BS'][6:9])

    # print(dist1,dist2,dist3)
    
    index = np.argmax(np.array([dist1,dist2,dist3]))

    # print(index,data['label'])

    if index == data['label']:
        pos+=1
    ovr+=1
    # if((i+1)%10==0):
    #     break
print(f'Accuracy based on shortest distance on val is {pos/ovr}')


# Federarted Learning

# Hyper Params
epoch_round = 2 # Number of epochs per dataset
cm_rounds = 10 #Overall communication round

torch.backends.cudnn.deterministic = True
# torch.backends.cudnn.benchmark = True #Use only while training, not while deterministic 

# Available option : 'mean','wmean'
agg = 'mean' 
# Possible model_type: 'lg' : lidar + GPS,'l' : lidar,'g' : Gps 
model_type = 'l'

#Parameters
## Calculating number of cars

def cars_dist(data_pd:pd.DataFrame) -> list:
    car_list = list()
    car_sample = dict()
    for i in range(0,len_train):
        if not(data_pd.at[i,'Name'] in car_list):
            car_list.append(data_pd.at[i,'Name'])
            car_sample[int(data_pd.at[i,'Name'][-2:])] = list()
        car_sample[int(data_pd.at[i,'Name'][-2:])].append(i)

    return car_sample, car_list

train_car_sample,train_car_list = cars_dist(train_gps)

# plt.rcParams['figure.figsize'] = [18, 6]
# plt.rcParams['figure.dpi'] = 100 
# len_car = [len(train_car_sample[i]) for i in range(0,len(train_car_list))]
# plt.bar(range(0,len(train_car_list)),len_car)

## Dataset
cl_dataset = list()

for i in train_car_list:
    tmp = bs_dataset(train_gps[train_gps['Name']==i].reset_index(drop=True),lpath=lpath,label_path=labpath)
    cl_dataset.append(tmp)

#Dataloader
cl_loader = list()

for i in range(0,len(cl_dataset)):
    tmp = DataLoader(
        cl_dataset[i],
        batch_size=BATCH_SIZE,
        pin_memory=True,
        num_workers = n_worker,
        drop_last = True,
        shuffle = True
        )
    cl_loader.append(tmp)

# Training Federated learning        
federated = fed_server(len(train_car_list),
                        cl_dataset,cl_loader,
                        len_train, train_loader, val_loader,test_loader,
                        agg,model_type,
                        cm_rounds,epoch_round,
                        wd = 1e-4,lr = 1e-4,
                        BATCH_SIZE = BATCH_SIZE,
                        device = device)

federated.train()
federated.test()