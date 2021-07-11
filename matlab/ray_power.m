% Evaluating signal power (overall, not for an individual beam)
% for multiple BS, considering MIMO 4X4 transmitter
% and 2X2 MIMO receiver 

%% Data paths
HOME = getenv('HOME');
dpath = HOME+"/webots_code/data/samples/";
save_dir = HOME+"/webots_code/data/sample_label/";
counter = numel(dir(dpath+"*.mat"))-1;
mkdir(save_dir);

%% Antenna config
fac = 1e-7;
BS_lat = [38.89328 38.89380 38.89393];
BS_lon = [-77.07611 -77.07590 -77.07644];


%% Array config for TX and RX
tx_array = arrayConfig("Size",[4 4],"ElementSpacing",[0.1 0.1]);
rx_array = arrayConfig("Size",[2 2],"ElementSpacing",[0.1 0.1]);

%% Siteveiwer Object
viewer = siteviewer("Buildings","map.osm","Basemap","topographic");

%% Iterating through all the data points
% Take approx 13s to complete one iteration on my pc
tstart = tic;
for i=0:counter

	d_path = dpath + string(i) + ".mat";
	load(d_path);

	lat_rx = gps(1);
	lon_rx = gps(2);
	height_rx = gps(3);

	tx_site = txsite("Name","MIMO transmitter", ...
    "Latitude",BS_lat, ...
    "Longitude",BS_lon, ...
	"Antenna",tx_array, ...
    "AntennaHeight",5, ...
    "TransmitterPower",5, ...
    "TransmitterFrequency",28e9);

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
    save(save_dir+string(i)+".mat",'ss')

    if mod(i,5)==0 %#ok<ALIGN>
    	TEnd = toc(tstart);
    	fprintf("%i files have been saved ",i+1);
    	fprintf("Time elapsed %f \n", TEnd);
	end
end




