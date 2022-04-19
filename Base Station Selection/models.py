import torch
from torch import nn
from torch.nn import functional as F



#GPS Model
class GPS(nn.Module):
    def __init__(self):
        super().__init__()

        self.ln1 = nn.Linear(3,8)
        self.ln2 = nn.Linear(8,16)
        self.ln3 = nn.Linear(16,8)
        self.ln4 = nn.Linear(8,3)

    def forward(self,x):
        x = F.prelu(self.ln1(x),torch.tensor(0.25))
        x = F.prelu(self.ln2(x),torch.tensor(0.25))
        x = F.prelu(self.ln3(x),torch.tensor(0.25))
        out = (self.ln4(x))

        return out


# LiDAR Model

class lidar(nn.Module):
    def __init__(self,drp:float=0.3,
                 drp_fc:float=0.2):
        super().__init__()
        
        self.drop_CNN = nn.Dropout(drp)
        self.drop_fc = nn.Dropout(drp_fc)
        self.mpool = nn.MaxPool2d((2,2))
        self.channels = 5
        self.fchannel = 3
        self.conv1 = self.create_conv(10,self.channels,13)
        self.conv2 = self.create_conv(self.channels,self.channels,13)
        self.conv3 = self.create_conv(self.channels,self.channels,7)
        self.conv4 = self.create_conv(self.channels,self.channels,7)

        # 1st Inception block
        self.in1 = nn.Sequential(
            self.create_conv(self.channels,self.fchannel,1),
            self.create_conv(self.fchannel,self.fchannel,3),
            self.create_conv(self.fchannel,self.fchannel,3)
        )
        self.in2 = nn.Sequential(
            self.create_conv(self.channels,self.fchannel,1),
            self.create_conv(self.fchannel,self.fchannel,3)
        )
        self.in3 = nn.Sequential(
            nn.MaxPool2d((3,3)),
            self.create_conv(self.channels,self.fchannel,1)
        )
        self.in4 = self.create_conv(self.channels,self.fchannel,1)

        # Second inception block
        self.in5 = nn.Sequential(
            self.create_conv(self.fchannel*4,self.fchannel,1),
            self.create_conv(self.fchannel,self.fchannel,3),
            self.create_conv(self.fchannel,self.fchannel,3)
        )
        self.in6 = nn.Sequential(
            self.create_conv(self.fchannel*4,self.fchannel,1),
            self.create_conv(self.fchannel,self.fchannel,3)
        )
        self.in7 = nn.Sequential(
            nn.MaxPool2d((3,3)),
            self.create_conv(self.fchannel*4,self.fchannel,1)
        )
        self.in8 = self.create_conv(self.fchannel*4,self.fchannel,1)

        self.conv5 = self.create_conv(self.fchannel*4,self.fchannel,7)
        self.conv6 = self.create_conv(self.fchannel,self.fchannel,7)

        self.conv7 = self.create_conv(self.fchannel,self.fchannel,3)
        self.conv8 = self.create_conv(self.fchannel,self.fchannel,3)
        
        self.flatten = nn.Flatten()
        self.linear = nn.Sequential(
            nn.Linear(588,16),
            nn.PReLU(1),
            nn.BatchNorm1d(16),
            nn.Linear(16,3)
        )

    
    def forward(self,X):
        X  = self.conv1(X)
        X  = self.conv2(X)
        X = self.mpool(X)

        X = self.conv3(X)
        X = self.conv4(X)
        X = self.mpool(X)

        X = self.drop_CNN(X)

        a = self.in1(X)
        a = F.pad(a,[2,2,2,2])
        b = self.in2(X)
        b = F.pad(b,[1,1,1,1])
        c = self.in3(X)
        c = F.pad(c,[16,16,16,16])
        d = self.in4(X)

        X = torch.cat((a,b,c,d),1)

        X = self.drop_CNN(X)

        a = self.in5(X)
        a = F.pad(a,[2,2,2,2])
        b = self.in6(X)
        b = F.pad(b,[1,1,1,1])
        c = self.in7(X)
        c = F.pad(c,[16,16,16,16])
        d = self.in8(X)

        X = torch.cat((a,b,c,d),1)
        X = self.drop_CNN(X)

        X = self.conv5(X)
        X = self.conv6(X)

        X = self.mpool(X)

        X = self.drop_CNN(X)

        X = self.conv7(X)
        X = self.conv8(X)

        X = self.flatten(X)
        out = self.linear(X)

        return out
    
    def create_conv(self,in_layers:int,out_layers:int,kernel,stride:int=1,
                    padding:int=0) -> nn.Module :

        return nn.Sequential(
            nn.Conv2d(in_layers,out_layers,kernel,stride,padding),
            nn.PReLU(out_layers),
            nn.BatchNorm2d(out_layers)
        )
