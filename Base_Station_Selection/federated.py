import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

import time
import tqdm

from utilities import *
from models import *


#Client Side
class client():
    
    '''
    Currently using standard trainer to train the model 
    '''
    def __init__(self,model:nn.Module,
                loader:DataLoader,
                epoch:int = 2,
                model_type:str='l',
                BATCH_SIZE = 64,
                wd=1e-4,lr=1e-3,
                device:torch.device = torch.device('cpu')):
    
        self.model = model.to(device)
        self.loader = loader
        self.epoch = epoch
        self.model_type = model_type
        self.batch_size = BATCH_SIZE
        self.device = device

        self.lr = lr
        self.wd = wd
        self.celoss = nn.CrossEntropyLoss()
        self.opt = torch.optim.Adam(model.parameters(),self.lr,weight_decay=self.wd)
        self.start = time.time()

    def train(self):

        self.model.train()
        self.model.zero_grad()

        for i in range(0,self.epoch):

            # print('-'*10+f' Starting Epoch {i+1} '+'-'*10)
            
            running_loss = 0.0
            running_acc = 0.000
            
            for count,batch in enumerate(self.loader):

                self.opt.zero_grad()

                lidar = batch['lidar'].float().to(self.device)
                gps = batch['gps'].float().to(self.device)
                BS = batch['BS'].float().to(self.device)
                label = batch['label'].long().to(self.device)

                if self.model_type == 'lg':
                    yhat = self.model(lidar,gps,BS)
                elif self.model_type == 'l':
                    yhat = self.model(lidar)
                else:
                    yhat = self.model(gps,BS)
                
                loss = self.celoss(yhat,label)
                running_loss +=loss.item()
                
                loss.backward()
                self.opt.step()

                top1 = top_k_acc(label.cpu().detach(),yhat.cpu().detach(),k=1)
                running_acc = (running_acc*(count)*self.batch_size + top1*self.batch_size)/ ((count+1)*self.batch_size)

                # if count%1000 == 0 :
                #     print(f'Cross Entropy loss after {count} iterations is {running_loss/((count+1)*self.batch_size)}. '\
                #           f'Time Elapsed {time.time()-self.start}')
                #     print(f'Accuracy on train after {count} iteration is {running_acc}')
            
            # print(f'Overall iteration completed {count}') #304
            # print('-'*10+f' Epoch {i+1} ends '+'-'*10)
            # print(f'Cross Entropy loss after {i+1} epochs is {running_loss/((count+1)*self.batch_size)}'\
            #       f'Time Elapsed {time.time()-self.start}')
            # print(f'Accuracy on train after {i+1} epochs is {running_acc}')




