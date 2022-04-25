% Evaluating signal power (overall, not for an individual beam)
% for multiple BS, considering MIMO 4X4 transmitter
% and 2X2 MIMO receiver 

%% Reading config.xml
HOME = getenv('HOME');
cpath = HOME+"/webots_code/comms_lidar_ML/config.json";


% Reading and parsing .json;
fid = fopen(cpath); % Opening the file
raw = fread(fid,inf); % Reading the contents
str = char(raw'); % Transformation
fclose(fid); % Closing the file
config = jsondecode(str); % Using the jsondecode function to parse JSON from string


%% Data paths
data_dir = config.dpath;
dpath = data_dir+"/MAT/";
opath = data_dir+"/OSM/";
rpath = data_dir+"/Rays/";
save_dir = data_dir+"/labels/";
counter = numel(dir(dpath+"*.mat"));
data = dir(dpath+"*.mat");

mkdir(save_dir);
mkdir(rpath);
save_data = dir(save_dir+"*.mat");


%% Antenna config
fac = 1e-7;

tmp = config.(config.use_map);
BS = tmp.(config.use_BS);
BS_lat = BS(:,1);
BS_lon = BS(:,2);


%% Array config for TX and RX
tx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);
rx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);


%% Iterating through all the data points
tstart = tic;
progressbar

for i=1:counter
    progressbar(i/counter)
   
    name = string(extractBetween(data(i).name,1,'.mat'));
    
    % Checking whether the files already exists
    % If yes, skip the loop
    exist_fun = @(x) strcmp(save_data(x).name,name+".mat");
    tf2 = arrayfun(exist_fun,1:numel(save_data));
    
    if isempty(find(tf2, 1)) == 0
        continue
    end
    

    %Loading site from .osm file
    viewer = siteviewer("Buildings",opath+name+".osm","Basemap","topographic");

	% Loading pre-processed GPS data
    d_path = dpath + name + ".mat";
	load(d_path);

    % Reciever antenna attributes
	lat_rx = gps(2,1);
	lon_rx = gps(2,2);
	height_rx = gps(2,3);

    % Transmitter site
	tx_site = txsite("Name","MIMO transmitter", ...
    "Latitude",BS_lat, ...
    "Longitude",BS_lon, ...
	"Antenna",tx_array, ...
    "AntennaHeight",5, ...
    "TransmitterPower",1, ...
    "TransmitterFrequency",60e9);

    % Reciever site
    rx_site = rxsite("Name","MIMO receiver", ...
    "Latitude",lat_rx, ...
    "Longitude",lon_rx, ...
	"Antenna",rx_array, ...
    "AntennaHeight",height_rx);

    % Propogation Model
    rtpm = propagationModel('raytracing',...
    "Method",'sbr',...
    "BuildingsMaterial",'perfect-reflector',...
    "TerrainMaterial","perfect-reflector",...
    "MaxNumReflections",2,...
    "AngularSeparation","high");


    % Calculating signal strength
    ss = sigstrength(rx_site,tx_site,rtpm);

    % Storing all the details of the reflacted ray and their point of reflection
    rays = raytrace(tx_site,rx_site,rtpm);
    
    % Saving 
    save(save_dir+name+".mat",'ss')
    save(rpath+name+".mat",'rays')

    if mod(i-1,500)==0 %#ok<ALIGN>
    	TEnd = toc(tstart);
    	fprintf("%i files have been saved ",i);
    	fprintf("Time elapsed %f \n", TEnd);
	end

    viewer.close()

end