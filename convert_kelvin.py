import json
import sys
import copy

import numpy as np


existing_file = sys.argv[1]

existing_json = {}
with open(existing_file, 'r') as ofile:
	existing_json = json.loads(ofile.read())
ofile.close()

new_json = copy.deepcopy(existing_json)

features = new_json['features']

large_values = False

for feature in features:
	_median = feature['properties']['_median']
	if float(_median) > 255:
		large_values = True

if large_values == True:

	for feature in features:
		_median = feature['properties']['_median']
		kelvin = 0
		first_step = (_median*0.000334)+0.1
		kelvin =1321.0789/np.log((774.8853/first_step)+1)
		feature['properties']['_median'] = kelvin


with open(existing_file.replace("a7_sliver", "a8_converted"), 'w') as ofile:
	ofile.write(json.dumps(new_json))
