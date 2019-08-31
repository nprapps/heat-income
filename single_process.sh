#store city and state as variables, replace " " with "-"
STATE=$2
CITY=$1

#data references
KEY="$STATE-$CITY"
echo $KEY
RASTER=$(cat good_images.json | jq -r ".[] | select(.name==\"$KEY\") | .\"image\"")

STATE_TRACTS="./data/output/$STATE/*tract_merged.shp"
CITY_BOUNDARY="./data/boundaries-census/$CITY.json"
CITY_RASTER="./data/output/images/$STATE-$CITY/$RASTER"
OCEAN="./water/ne_10m_ocean.shp"
WATER_BODIES="./water/USA_Detailed_Water_Bodies.shp"


#right now only run for cities with files
if [ "$RASTER" = '' ];
then
	echo "$KEY has no raster!"
	cp $CITY_BOUNDARY boundaries/$CITY.json

else
	echo "Begin $KEY"

	## check if directory exists, if so delete and recreate
	if [ -d ./data/output/analysis_out/$CITY ]; then
		rm -rf ./data/output/analysis_out/$CITY
	fi

	if [ ! -d ./data/output/analysis_out/ ]; then
		mkdir ./data/output/analysis_out/
		mkdir ./data/output/analysis_out/final
		mkdir ./data/output/analysis_out/final/simpl
	fi


	if [ ! -d ./data/output/analysis_out/$CITY ]; then
		mkdir ./data/output/analysis_out/$CITY
	fi

	#dissolve city polygons to one boundary
	mapshaper $CITY_BOUNDARY -dissolve2 \
	-o ./data/output/$STATE/$CITY-polygon-dissolved.shp
	CITY_BOUNDARY_DIS=./data/output/$STATE/$CITY-polygon-dissolved.shp
	echo "dissolved finished $KEY"

	#project tracts to wgs84
	ogr2ogr ./data/output/analysis_out/$CITY/a1_project.shp -t_srs "EPSG:4326" $STATE_TRACTS
	echo "A1 finished $KEY"

	#clip to city boundary
	mapshaper ./data/output/analysis_out/$CITY/a1_project.shp -clip $CITY_BOUNDARY_DIS -o ./data/output/analysis_out/$CITY/a2_clip_city.shp
	echo "A2 finished $KEY"

	#hole punch for ocean and waterbodies
	mapshaper ./data/output/analysis_out/$CITY/a2_clip_city.shp \
	-erase $OCEAN -o ./data/output/analysis_out/$CITY/a3_erase_ocean.shp
	echo "A3 finished $KEY"
	mapshaper ./data/output/analysis_out/$CITY/a3_erase_ocean.shp \
	-erase $WATER_BODIES -o ./data/output/analysis_out/$CITY/a4_erase_wb.shp
	echo "A4 finished $KEY"

	#project tracts to raster projection
	ogr2ogr ./data/output/analysis_out/$CITY/a5_shapes.geojson \
		-f GeoJSON \
		-s_srs "EPSG:4326" \
		-t_srs "$(gdalsrsinfo $CITY_RASTER -O proj4)" \
		./data/output/analysis_out/$CITY/a4_erase_wb.shp
	echo "A5 finished $KEY"

	#Zonal stats. Make sure to run pip install rasterio rasterstats boto3
	rio zonalstats  ./data/output/analysis_out/$CITY/a5_shapes.geojson \
		-r $CITY_RASTER --stats "median" \
		> ./data/output/analysis_out/$CITY/a6_stats.geojson
	echo "A6 finished $KEY"

	#filter out slivers
	mapshaper ./data/output/analysis_out/$CITY/a6_stats.geojson \
		-filter '_median != null'\
		-o ./data/output/analysis_out/$CITY/a7_sliver.geojson
	echo "A7 finished $KEY"

	# convert spectral raidance => degrees kelvin
	`python convert_kelvin.py ./data/output/analysis_out/$CITY/a7_sliver.geojson` 
	echo "a8 finished $KEY"

	#project back to wgs84 for visualization with D3
	ogr2ogr ./data/output/analysis_out/$CITY/a9_final.geojson \
		-f GeoJSON \
		-s_srs "$(gdalsrsinfo $CITY_RASTER -O proj4)" \
		-t_srs "EPSG:4326" \
		./data/output/analysis_out/$CITY/a8_converted.geojson
	echo "A9 finished $KEY"

	# copy file to final folder
	cp ./data/output/analysis_out/$CITY/a9_final.geojson ./data/output/analysis_out/final/$CITY.geojson
	echo "FINAL finished $KEY"

	# copy good image to good-images folder and boundary to boundary folder
	mkdir -p good-images
	mkdir -p boundaries
	cp $CITY_RASTER good-images/$CITY.tif
	cp $CITY_BOUNDARY boundaries/$CITY.json


	if [ ! -d ./data/output/analysis_out/final/simpl ]; then
		mkdir ./data/output/analysis_out/final/simpl
	fi

	# simplify final output
	mapshaper ./data/output/analysis_out/final/$CITY.geojson -simplify visvalingam 20% -o format=geojson ./data/output/analysis_out/final/simpl/$CITY.geojson

	# calculate r values and store them in data/output/analysis_out/$citty
	R_INCOME=`python analyze_geojson_output.py ./data/output/analysis_out/$CITY/a9_final.geojson median_hou`
	R_NONWHITE=`python analyze_geojson_output.py ./data/output/analysis_out/$CITY/a9_final.geojson nonwhite_pct`


fi