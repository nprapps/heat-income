import json
import zipfile, io
import glob, os
import urllib.parse, urllib.request
import glob, os
import ssl

import requests
from bs4 import BeautifulSoup
from satsearch import Search 
import geopandas as gpd


########## start __main__ function ##########

def main():


	cities = []
	with open('data/cities.json', 'r') as ofile:
		cities = json.loads(ofile.read())
	ofile.close()



	for city in cities[76:77]:
		city['state_fips'] = get_fips(city['state'])
		city['county'] = get_county(city)
		print(city)


		try:
			download_census_shp(city)
		except Exception as e: print('download shp error ' + str(e))
		try:
			download_census_data(city)
		except Exception as e: print('download census data error ' + str(e))
		try:
			# austin (TX) and st petersburg (FL) not loading - be sure to grab by hand
			download_tiles_plus_geojson(city)
		except Exception as e: print('download tile error ' + str(e))
		try:
			merge_census_shp(city)
		except Exception as e: print('merge shp file error ' + str(e))


########## end __main__ function ##########




def download_census_shp(city):
	base_url = "https://www2.census.gov/geo/tiger/TIGER2017/TRACT/tl_2017_--FIPS--_tract.zip"
	real_url = base_url.replace("--FIPS--", city['state_fips'])
	resp = requests.get(real_url)

	z = zipfile.ZipFile(io.BytesIO(resp.content))

	z.extractall('data/output/' + clean_path_name(city['state']))



def download_census_data(city):


	state = city['state']
	county = city['county']
	state_fips = city['state_fips']


	# swap in your own census API key here
	api_key =  os.getenv('CENSUS_API_KEY')

	# name, geoid, median income by residence
	# https://api.census.gov/data/2015/acs/acs1/groups/B07011.html
	query_variables = ["NAME","GEO_ID", "B02001_002E", "B01003_001E", "B19013_001E"]
	query_keys = {"B02001_002E": "white population", "B01003_001E": "total population", "B19013_001E": "Median household income in the past 12 months"}
	base_url = "https://api.census.gov/data/2017/acs/acs5/"
	request_url = base_url + "?get=" + ",".join(query_variables) + "&in=state:" + state_fips + "&for=tract:*&key=" + api_key

	state_census_output_file = "data/output/" + clean_path_name(state) + "/" + 'tracts-data.json'

	resp = requests.get(request_url)

	resp_text_obj = json.loads(resp.text)

	# cleanup var names
	for ind, col_head in enumerate(resp_text_obj[0]):
		if col_head in query_keys:
			resp_text_obj[0][ind] = query_keys[col_head].lower().replace(" ", "_")


	with open(state_census_output_file, 'w') as ofile:
		ofile.write(json.dumps(resp_text_obj))
	ofile.close()


