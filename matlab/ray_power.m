% Evaluating signal power (overall, not for an individual beam)
% for multiple BS, considering MIMO 4X4 transmitter
% and 2X2 MIMO receiver 

%% Data paths
HOME = getenv('HOME');
dpath = HOME+"/webots_code/data/final/MAT/";
opath = HOME+"/webots_code/data/final/OSM/";
save_dir = HOME+"/webots_code/data/final/labels/";
counter = numel(dir(dpath+"*.mat"));
data = dir(dpath+"*.mat");
mkdir(save_dir);

%% Antenna config
fac = 1e-7;
use_site = 1;
use_site = use_site + 1;
lat_sites = [[38.89328 38.89380 38.89393];[38.89502 38.89442 38.89452]];
lon_sites = [[-77.07611 -77.07590 -77.07644];[-77.07303 -77.07294 -77.07358]];
BS_lat = lat_sites(use_site,:);
BS_lon = lon_sites(use_site,:);


%% Array config for TX and RX
tx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);
rx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);



%% Iterating through all the data points
% Take approx 33s to complete one iteration on my pc
tstart = tic;
for i=1:counter

    name = string(extractBetween(data(i).name,1,'.mat'));

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
    "TransmitterPower",5, ...
    "TransmitterFrequency",60e9);

    rtpm = propagationModel('raytracing',...
    "Method",'sbr',...
    "MaxNumReflections",5);

    rx_site = rxsite("Name","MIMO receiver", ...
    "Latitude",lat_rx, ...
    "Longitude",lon_rx, ...
	"Antenna",rx_array, ...
    "AntennaHeight",height_rx);

    % ss in the format : row -> Transmitter and column-> Reciever
    ss = sigstrength(rx_site,tx_site,rtpm);
    save(save_dir+name+".mat",'ss')

    if mod(i-1,500)==0 %#ok<ALIGN>
    	TEnd = toc(tstart);
    	fprintf("%i files have been saved ",i);
    	fprintf("Time elapsed %f \n", TEnd);
	end

    viewer.close()
end




