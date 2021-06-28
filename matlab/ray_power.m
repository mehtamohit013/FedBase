counter = 154; % No of files in samples dir
dpath = "/home/mohit/webots_code/data/samples/";
save_dir = "/home/mohit/webots_code/data/sample_label/";
fac = 1e-7;
tx1_lat = [38.8939600 38.8939601 38.8939600 38.8939601];
tx2_lat = [38.8946400 38.8946401 38.8946400 38.8946401];
tx1_lon = [-77.0782300 -77.0782300 -77.0782301 -77.0782301];
tx2_lon = [-77.0784600 -77.0784600 -77.0784601 -77.0784601];

viewer = siteviewer("Buildings","map.osm","Basemap","topographic");

for i=0:counter

	d_path = dpath + string(i) + ".mat";
	load(d_path);

	if(length(tx1)>0 & length(tx2)>0)
		tx_lat = cat(2,tx1_lat,tx2_lat);
		tx_lon = cat(2,tx1_lon,tx2_lon);
	end

	if(length(tx2)>0 & length(tx1)==0)
		tx_lat = tx2_lat;
		tx_lon = tx2_lon;
	end

	if(length(tx2)==0 & length(tx1)>0)
		tx_lat = tx1_lat;
		tx_lon = tx1_lon;
	end
	

	lat_rx = gps(1);
	lon_rx = gps(2);
	height_rx = gps(3);

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

    ss = sigstrength(rx_site,tx_site,rtpm);
    save(save_dir+string(i)+".mat",'ss')

    if mod(i,10)==0
    	fprintf("%i files have been saved\n",i)
	end
end




