import os
from typing import Union 
import pandas as pd
import scipy.io as io
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import math

HOME = os.environ['HOME']

class OSMEngine():
    def __init__(self,gspath:str,tpath:str,
                opath:str,timestep:float,mpath:str=f'{HOME}/webots_code/comms_lidar_ML/map.osm',
                add_curr:bool=False) -> None:
        self.gspath = gspath
        self.gps = pd.read_pickle(self.gspath)
        self.tpath = tpath
        self.add_curr = add_curr
        self.opath = opath
        self.timestep = timestep
        self.conv_gis = (1e-5)/1.1

        # Vehicle Details
        self.width_cars = {
            'BMW X5': 2.00,
            'Citroen C-Zero': 1.6,
            'Toyota Prius': 1.95,
            'Lincoln MKZ': 1.95,
            'Range Rover SVR': 2.00,
            'Tesla model 3': 1.95,
            'Mercedes-Benz Sprinter': 2.00,
        }
        self.height_cars = {
            'BMW X5': 1.8,
            'Citroen C-Zero': 1.7,
            'Toyota Prius': 1.7,
            'Lincoln MKZ': 1.57,
            'Range Rover SVR': 1.7,
            'Tesla model 3': 1.5,
            'Mercedes-Benz Sprinter': 2.7,
        }

        #Beautiful Soup Object of map
        self.map_bs = bs(open(mpath),'xml')


    def get_coord(self,gps:list,model:str,conv_gis:float) -> Union[list,list]:
        '''
        Get all the four corners of a car, based on simple box
        based geometry
        '''

        x2,y2,_ = gps[0] #Front GPS coord
        x1,y1,_ = gps[1] #Center GPS coord
        x3,y3,_ = gps[2] #Rear GPS coord

        a  = float(self.width_cars[model])/float(2.00) 
        
        #Default range is [-pi/2,pi/2]
        theta = math.atan((y2-y1)/(x2-x1))
        
        if theta<0:
            theta += math.pi
        
        lat = [x2 - a*conv_gis*math.sin(theta),
            x2 + a*conv_gis*math.sin(theta),
            x3 + a*conv_gis*math.sin(theta),
            x3 - a*conv_gis*math.sin(theta)]
        
        lon = [y2 + a*conv_gis*math.cos(theta),
            y2 - a*conv_gis*math.cos(theta),
            y3 - a*conv_gis*math.cos(theta),
            y3 + a*conv_gis*math.cos(theta)]
        
        return lat,lon

    
    def add_vehicle(self,y:bs,
                lat:list,lon:list,
                height:float) -> bs:
    
        '''
        Add a vehicle disguised as building, bounded by 
        rectangle corners defined by lat and lon and height & width
        defined according to vehicle type
        '''
        # Retreiving last node number and way number
        node_num = int(y.osm.find_all("node")[-1]['id'])
        way_num = int(y.osm.find_all("way")[-1]['id'])

        # Construct the corner nodes and add after last node
        y.osm.find('node',{'id':str(node_num)}).insert_after(y.new_tag("node",id=str(node_num+1),
                                                            visible="true",version='1',
                                                            lat=f'{lat[0]:.8f}',lon=f'{lon[0]:.8f}'))
        y.osm.find('node',{'id':str(node_num+1)}).insert_after(y.new_tag("node",id=str(node_num+2),
                                                                visible="true",version='1',
                                                                lat=f'{lat[1]:.8f}',lon=f'{lon[1]:.8f}'))
        y.osm.find('node',{'id':str(node_num+2)}).insert_after(y.new_tag("node",id=str(node_num+3),
                                                                visible="true",version='1',
                                                                lat=f'{lat[2]:.8f}',lon=f'{lon[2]:.8f}'))
        y.osm.find('node',{'id':str(node_num+3)}).insert_after(y.new_tag("node",id=str(node_num+4),
                                                                visible="true",version='1',
                                                                lat=f'{lat[3]:.8f}',lon=f'{lon[3]:.8f}'))
        
        # Construct way (building) using the nodes above
        way_tag = y.new_tag("way",id=str(way_num+1),version='1',visible="true")
        way_tag.append(y.new_tag('nd',ref=str(node_num+1)))
        way_tag.append(y.new_tag('nd',ref=str(node_num+2)))
        way_tag.append(y.new_tag('nd',ref=str(node_num+3)))
        way_tag.append(y.new_tag('nd',ref=str(node_num+4)))
        way_tag.append(y.new_tag('nd',ref=str(node_num+1)))
        way_tag.append(y.new_tag('tag',k="height",v=f'{height}'))
        way_tag.append(y.new_tag('tag',k="building",v="apartments"))
        way_com = Comment('Way Tag inserted here') # A comment for reference
        y.osm.find('way',{'id':str(way_num)}).insert_after(way_com,way_tag)

        return y

    def save_osm(self,y:bs,osm_path:str,filename:str):
        with open(os.path.join(osm_path,filename),'w') as f:
            f.write(y.prettify()) 

    def construct_osm(self,siml_time:float,car_name:str,filename:str):
        
        '''
        Construct OSM file for each sample collected 
        filename : *.mat
        '''

        y=self.map_bs

        if not(filename in os.listdir(self.opath)):

            for count,tfile in enumerate(os.listdir(self.tpath)):
                
                gps_pd = pd.read_feather(os.path.join(self.tpath,tfile))
                
                if (tfile == (f'gps_pd_'+ car_name + '.feather')) and not(self.add_curr):
                    continue
                    
                entry = gps_pd[
                                ((siml_time - self.timestep) < gps_pd['Time']) &
                                (gps_pd['Time'] <= siml_time)
                                ]
                
                # Check whether the vechile exist for
                # curr timestep
                if entry.empty :
                    continue
                
                gps_data = entry['gps'].values[0]
                model = entry['model'].values[0]

                lat,lon = self.get_coord(gps_data,model,self.conv_gis)

                y = self.add_vehicle(y,lat,lon,self.height_cars[model])

            self.save_osm(y,self.opath,filename)

    def __call__(self,index:int) -> None:
        self.construct_osm(
            self.gps.at[index,'Time'],
            self.gps.at[index,'Name'],
            self.gps.at[index,'Lidar'][:-3]+'osm'
        )
    

