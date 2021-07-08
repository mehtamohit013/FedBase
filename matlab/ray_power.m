%% Data paths
counter = 154; % No of files in samples dir
HOME = getenv('HOME');
dpath = HOME+"/webots_code/data/samples/";
save_dir = HOME+"/webots_code/data/sample_label/";

%% Antenna config
fac = 1e-7;
tx1_lat_base = 38.8939600;
tx1_lon_base = -77.0782300;
tx2_lat_base = 38.8946400;
tx2_lon_base = -77.0784600;

%% Creating antenna arrays -> 32 : 8X4 arrays
[tx1_lat,tx1_lon] = create_array(tx1_lat_base,tx1_lon_base,8,4,fac);
[tx2_lat,tx2_lon] = create_array(tx2_lat_base,tx2_lon_base,8,4,fac);

%% Siteveiwer Object
viewer = siteviewer("Buildings","map.osm","Basemap","topographic");

%% Iterating through all the data points
% Take approx 3min to complete one iteration on my pc
tstart = tic;
for i=0:counter

	d_path = dpath + string(i) + ".mat";
	load(d_path);

	if(~isempty(tx1) && ~isempty(tx2))
		tx_lat = cat(2,tx1_lat,tx2_lat);
		tx_lon = cat(2,tx1_lon,tx2_lon);
	end

	if(~isempty(tx2) && isempty(tx1))
		tx_lat = tx2_lat;
		tx_lon = tx2_lon;
	end

	if(isempty(tx2) && ~isempty(tx1))
		tx_lat = tx1_lat;
		tx_lon = tx1_lon;
	end
	

	lat_base_rx = gps(1);
	lon_base_rx = gps(2);
	height_rx = gps(3);

	%  Creating a 4X2 array config -> 8 recievers
	[lat_rx,lon_rx] = create_array(lat_base_rx,lon_base_rx,4,2,fac);

	tx_site = txsite("Name","MIMO transmitter", ...
    "Latitude",tx_lat, ...
    "Longitude",tx_lon, ...
    "AntennaHeight",5, ...
    "TransmitterPower",5, ...
    "TransmitterFrequency",28e9);

    rtpm = propagationModel('raytracing',...
    "Method",'sbr',...
    "MaxNumReflections",5);

    rx_site = rxsite("Name","SISO receiver", ...
    "Latitude",lat_rx, ...
    "Longitude",lon_rx, ...
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




