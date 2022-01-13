import gym
import numpy as np
import pandas as pd
import scipy.io as io

class BS_env(gym.Env):
    def __init__(self,ep:list,dpath:str,ds:str='train'):
        
        '''
        ep: Pass the number of episodes to run: [start,end] where end is inclusive 
        dpath: Data path 
        ds: Dataset type: 'train','val' and 'test'
        '''
        super().__init__()
        self.dpath = dpath
        self.len = ep[1]
        self.curr = ep[0]
        self.reward_range = [-120,0]
        
        if ds == 'train':
            self.df = pd.read_pickle(self.dpath+'/train.pkl')
        elif ds == 'val':
            self.df = pd.read_pickle(self.dpath+'/val.pkl')
        else:
            self.df = pd.read_pickle(self.dpath+'/test.pkl')
        
        self.df = self.df.reset_index()
        
        #Observation Space: Lidar : [10,240,240]
        self.observation_space = gym.spaces.Box(
                                low = -10.0,
                                high = 10.0,
                                shape = (10,240,240),
                                dtype = np.float32
                                )
        
        # Action Space : Discrete : 0,1,2 -> Base station
        self.action_space = gym.spaces.Discrete(3)
        
        # Init the env and resetting it
        self.reset()
    
    def reset(self):
        self._state = np.zeros((10,240,240))
        self.curr = 0
    
    def step(self, action):
        
        '''
        Inp : Action Space
        Output : Next State , Reward, done, info
        '''
        label = io.loadmat(self.dpath+'/labels/'+self.df.at[self.curr,'Lidar'][:-3]+'mat')
        label = (np.array([label['ss'][0][0],
                                   label['ss'][1][0],
                                   label['ss'][2][0]]))
        self.state = np.load(self.dpath+'/lidar_compressed/'+self.df.at[self.curr,'Lidar'])['lidar']

        '''
        Reward Calculation
        Currently using power as reward
        '''
        reward = label[action]
#         print(type(reward))
        
        if reward <= -120.0 :
            reward = np.float64(-120.0)
        
        self.curr +=1
        
        if self.curr>=self.len:
            done=1
        else:
            done = 0
            
        info = [action,label]
        return self.state, reward, done, info
