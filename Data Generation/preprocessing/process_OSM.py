import os
from typing import Union
import pandas as pd
from lxml import etree as et
import math

HOME = os.environ['HOME']

class OSMEngine():
    def __init__(self,gspath:str,tpath:str,
                opath:str,timestep:float,mpath:str=f'{HOME}/webots_code/comms_lidar_ML/map.osm',
                add_curr:bool=False) -> None:
        self.gspath = gspath
        self.gps = pd.read_pickle(self.gspath)
        self.tpath = tpath
        self.mpath = mpath
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

    
    # Creating a single node at particular latitude and longitude
    def create_node(self,ind:int,lat:float,lon:float) -> et._Element:
        return et.Element(
            'node',
            id=str(ind),
            visible = 'true',
            version = '1',
            lat=f'{lat:.8f}',
            lon=f'{lon:.8f}'
        )
           
    # Creating way points
    def create_way(self,ind:int,node_id:list,veh_height:float):
        
        elem = et.Element('way',id=str(ind),version='1',visible='true')
        for i in range(0,len(node_id)):
            et.SubElement(
                elem,
                'nd',
                ref=str(node_id[i])
            )
        et.SubElement(elem,'nd',ref=str(node_id[0]))
        et.SubElement(elem,'tag',k="height",v=f'{veh_height}')
        et.SubElement(elem,'tag',k="building",v="apartments")

        return elem

    def add_vehicle(self,root:et._Element,lat:list,lon:list,model:str):
    
        '''
        Add a vehicle disguised as building, bounded by 
        rectangle corners defined by lat and lon and height & width
        defined according to vehicle type
        '''

        height  = self.height_cars[model]

        # Retreiving last node pos and id 
        last_node = root.findall('node')[-1]
        node_pos = root.index(last_node)
        node_id = int(last_node.get('id'))

        root.insert(node_pos+1,self.create_node(node_id+1,lat[0],lon[0]))
        root.insert(node_pos+2,self.create_node(node_id+2,lat[1],lon[1]))
        root.insert(node_pos+3,self.create_node(node_id+3,lat[2],lon[2]))
        root.insert(node_pos+4,self.create_node(node_id+4,lat[3],lon[3]))

        # Retreiving last way pos and id
        last_way = root.findall('way')[-1]
        way_pos = root.index(last_way)
        way_id = int(last_way.get('id'))

        #Constructing and appending way
        root.insert(way_pos+1,self.create_way(way_id+1,
                    [node_id+1,node_id+2,node_id+3,node_id+4],
                    height))

    def save_osm(self,tree:et._ElementTree,filename:str):
        tree.write(
            os.path.join(self.opath,filename),
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8"
        )

    def construct_osm(self,siml_time:float,car_name:str,filename:str):
        
        '''
        Construct OSM file for each sample collected 
        filename : *.mat
        '''
        root = et.parse(self.mpath).getroot()

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

                self.add_vehicle(root,lat,lon,model)

            self.save_osm(et.ElementTree(root),filename)

    def __call__(self,index:int) -> None:
        self.construct_osm(
            self.gps.at[index,'Time'],
            self.gps.at[index,'Name'],
            self.gps.at[index,'Lidar'][:-3]+'osm'
        )
    

