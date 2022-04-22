import pytorch_lightning as pl
import torch
from torch import nn

from models import *
from utilities import *

class gps_trainer(pl.LightningModule):
    def __init__(self,learning_rate = 1e-3,
                BATCH_SIZE:int = 64,
                num_BS:int = 3):

        super().__init__()
        self.model = GPS()

        self.celoss = nn.CrossEntropyLoss()
        self.lr = learning_rate
        self.batch_size = BATCH_SIZE
        self.num_BS = num_BS

        self.train_acc = 0
        self.val_acc = 0
        self.test_acc = 0
    
    def forward(self,gps,BS):
        
        out = self.model(gps)

        return out
    
    def training_step(self,batch,batch_idx):
        gps = batch['gps'].float()
        BS = batch['BS'].float()
        label = batch['label'].long()
        
        yhat = self(gps,BS)
        
        loss = self.celoss(yhat,label)
        
        self.log('Train Loss',loss)
        
        return {'loss':loss,'pred':yhat.cpu().detach(),'label':label.cpu().detach()}
    
    def configure_optimizers(self):
        opt = torch.optim.Adam(self.parameters(),self.lr)
        return opt
    
    def training_epoch_end(self,train_out):        
        len_out = len(train_out)
        y_pred = torch.Tensor(len_out*self.batch_size,self.num_BS)
        y_true = torch.Tensor(len_out*self.batch_size)

        for i in range(0,len_out):
            y_pred[i*self.batch_size:(i+1)*self.batch_size,:] = train_out[i]['pred'] 
            y_true[i*self.batch_size:(i+1)*self.batch_size] = train_out[i]['label']

        # Calculating Avg loss
        avg_loss = torch.stack([x['loss'] for x in train_out]).mean()

        top1 = top_k_acc(y_true,y_pred,k=1)
        self.train_acc = top1

        self.logger.experiment.add_scalar('Loss-Train per epoch',avg_loss,self.current_epoch)
        self.logger.experiment.add_scalar('Train Accuracy',top1,self.current_epoch)

        print(f'Train accuracies is {top1}')

    def validation_step(self,batch,batch_idx):
        gps = batch['gps'].float()
        BS = batch['BS'].float()
        label = batch['label'].long()
        
        yhat = self.forward(gps,BS)
        
        return [yhat.cpu().detach(),label.cpu().detach()]
     
    def validation_epoch_end(self,val_out):
        len_out = len(val_out)
        y_pred = torch.Tensor(len_out*self.batch_size,self.num_BS)
        y_true = torch.Tensor(len_out*self.batch_size)

        for i in range(0,len_out):
            y_pred[i*self.batch_size:(i+1)*self.batch_size,:] = val_out[i][0] 
            y_true[i*self.batch_size:(i+1)*self.batch_size] = val_out[i][1] 

        top1 = top_k_acc(y_true,y_pred,k=1)
        self.val_acc = top1

        self.logger.experiment.add_scalar('Validation Accuracy',top1,self.current_epoch)

        print(f'Validation accuracy is {top1}')
    
    def test_step(self,batch,batch_idx):
        gps = batch['gps'].float()
        BS = batch['BS'].float()
        label = batch['label'].long()
        
        yhat = self.forward(gps,BS)
        
        return [yhat.cpu().detach(),label.cpu().detach()]
     
    def test_epoch_end(self,val_out):
        len_out = len(val_out)
        y_pred = torch.Tensor(len_out*self.batch_size,self.num_BS)
        y_true = torch.Tensor(len_out*self.batch_size)

        for i in range(0,len_out):
            y_pred[i*self.batch_size:(i+1)*self.batch_size,:] = val_out[i][0] 
            y_true[i*self.batch_size:(i+1)*self.batch_size] = val_out[i][1] 

        top1 = top_k_acc(y_true,y_pred,k=1)
        self.test_acc = top1

        self.logger.experiment.add_hparams(
            {
                'LR' : self.lr,
                'overall params' : sum(p.numel() for p in self.model.parameters())
            },
            {
                'hparam/test_acc' : self.test_acc,
                'hparam/train_acc' : self.train_acc,
                'hparam/val_acc' : self.val_acc
            }
        )

        print(f'Test accuracy is {top1}')

