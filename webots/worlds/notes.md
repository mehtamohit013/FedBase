# Steps to construct SUMO files
 
### 1. Download the corresponding osm file from openstreetmaps using the export functionality.
### 2. Use either osmBuild.py or netconvert using osm.sumocfg fle to convert the osm file to the corresponding .net.xml
1. [netconvert doc](https://sumo.dlr.de/docs/netconvert.html)
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