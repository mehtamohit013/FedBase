import os
from typing import Union 
import pandas as pd
import scipy.io as io
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import math


# Vehicle Details
width_cars = {
    'BMW X5': 2.00,
    'Citroen C-Zero': 1.6,
    'Toyota Prius': 1.95,
    'Lincoln MKZ': 1.95,
    'Range Rover SVR': 2.00,
    'Tesla model 3': 1.95,
    'Mercedes-Benz Sprinter': 2.00,
}
height_cars = {
    'BMW X5': 1.8,
    'Citroen C-Zero': 1.7,
    'Toyota Prius': 1.7,
    'Lincoln MKZ': 1.57,
    'Range Rover SVR': 1.7,
    'Tesla model 3': 1.5,
    'Mercedes-Benz Sprinter': 2.7,
}

def add_vehicle(y:bs,
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

def get_coord(gps:list,model:str,conv_gis:float) -> Union[list,list]:
    '''
    Get all the four corners of a car, based on simple box
    based geometry
    '''

    x2,y2,_ = gps[0] #Front GPS coord
    x1,y1,_ = gps[1] #Center GPS coord
    x3,y3,_ = gps[2] #Rear GPS coord

    a  = float(width_cars[model])/float(2.00) 
    
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

def save_osm(y:bs,osm_path:str,filename:str):
    with open(os.path.join(osm_path,filename),'w') as f:
        f.write(y.prettify())

def construct_osm(dpath:str,gpath:str,
                filename:str,add_curr:bool,
                osm_path:str,
                osm_file:str='map.osm',
                timestep:float=0.128,
                conv_gis:float = (1e-5)/1.1):
    
    '''
    Construct OSM file for each sample collected 
    filename : *.mat
    '''
    y = bs(open(osm_file),'xml')
    data = io.loadmat(os.path.join(dpath,filename))

    for count,gfile in enumerate(os.listdir(gpath)):
        
        gps_pd = pd.read_pickle(os.path.join(gpath,gfile))
        
        if (gfile == (f'gps_pd_'+ data['car_name'][0] + '.xz')) and not(add_curr):
            continue
            
        entry = gps_pd[
                        ((data['siml_time'][0,0] - timestep) < gps_pd['timestep']) &
                        (gps_pd['timestep'] <= data['siml_time'][0,0])
                        ]
        
        # Check whether the vechile exist for
        # curr timestep
        if entry.empty :
            continue
        
        gps_data = entry['gps'].values[0]
        model = entry['model'].values[0]

        lat,lon = get_coord(gps_data,model,conv_gis)

        y = add_vehicle(y,lat,lon,height_cars[model])

    save_osm(y,osm_path,filename[:-3]+'osm')
        
    

