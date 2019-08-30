import os
import json

cities = []


def clean_path_name(text_input):
	return text_input.lower().replace(" ", "-")

with open('data/cities.json', 'r') as ofile:
	cities = json.loads(ofile.read())

for city in cities:
	if os.path.isdir('data/output/images/' + clean_path_name(city['state'] + '-' + city['name'])) == False:
		print(city)

