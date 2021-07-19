# Steps to Construct .wbt from .osm 
```bash
python $WEBOTS_HOME/resources/osm_importer/importer.py --input=map.osm --output=webots.wbt
```

Use ```--extract-projection``` option to extract the projection script used

Default projection : ```+proj=utm +north +zone=18 +lon_0=-77.074875 +lat_0=38.894830 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs```

# Setup for using SUMO from webots
1. ```unset $SUMO_HOME```
2. Remove SUMO bin from LD_LIBRARY_PATH
3. Add webots sumo path 
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$WEBOTS_HOME/projects/default/resources/sumo/bin:$WEBOTS_HOME/lib
```
4. SUMO bin is located at :
    ```$WEBOTS_HOME/projects/default/resources/sumo/bin```


# Steps to construct SUMO files
 
### 1. Download the corresponding osm file from openstreetmaps using the export functionality 

Warning : Dont use the [exporter.py]($WEBOTS_HOME/resources/sumo_exporter/exporter.py) to construct nodes and edg xml files, as the files will be constructed without projection i.e. devoid of lat and lon


### 2. Use either osmBuild.py or netconvert using osm.sumocfg fle to convert the osm file to the corresponding .net.xml according to the parameters set in .netcfg

sample netcfg : 
```xml
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/netconvertConfiguration.xsd">

    <input>
        <osm-files value="map.osm"/>
    </input>

    <output>
        <output-file value="osm.net.xml"/>
        <output.street-names value="true"/>
        <output.original-names value="true"/>
    </output>

    <processing>
        <geometry.remove value="true"/>
        <roundabouts.guess value="true"/>
    </processing>

    <projection>
        <proj value="+proj=utm +north +zone=18 +lon_0=-77.074875 +lat_0=38.894830 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"/>
    </projection>
    
    <tls_building>
        <tls.discard-simple value="true"/>
        <tls.join value="true"/>
        <tls.guess-signals value="true"/>
    </tls_building>

    <ramp_guessing>
        <ramps.guess value="true"/>
    </ramp_guessing>

    <junctions>
        <junctions.join value="true"/>
        <junctions.corner-detail value="5"/>
    </junctions>

    <report>
        <verbose value="true"/>
    </report>

</configuration>

```

1. [netconvert doc](https://sumo.dlr.de/docs/netconvert.html)

    sample: ```netconvert -c ../osm.netccfg --osm-files ../map.osm -o sumo.net.xml```

2. [osmBuild.py](https://sumo.dlr.de/docs/Tools/Import/OSM.html)

### 3. Generate random trips using [randomTrips.py](https://sumo.dlr.de/docs/Tools/Trip.html) and validate it using duarouter
1. Current Usage : 

```bash    
python $SUMO_HOME/tools/randomTrips.py -n sumo.net.xml -r sumo.rou.xml -b 0 -e 10000 -p 20 --min-distance 25 --fringe-factor 4 --random --intermediate 40  
```
Note: To generate longer trips within a network, intermediate way points may be generated using the option --intermediate (INT) [explanation](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#incomplete_routes_trips_and_flows). This will add the given number of via-edges to the trip definitions.

### 4. Make .sumocfg file for running sim
Sample

```xml
<?xml version='1.0' encoding='UTF-8'?>
<configuration>
<input>
    <net-file value="sumo.net.xml"/>
    <route-files value="sumo.rou.xml"/>
</input>
<time>
    <begin value="0"/>
</time>
<report>
    <verbose value="true"/>
    <no-step-log value="true"/>
</report>
</configuration>
```
### 5.. Capture the fcd-output using sumo-gui with `fcd-output.geo true` for 
Current Usage:

```bash
sumo-gui -c sumo.sumocfg --step-length 0.032 --fcd-output sumo_data.xml --fcd-output.geo true
```
# Alternative
U can also use osmWebWizard.py to generate SUMO data and vehicle demand from openstreet maps