#Global Server
class fed_server():
    def __init__(self,cars:int,
                cl_dataset,
                cl_loader,
                ovr_sample:int,
                val_loader:DataLoader,
                train_loader:DataLoader,
                test_loader:DataLoader,
                agg:str='mean',
                model_type:str='l',
                cm_rounds:int  = 10,
                epoch_rounds:int = 10,
                wd:float = 1e-4,lr:float=1e-4,
                BATCH_SIZE = 64,
                device:torch.device = torch.device('cpu')):
        
        self.cars = cars
        self.dataset = cl_dataset
        self.loader = cl_loader
        self.agg = agg
        self.model_type = model_type
        self.ovr_sample = ovr_sample
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.test_loader = test_loader
        self.cm_rounds = cm_rounds
        self.epochs = epoch_rounds
        self.lr = lr
        self.wd = wd
        self.batch_size = BATCH_SIZE
        self.device = device

        self.writer = SummaryWriter(log_dir =f'./tb_logs/federated/{self.model_type}',
                                    comment=self.model_type)

        self.celoss = nn.CrossEntropyLoss()

        self.create_model() #Global Model
    
    def create_model(self):
        if self.model_type == 'l':
            self.model = lidar(0.3,0.2).to(self.device)
            self.lr = 3.63e-4
            self.sample_input = torch.rand((2,10,240,240)).to(self.device)
        else:
            self.model = GPS().to(self.device)
            self.sample_input = [torch.rand((2,3)).to(self.device),torch.rand((2,9)).to(self.device)]

        self.writer.add_graph(self.model,self.sample_input)
    
    def per_round(self,epoch):

        #Synchronizing client model with global model at start of each round
        cl_model = [self.model for i in range(0,self.cars)]
        for cmodel in cl_model:
            cmodel.load_state_dict(self.model.state_dict())


        # Training Client Model
        for i in tqdm.tqdm(range(0,self.cars),desc='Cars'):
            # print('*'*3+f' Starting Client {i} ' +'*'*3)
            
            if not(len(self.loader[i])) :
                # print(f'Not enough samples for client {i}')
                cl_model[i].load_state_dict(self.model.state_dict())
                continue

            tmp = client(cl_model[i],self.loader[i],epoch,self.model_type,wd=self.wd,lr=self.lr,device = self.device)
            tmp.train()

        # Global aggregration
        global_dict = self.model.state_dict()

        for k in global_dict.keys():
            if self.agg == 'mean':
                
                global_dict[k] = torch.stack([cl_model[i].state_dict()[k].float() 
                                            for i in range(len(cl_model))], 0).mean(0)
            
            else:
                global_dict[k] = torch.sum(
                                        torch.stack([cl_model[i].state_dict()[k].float()*(float(len(self.dataset[i]))/float(self.ovr_sample)) 
                                        for i in range(len(cl_model))], 0),
                                        0)
        
        self.model.load_state_dict(global_dict)
        print('Global Aggregration Successfull')
    
    def train(self):

        for i in tqdm.tqdm(range(0,self.cm_rounds),desc='Rounds'):
            
            # print('-'*10+f' Staring round {i+1} '+ '-'*10)
            self.per_round(self.epochs)

            print('#'*3 + 'Train Accuracy '+ '#'*3)
            self.train_acc(i)
            
            print('#'*3 + 'Validation Accuracy '+ '#'*3)
            self.val(i)

    def train_acc(self,epoch:int):
        self.model.eval()
        running_loss = 0.0
        running_acc = 0.000
        running_loss = 0.0

        for count,batch in tqdm.tqdm(enumerate(self.train_loader),desc='Train Metrics',
                                         total=len(self.train_loader)):

            lidar = batch['lidar'].float().to(self.device)
            gps = batch['gps'].float().to(self.device)
            BS = batch['BS'].float().to(self.device)
            label = batch['label'].long().to(self.device)

            if self.model_type == 'lg':
                yhat = self.model(lidar,gps,BS)
            elif self.model_type == 'l':
                yhat = self.model(lidar)
            else:
                yhat = self.model(gps,BS)

            loss = self.celoss(yhat,label)
            running_loss += loss.item()
            top1 = top_k_acc(label.cpu().detach(),yhat.cpu().detach(),k=1)
            running_acc = (running_acc*(count)*self.batch_size + top1*self.batch_size)/ ((count+1)*self.batch_size)
        
        running_loss = running_loss/((count+1)*self.batch_size)
        self.writer.add_scalar('Train Acc',running_acc,epoch)
        self.writer.add_scalar('Avg Train Loss per round',running_loss,epoch)
        print(f'Accuracy on train is {running_acc}')
    
    def val(self,epoch:int):

        self.model.eval()
        running_loss = 0.0
        running_acc = 0.000

        for count,batch in tqdm.tqdm(enumerate(self.val_loader),desc='Val Metrics',
                                         total=len(self.val_loader)):

            lidar = batch['lidar'].float().to(self.device)
            gps = batch['gps'].float().to(self.device)
            BS = batch['BS'].float().to(self.device)
            label = batch['label'].long().to(self.device)

            if self.model_type == 'lg':
                yhat = self.model(lidar,gps,BS)
            elif self.model_type == 'l':
                yhat = self.model(lidar)
            else:
                yhat = self.model(gps,BS)

            top1 = top_k_acc(label.cpu().detach(),yhat.cpu().detach(),k=1)
            running_acc = (running_acc*(count)*self.batch_size + top1*self.batch_size)/ ((count+1)*self.batch_size)
        
        self.writer.add_scalar('Val Acc',running_acc,epoch)
        print(f'Accuracy on val is {running_acc}')
    
    def test(self):
        self.model.eval()
        running_loss = 0.0
        running_acc = 0.000

        for count,batch in tqdm.tqdm(enumerate(self.test_loader),desc='Test Metrics'):

            lidar = batch['lidar'].float().to(self.device)
            gps = batch['gps'].float().to(self.device)
            BS = batch['BS'].float().to(self.device)
            label = batch['label'].long().to(self.device)

            if self.model_type == 'lg':
                yhat = self.model(lidar,gps,BS)
            elif self.model_type == 'l':
                yhat = self.model(lidar)
            else:
                yhat = self.model(gps,BS)

            top1 = top_k_acc(label.cpu().detach(),yhat.cpu().detach(),k=1)
            running_acc = (running_acc*(count)*self.batch_size + top1*self.batch_size)/ ((count+1)*self.batch_size)
        
        self.writer.add_scalar('Test Acc',running_acc,0)
        print(f'Accuracy on Test is {running_acc}')