def download_tiles_plus_geojson(city):


	custom_dates = {}

	with open("data/manual_override_imagedates.json", "r") as ofile:
		custom_dates = json.loads(ofile.read())
	ofile.close()

	custom_colrows = {}

	with open("data/manual_override_colrows.json", "r") as ofile:
		custom_colrows = json.loads(ofile.read())
	ofile.close()


	good_imgs = []
	good_imgs_dict = {}

	with open("good_images.json", "r") as ofile:
		good_imgs = json.loads(ofile.read())
	ofile.close()

	for item in good_imgs:
		good_imgs_dict[item['name']] =  item["image"]

	
	cityDir = 'data/output/images/' + clean_path_name(city['state']) + "-" + clean_path_name(city['name'])


	
	coord_output_file = "data/boundaries-census/"+ city['name'].lower().replace(" ", "-") +".json"


	# THESE THREE ARE PULLING INCORRECTLY FROM TIGER
	osm_boundaries = ["louisville", "washington", "glendale"]

	if city['name'].lower() in osm_boundaries:
		coordinates = get_geom(city)

		with open(coord_output_file, 'w') as ofile:
			ofile.write(json.dumps(coordinates))
		ofile.close()

	else:
		with open(coord_output_file, 'r') as ofile:
			coordinates = json.loads(ofile.read())
		ofile.close()


		coordinates = coordinates['features'][0]['geometry']


	print('downloading new data')

	centroid = get_center_coordinate(coordinates['coordinates'])[0]
	bbox = get_center_coordinate(coordinates['coordinates'])[1]


	if city['name'] not in custom_colrows:
		centroid_colrows = get_landsat_colrows(centroid)
	else:
		centroid_colrows = [custom_colrows[city['name']]]


	query_params = {
	  "eo:cloud_cover": {
	    "lt": 4
	  },
	  "collection": {
	    "eq": "landsat-8-l1"
	  }
	}
	time_range = "2011/2019"


	

	if city['name'] in custom_dates:
		if "LC80" in custom_dates[city['name']]:
			api_base_url = "http://sat-api.developmentseed.org/collections/landsat-8-l1/items/"
			resp = requests.get(api_base_url + custom_dates[city['name']])
			if "not found" in resp.text.lower():
				print("Need to download image manually for " + city['name'] + "!")
				return
			json_obj = json.loads(resp.text)
			assets = json_obj['assets']
			b10_url = assets['B10']['href']
			ssl._create_default_https_context = ssl._create_unverified_context
			try:
				os.mkdir(cityDir +"/")
			except:
				pass
			urllib.request.urlretrieve(b10_url, cityDir +"/"+ b10_url.split("/")[-1])
			return

		query_params['eo:cloud_cover'] = {"lt": 100}
		time_range = custom_dates[city['name']]
		bbox_search = [bbox['x1'], bbox['y1'], bbox['x2'], bbox['y2']]
		search = Search(bbox=bbox_search, query=query_params, time=time_range)

	else:
		search = Search(intersects=coordinates, query=query_params, time=time_range)


	scenes = search.items()

	print(len(scenes))


	def summer_date(date_str):
		for month in ['06', '07', '08']:
			if "-" + month + "-" in date_str:
				return True
		return False

	def in_colrows(scene, centroid_colrows):
		for colrow in centroid_colrows:
			if int(scene["eo:row"]) == int(colrow['row']) and int(scene["eo:column"]) == int(colrow['col']):
				return True
		return False



	if city['name'] in custom_dates:
		for ind, scene in enumerate(scenes):
			scene.download("B10", path=cityDir, filename='good' + str(ind))
			print("manual scene downloaded")
	else:
		colrow_scenes = [x for x in scenes if in_colrows(x, centroid_colrows)]

		summer_scenes = [x for x in colrow_scenes if summer_date(str(x.date))]


		all_colrows = {}

		for scene in summer_scenes:
			colrow = scene['eo:column'] + "-" + scene['eo:row']
			if colrow not in all_colrows:
				all_colrows[colrow] = 0
		

		for scene in summer_scenes:
			colrow = scene['eo:column'] + "-" + scene['eo:row']
			export_name = colrow + "-" + str(scene.date)
			if export_name in good_imgs_dict[clean_path_name(city['state']) + "-" + clean_path_name(city['name'])]:
				scene.download("B10", path=cityDir, filename=colrow + "-" + str(scene.date))
				print("non-manual scene downloaded")

			all_colrows[colrow] = all_colrows[colrow] + 1 
			full_colrows_threshold = 2
			if full_colrows_check(all_colrows, full_colrows_threshold) == True:
				break




