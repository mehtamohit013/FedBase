function [ant_array_lat,ant_array_lon] = create_array(lat,lon,horz_len,vert_len,fac)
	ant_array_lat = [];
	ant_array_lon = [];
	for i=1:horz_len
		for j=1:vert_len
			ant_array_lat = cat(2,ant_array_lat,[lat+i*fac]);
			ant_array_lon = cat(2,ant_array_lon,[lon+j*fac]);
		end
	end
end