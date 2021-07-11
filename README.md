# Base station selection

Currently, calculating signal power of a base station as a whole, not individual beams from a
base station

## Specifications
1. Range of lidar sensor : 120 m i.e. from [-120,120]
2. Height range : Approx [-2.2,4.35]
3. Assign the values of the obstacles point cloud value to 1
4. Lidar Array Size = [20,440,440]

    Antenna range : 100m
   
    Lidar Range : 120 m
    
    Overall Range : [-220m,220m] == 440
5. Transmitter Array : 4X4 arrayconfig object
6. Receiver Array : 2X2 arrayConfig object 

# To-Do
1. Elminate the for loop in process_data.py (in main func)
2. Add values for transmitter and receiver in final lidar array
3. Eliminate for loop in lidar_array in process_data.py
4. Increase traffic
5. Add multi processing support to process_data.py