def get_landsat_colrows(centroid):

	def get_xcsrftoken(html_str):
		lines = html_str.split("\n")
		for line in lines:
			if "X-Csrf-Token" in line:
				return line.split("X-Csrf-Token', '")[1].replace("');", "")

	def get_php_sess(resp_header):
		after_last_phpsessid = initial_resp.headers['Set-Cookie'].split("PHPSESSID=")[-1]
		phpsessid = after_last_phpsessid.split("; ")[0]
		return phpsessid

	def make_post_requests(phpsessid, xcsrftoken, centroid, collection_id=12864):
		save_headers = {"Accept": "text/html, */*; q=0.01",
						"Accept-Encoding": "gzip, deflate, br",
						"Accept-Language": "en-US,en;q=0.9,la;q=0.8,fy;q=0.7",
						"Connection": "keep-alive",
						"Content-Length": "18",
						"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
						"Cookie": "PHPSESSID="+ phpsessid +"; _ga=GA1.2.1836831423.1561566866; _gid=GA1.2.1967535729.1561566866; _ga=GA1.3.1836831423.1561566866; _gid=GA1.3.1967535729.1561566866; _gat_ee=1; _gat_lta=1; _gat_GSA_ENOR0=1; _gat_GSA_ENOR1=1; _gat_GSA_ENOR2=1",
						"Host": "earthexplorer.usgs.gov",
						"Origin": "https://earthexplorer.usgs.gov",
						"Referer": "https://earthexplorer.usgs.gov/",
						"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36",
						"X-Csrf-Token": get_xcsrftoken(initial_resp.text),
						"X-Requested-With": "XMLHttpRequest"}

		save_data = {"tab":1,
					"destination":4,
					"coordinates":[{"c":"0","a":centroid['y'],"o":centroid['x']}],
					"format":"dms",
					"dStart":"",
					"dEnd":"",
					"searchType":"Std",
					"num":"1000",
					"includeUnknownCC":"1",
					"maxCC":100,
					"minCC":0,
					"months":["5","6","7"],
					"pType":"polygon"}

		save_post = session.post("https://earthexplorer.usgs.gov/tabs/save", headers=save_headers, data={"data": json.dumps(save_data)})
		index_resp = session.post('https://earthexplorer.usgs.gov/result/index', headers=save_headers, data={"collectionId": 12864})
		return index_resp.text


	def parse_colrow(html_text):
		colrows = []
		soup = BeautifulSoup(html_text, 'html.parser')
		result_row_contents = soup.select("td.resultRowContent")
		for row in result_row_contents:
			d = {}
			for list_item in row.select("li"):
				if "<strong>Path:</strong>" in str(list_item):
					d['col'] =list_item.text.split(":")[1]
				if "<strong>Row:</strong>" in str(list_item):
					d['row'] =list_item.text.split(":")[1]
			if d != {} and d not in colrows:
				colrows.append(d)

		return colrows


	session = requests.Session()
	initial_resp = session.get('https://earthexplorer.usgs.gov/')
	phpsessid = get_php_sess(initial_resp.headers['Set-Cookie'])
	html_text = make_post_requests(phpsessid, get_xcsrftoken(initial_resp.text), centroid)
	colrows = parse_colrow(html_text)

	return colrows





def get_geom(city):
	domain = "https://nominatim.openstreetmap.org/"

	resp = requests.get(domain + 'search.php?q='+ city['name'].replace(" ", "+") + "+" + city['state'].replace(" ", "+") +'&polygon_geojson=1')


	soup = BeautifulSoup(resp.text, "html.parser")

	result_url = soup.select("a.btn-xs.details")[0]['href']


	if city['name'].lower() in ["anchorage", "durham"]:
		result_url = soup.select("a.btn-xs.details")[1]['href']
	else:
		result_type = soup.select("#searchresults .result .type")[0].text
		if result_type != "(City)":
			print("NOT A CITY!")
			resp = requests.get(domain + 'search.php?q='+ city['name'].replace(" ", "+")  +'&polygon_geojson=1')
			soup = BeautifulSoup(resp.text, "html.parser")
			result_url = soup.select("a.btn-xs.details")[0]['href']
			result_type = soup.select("#searchresults .result .type")[0].text
			if result_type != "(City)":
				print("STILL NOT A CITY!")
				resp = requests.get(domain + 'search.php?q='+ city['name'].replace(" ", "+") + "+" + "city"  +'&polygon_geojson=1')
				soup = BeautifulSoup(resp.text, "html.parser")
				result_url = soup.select("a.btn-xs.details")[0]['href']
				result_type = soup.select("#searchresults .result .type")[0].text



	detailed_resp = requests.get(domain + result_url)

	detailed_soup = BeautifulSoup(detailed_resp.text, "html.parser")

	relation_links = [x for x in detailed_soup.select("a") if '/relation/' in x['href']]

	osm_id = relation_links[0]['href'].split("/")[-1]

	osm_resp = requests.get("http://polygons.openstreetmap.fr/get_geojson.py?id="+ osm_id +"&params=0")

	osm_gemo = json.loads(osm_resp.text)['geometries'][0]

	return osm_gemo


