# NPR Heat and Poverty Analysis

### Code by Sean McMinn and Nick Underwood; additional reporting by Meg Anderson and Nora Eckert

To determine the link between heat and income in U.S. cities, NPR used NASA satellite imagery and U.S. Census American Community Survey data. An open-source computer program developed by NPR downloaded median household income data for census tracts in the 100 most populated American cities, as well as geographic boundaries for census tracts. NPR combined these data with TIGER/Line shapefiles of the cities.

The software also downloaded thermal imagery for each city from NASA's Landsat 8 satellite, looking for days since 2011 in June, July and August when there was less than 4 percent cloud cover. NPR reviewed each of the satellite images and removed images that contained clouds or other obscuring features over the city of interest. In cases when there were multiple clear images of a city, we used the thermal reading that showed a greater contrast between the warm and cool parts of the area of interest. In cases where there were no acceptable images, we manually searched for additional satellite images, and found acceptable images from Landsat 8 for every city except for Hialeah and Miami, Fla., and Honolulu, which are frequently covered by clouds.

For each city, NPR aligned the satellite surface temperature data with the census tracts. For each census tract, the software trimmed the geography to only what is contained within the city of interest's boundaries, then removed any lakes, rivers, ocean, etc. It calculated a median temperature reading for each census tract. When all the tracts in a city were completed, it calculated a correlation coefficient (R) of the tracts to find the relationship between income and heat.

The satellite data measures temperature at a surface, like the ground or a rooftop. We used this measurement rather than ambient temperature, which measures the air about two meters above the ground. Measuring air is a more accurate measure of how people experience heat, but satellite data is more widely available than air temperature data. Using it allowed us to provide a more complete snapshot of temperature trends across many cities.

## Data files

Completed data files for each city are saved as .geojson files in `data/output/analysis_out/final/`.

Correlations for each city are listed in `good_images_w_r.json`.

## Simplified files

Also in the `final` directory is a directory called `simpl`. This has .geojson files with simplified polygons for mapping on the web. These are used in NPR's web maps and were simplified using [mapshaper](https://github.com/mbloch/mapshaper).


## Instructions To Reproduce Analysis

- `virtualenv heat-income`
- `cd heat-income`
- `pip install -r requirements.txt`
- Set your Census API key as an environment variable in `bin/activate`
- Download the manual images as GEOTIFFs (specified in `download_data.py`) from EarthExplorer
- `.sh mkfile.sh` (this will take a long time)

## Caveats
- There is a difference between poverty vs. low-income
- More detailed Census geography = larger margins of error
- We're using surface temperature, not ambient temperature
- Only one day of data per city
- Not every city is counted
- Some cities split satellite scene paths/rows, so we took the image from the scene that contained most of the city. You'll need to filter out tracts without heat data in any data analysis/mapping you do.