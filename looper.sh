# loop through cities json
for ROW in $(cat data/cities.json | jq -r '.[] | @base64')
	do 
		_jq() {
     	echo ${ROW} | base64 --decode | jq -r ${1}
    	}
    	#store city and state as variables, replace " " with "-"
    	CITY_RAW=$(_jq '.name' | tr '[:upper:]' '[:lower:]')
    	STATE_RAW=$(_jq '.state' | tr '[:upper:]' '[:lower:]')

    	#data references
    	CITY=${CITY_RAW// /-}
    	STATE=${STATE_RAW// /-}
    	KEY="$STATE-$CITY"
    	RASTER=$(cat good_images.json | jq -r '.[] | select(.name=="'$KEY'") | ."image"')

    	STATE_TRACTS="./data/output/$STATE/*tract_merged.shp"
		CITY_BOUNDARY="./data/output/$STATE/$CITY-polygon.json"
		CITY_RASTER="./data/output/images/$STATE-$CITY/$RASTER"
		OCEAN="./water/ne_10m_ocean.shp"
		WATER_BODIES="./water/USA_Detailed_Water_Bodies.shp"

    	#right now only run for cities with files
    	if [ "$RASTER" = '' ];
    	then
    		echo "$KEY has no raster!"
    		cp $CITY_BOUNDARY boundaries/$CITY.json

    	else
    		echo "Running zonal stats for $KEY"

			## check if directory exists, if so delete and recreate
			if [ -d ./analysis_out/$CITY ]; then
				rm -rf ./analysis_out/$CITY
			fi

			if [ ! -d ./analysis_out/$CITY ]; then
				mkdir ./analysis_out/$CITY
			fi

			#dissolve city polygons to one boundary
			mapshaper $CITY_BOUNDARY -dissolve2 \
			-o ./data/output/$STATE/$CITY-polygon-dissolved.shp
			CITY_BOUNDARY_DIS=./data/output/$STATE/$CITY-polygon-dissolved.shp
				
			#project tracts to wgs84
			ogr2ogr ./analysis_out/$CITY/a1_project.shp -t_srs "EPSG:4326" $STATE_TRACTS

			#clip to city boundary
			mapshaper ./analysis_out/$CITY/a1_project.shp -clip $CITY_BOUNDARY_DIS -o ./analysis_out/$CITY/a2_clip_city.shp

			#hole punch for ocean and waterbodies
			mapshaper ./analysis_out/$CITY/a2_clip_city.shp \
			-erase $OCEAN -o ./analysis_out/$CITY/a3_erase_ocean.shp
			mapshaper ./analysis_out/$CITY/a3_erase_ocean.shp \
			-erase $WATER_BODIES -o ./analysis_out/$CITY/a4_erase_wb.shp

			#project tracts to raster projection
			ogr2ogr ./analysis_out/$CITY/a5_shapes.geojson \
				-f GeoJSON \
				-s_srs "EPSG:4326" \
				-t_srs "$(gdalsrsinfo $CITY_RASTER -O proj4)" \
				./analysis_out/$CITY/a4_erase_wb.shp

			#Zonal stats. Make sure to run pip install rasterio, rasterstats, boto3
			rio zonalstats  ./analysis_out/$CITY/a5_shapes.geojson \
				-r $CITY_RASTER --stats "median" \
				> ./analysis_out/$CITY/a6_stats.geojson

			#filter out slivers
			mapshaper ./analysis_out/$CITY/a6_stats.geojson \
				-filter '_median != null'\
				-o ./analysis_out/$CITY/a7_sliver.geojson

			#project back to wgs84 for visualization with D3
			ogr2ogr ./analysis_out/$CITY/a8_final.geojson \
				-f GeoJSON \
				-s_srs "$(gdalsrsinfo $CITY_RASTER -O proj4)" \
				-t_srs "EPSG:4326" \
				./analysis_out/$CITY/a7_sliver.geojson

			copy file to final folder
			cp ./analysis_out/$CITY/a8_final.geojson ./analysis_out/final/$CITY.geojson

			copy good image to good-images folder and boundary to boundary folder
			cp $CITY_RASTER good-images/$CITY.tif
			cp $CITY_BOUNDARY boundaries/$CITY.json

			##calculate r-squared
			R=`python analyze_geojson_output.py ./analysis_out/$CITY/a8_final.geojson`
			echo $R

			##add r-squared to cities json
			tmp=$(mktemp)
			cat good_images.json | jq 'map(if .name == "'$KEY'" then . + {"r-squared":"'$R'"} else . end )' > "$tmp" && mv "$tmp" good_images.json
			#cat data/cities.json | jq -r '.[] | select(.name=="'$CITY_UPPER'") + { "r-squared": '$R' }'
    	fi

done