#LiDAR Trainer
class lidar_trainer(pl.LightningModule):
    def __init__(self,
                 drop_prob:float = 0.3,
                 drop_prob_fc:float = 0.2,
                 learning_rate:float = 3.63e-4,
                 weight_decay:float = 1e-4,
                 BATCH_SIZE:int = 64,
                 num_BS:int = 3):
        
        super().__init__()
        
        self.drp = drop_prob
        self.drp_fc = drop_prob_fc
        self.batch_size = BATCH_SIZE
        self.num_BS = num_BS
        
        self.model = lidar(drp=drop_prob,drp_fc = drop_prob_fc)

        self.celoss = nn.CrossEntropyLoss()
        self.lr = learning_rate
        self.wd = weight_decay

        self.train_acc = 0
        self.val_acc = 0
        self.test_acc = 0

        self.example_input_array = torch.rand(1,10,240,240) # For logging graph
    
    def forward(self,lidar):
        out = self.model(lidar)
        return out
    
    def training_step(self,batch,batch_idx):
        lidar = batch['lidar'].float()
        label = batch['label'].long()
        
        yhat = self(lidar)
        
        loss = self.celoss(yhat,label)
        
        self.log('Train Loss',loss)
        
        return {'loss':loss,'pred':yhat.cpu().detach(),'label':label.cpu().detach()}
    
    def configure_optimizers(self):
        opt = torch.optim.Adam(self.parameters(),self.lr,
                               weight_decay=self.wd)
        return opt
    
    def training_epoch_end(self,train_out):        
        len_out = len(train_out)
        y_pred = torch.Tensor(len_out*self.batch_size,self.num_BS)
        y_true = torch.Tensor(len_out*self.batch_size)

        for i in range(0,len_out):
            y_pred[i*self.batch_size:(i+1)*self.batch_size,:] = train_out[i]['pred'] 
            y_true[i*self.batch_size:(i+1)*self.batch_size] = train_out[i]['label']

        top1 = top_k_acc(y_true,y_pred,k=1)

        # Calculating Avg loss
        avg_loss = torch.stack([x['loss'] for x in train_out]).mean()
        
        self.logger.experiment.add_scalar('Loss-Train per epoch',avg_loss,self.current_epoch)
        self.logger.experiment.add_scalar('Train Accuracy',top1,self.current_epoch)

        self.train_acc = top1
        
        print(f'Train accuracies is {top1}')

    def validation_step(self,batch,batch_idx):
        lidar = batch['lidar'].float()
        label = batch['label'].long()
        
        yhat = self.forward(lidar)
        
        return [yhat.cpu().detach(),label.cpu().detach()]
     
    def validation_epoch_end(self,val_out):
        len_out = len(val_out)
        y_pred = torch.Tensor(len_out*self.batch_size,self.num_BS)
        y_true = torch.Tensor(len_out*self.batch_size)

        for i in range(0,len_out):
            y_pred[i*self.batch_size:(i+1)*self.batch_size,:] = val_out[i][0] 
            y_true[i*self.batch_size:(i+1)*self.batch_size] = val_out[i][1] 

        top1 = top_k_acc(y_true,y_pred,k=1)
        self.val_acc = top1

        self.logger.experiment.add_scalar('Validation Accuracy',top1,self.current_epoch)

        print(f'Validation accuracy is {top1}')
    
    def test_step(self,batch,batch_idx):
        lidar = batch['lidar'].float()
        label = batch['label'].long()
        
        yhat = self.forward(lidar)
        
        return [yhat.cpu().detach(),label.cpu().detach()]
     
    def test_epoch_end(self,val_out):
        len_out = len(val_out)
        y_pred = torch.Tensor(len_out*self.batch_size,self.num_BS)
        y_true = torch.Tensor(len_out*self.batch_size)

        for i in range(0,len_out):
            y_pred[i*self.batch_size:(i+1)*self.batch_size,:] = val_out[i][0] 
            y_true[i*self.batch_size:(i+1)*self.batch_size] = val_out[i][1] 

        top1 = top_k_acc(y_true,y_pred,k=1)
        self.test_acc = top1

        self.logger.experiment.add_hparams(
            {
                'LR' : self.lr,
                'weight_decay' : self.wd,
                'drop_prob' : self.drp,
                'drop_fc' : self.drp_fc,
                'overall params' : sum(p.numel() for p in self.model.parameters())
            },
            {
                'hparam/test_acc' : self.test_acc,
                'hparam/train_acc' : self.train_acc,
                'hparam/val_acc' : self.val_acc
            }
        )
        print(f'Test accuracy is {top1}')

