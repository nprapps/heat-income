# FORM LIST OF CITIES IN A WAY WE CAN PIPE TO PARALLEL

rm list_of_cities.txt

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

    	FULL_INPUT="$CITY $STATE"
    	echo $FULL_INPUT >> list_of_cities.txt 
    done




# # RUN PARALLEL TO PERFORM GEOANALYSIS/R ANALYSIS ON EACH CITY

# cat list_of_cities.txt | parallel -u --verbose -j 4 --colsep ' ' sh single_process.sh {}





# OBTAIN R VALUE FROM EACH CITY THEN PUT IT INTO GOOD_IMAGES_W_R.JSON


cp good_images.json good_images_w_r.json

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

		# add r to cities json

		R_INCOME=$(cat "data/output/analysis_out/$CITY/median_hou-R.txt")
		R_NONWHITE=$(cat "data/output/analysis_out/$CITY/nonwhite_pct-R.txt")

		tmp=$(mktemp)

		# cat good_images_w_r.json 

		cat good_images_w_r.json |  jq "map(if .name == \"$KEY\" then . + {\"r-income\":\"$R_INCOME\", \"r-nonwhite\": \"$R_NONWHITE\"} else . end ) "> "$tmp"

		mv "$tmp" good_images_w_r.json
	done

	