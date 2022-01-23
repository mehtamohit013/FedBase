% Evaluating signal power (overall, not for an individual beam)
% for multiple BS, considering MIMO 4X4 transmitter
% and 2X2 MIMO receiver 

%% Data paths
HOME = getenv('HOME');
dpath = HOME+"/webots_code/data/5_bs/MAT/";
opath = HOME+"/webots_code/data/5_bs/OSM/";
rpath = HOME+"/webots_code/data/5_bs/Rays/";
save_dir = HOME+"/webots_code/data/5_bs/labels/";
counter = numel(dir(dpath+"*.mat"));
data = dir(dpath+"*.mat");

mkdir(save_dir);
mkdir(rpath);
save_data = dir(save_dir+"*.mat");
%% Antenna config
fac = 1e-7;
use_site = 1;
use_site = use_site + 1;
lat_sites = [[38.89328 38.89380 38.89393];[38.89500 38.89442 38.89455 38.89527 38.89463]];
lon_sites = [[-77.07611 -77.07590 -77.07644];[-77.07303 -77.07296 -77.07356 -77.07339 -77.07404]];
BS_lat = lat_sites(use_site,:);
BS_lon = lon_sites(use_site,:);


%% Array config for TX and RX
tx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);
rx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);



%% Iterating through all the data points
% Take approx 33s to complete one iteration on my pc
tstart = tic;
progressbar

for i=1:counter
    progressbar(i/counter)
   
    name = string(extractBetween(data(i).name,1,'.mat'));
    
    exist_fun = @(x) strcmp(save_data(x).name,name+".mat");
    tf2 = arrayfun(exist_fun,1:numel(save_data));
    
    if isempty(find(tf2, 1)) == 0
        continue
    end
    
    %Siteveiwer Object
    viewer = siteviewer("Buildings",opath+name+".osm","Basemap","topographic");

	d_path = dpath + name + ".mat";
	load(d_path);

	lat_rx = gps(2,1);
	lon_rx = gps(2,2);
	height_rx = gps(2,3);

	tx_site = txsite("Name","MIMO transmitter", ...
    "Latitude",BS_lat, ...
    "Longitude",BS_lon, ...
	"Antenna",tx_array, ...
    "AntennaHeight",5, ...
    "TransmitterPower",1, ...
    "TransmitterFrequency",60e9);

    rtpm = propagationModel('raytracing',...
    "Method",'sbr',...
    "BuildingsMaterial",'perfect-reflector',...
    "TerrainMaterial","perfect-reflector",...
    "MaxNumReflections",2,...
    "AngularSeparation","high");

    rx_site = rxsite("Name","MIMO receiver", ...
    "Latitude",lat_rx, ...
    "Longitude",lon_rx, ...
	"Antenna",rx_array, ...
    "AntennaHeight",height_rx);

    % ss in the format : row -> Transmitter and column-> Reciever
    ss = sigstrength(rx_site,tx_site,rtpm);
    rays = raytrace(tx_site,rx_site,rtpm);
    
    save(save_dir+name+".mat",'ss')
    save(rpath+name+".mat",'rays')

    if mod(i-1,500)==0 %#ok<ALIGN>
    	TEnd = toc(tstart);
    	fprintf("%i files have been saved ",i);
    	fprintf("Time elapsed %f \n", TEnd);
	end

    viewer.close()

    
end