def clean_path_name(text_input):
	return text_input.lower().replace(" ", "-")



def get_center_coordinate(coord_list):

	# print(coord_list)

	bbox = {}


	for sub_coord_list in coord_list:
		if len(sub_coord_list) == 1:
			point_container = sub_coord_list[0]
		elif type(sub_coord_list[0]) == list:
			point_container = []
			for sub_sub_coord_list in sub_coord_list:
				point_container = point_container + sub_sub_coord_list
		if type(sub_coord_list[0][0]) == float:

			point_container = sub_coord_list
		for point in point_container:
			if len(bbox.keys()) == 0:
				bbox['x1'] = point[0]
				bbox['x2'] = point[0]
				bbox['y1'] = point[1]
				bbox['y2'] = point[1]
			else:
				if point[0] < bbox['x1']:
					bbox['x1'] = point[0]
				if point[0] > bbox['x2']:
					bbox['x2'] = point[0]
				if point[1] < bbox['y1']:
					bbox['y1'] = point[1]
				if point[1] > bbox['y2']:
					bbox['y2'] = point[1]

	centroid = {}

	centroid['x'] = bbox['x1'] + ((bbox['x2'] - bbox['x1']) / 2);
	centroid['y'] = bbox['y1'] + ((bbox['y2'] - bbox['y1']) / 2);


	return [centroid, bbox]






def get_county(city):
	# getting network/request info from here
	# http://statsamerica.org/CityCountyFinder/Default.aspx
	url = "http://www.stats.indiana.edu/uspr/b/place_query.asp"
	form_data = {"states": city['state_fips'],
				"place_name": city['name'],
				"Submit": "Submit"}
	headers = {"Content-Type": "application/x-www-form-urlencoded"}
	resp = requests.post(url, headers=headers, data=urllib.parse.urlencode(form_data))


	soup = BeautifulSoup(resp.text, "html.parser")

	try:
		soup_body = soup.select("body")[0]
	except:
		print(city)
		print(resp.text)
	first_result = soup_body.select("tr")[1]
	try:
		county_cell = first_result.select("td")[2]
	except:
		return city['county']
	county = county_cell.text.split(" County,")[0]

	# cleanup
	county = county.replace("City", "").strip()

	return county


def get_fips(statename):
	state_fips = {}

	with open("data/state_fips_full.json", "r") as ofile:
		state_fips = json.loads(ofile.read())
	ofile.close()

	state_id = state_fips[statename]

	return state_id

def full_colrows_check(input_dict, full_threshold):
	full_status = True
	overfull_status = False
	for key in input_dict:
		if input_dict[key] > full_threshold + 1:
			overfull_status = True
		if input_dict[key] < full_threshold:
			full_status = False
	if overfull_status == True:
		return True
	return full_status


def merge_census_shp(city):

	added_extension = "merged"

	census_data = []
	census_output_file = "data/output/" + clean_path_name(city['state']) + '/tracts-data.json'

	with open(census_output_file, 'r') as ofile:
		census_data = json.loads(ofile.read())
	ofile.close()

	census_formatted = []

	for census_row in census_data:
		if census_row != census_data[0]:
			d = {}
			for ind, datum in enumerate(census_row):
				d[census_data[0][ind]] = datum
			census_formatted.append(d)


	gpd_census_data = gpd.GeoDataFrame(census_formatted)
	gpd_census_data['GEOID'] = gpd_census_data["GEO_ID"].str.replace("1400000US", "")


	state_shp_path = ""

	for file in glob.glob("data/output/" + clean_path_name(city['state']) + "/*_tract.shp"):
		state_shp_path = file


	gpd_shp_data = gpd.read_file(state_shp_path)

	gpd_shp_data = gpd_shp_data.merge(gpd_census_data, how='left', on='GEOID')


	gpd_shp_data.to_file(state_shp_path.split(".shp")[0].replace("_" + added_extension, "") + "_"+ added_extension +".shp")



	print('\n========\n')


if __name__ == "__main__":
	main()