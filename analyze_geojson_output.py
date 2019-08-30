import json
from pprint import pprint
import sys

import numpy as np


# DEFINE WHAT VARIABLES YOU WANT TO COMPARE
# x_attribute = "median_hou"
x_attribute = sys.argv[2]
y_attribute = "_median"

x_values = []
y_values = []


# LOAD GEOJSON AS A DICTIONARY
geojson = {}

with open(sys.argv[1], 'r') as ofile:
	geojson = json.loads(ofile.read())
ofile.close()

# COMPILE VARIABLES INTO TWO LISTS

for feature in geojson['features']:

	if x_attribute == "nonwhite_pct":
		total_pop = int(feature['properties']['total_popu'])
		white_pop = int(feature['properties']['white_popu'])
		if total_pop > 0:
			x = (total_pop - white_pop) / total_pop
		else:
			x = None
	else:
		print(feature['properties'])
		x = int(feature['properties'][x_attribute])
	y = feature['properties'][y_attribute]



	# IF THERE ARE NULL DATA VALUES, EITHER CONVERTS TO ZERO OR IGNORES - YOU CHOOSE!

	# filter out income no data value (specifically the -66666...s)
	if x_attribute == "median_hou" and x < 0:
		x = None

	# if x == None:
	# 	x = 0
	# if y == None:
	# 	y = 0
	if x == None or y == None or y == 0:
		continue

		
	x_values.append(x)
	y_values.append(y)


# PRINTS OUT THE COEFFICIENT USING NUMPY LIBRARY
print(np.corrcoef(x_values, y_values)[0][1])

output_dir = sys.argv[1].split("a9_final")[0].replace("./", "")

with open(output_dir + sys.argv[2] + "-R.txt", 'w') as ofile:
	ofile.write(str(np.corrcoef(x_values, y_values)[0][1]))
