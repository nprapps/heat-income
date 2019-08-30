# NPR Heat and Poverty Analysis

To determine the link between heat and poverty in a U.S. cities, we used NASA satellite imagery and U.S. Census American Community Survey data. An open-source computer program developed by NPR downloaded median household income data for Census tracts in 97 American cities, as well as geographic boundaries for Census tracts. NPR combined these data with TIGER/Line shapefiles of the 100 largest U.S. cities.

The software also downloaded thermal imagery for each city from NASA’s Landsat 8 satellite, looking for days since 2011 in June, July and August when there was less than 4 percent cloud cover. NPR reviewed each of the satellite images and removed images that contained clouds or other obscuring features over the city of interest. In cases when there were multiple clear images of a city, we chose the thermal reading that showed a greater contrast between the warm and cool parts of the area of interest. In cases where there were no acceptable images, staff searched for additional satellite images, and found acceptable images from Landsat 8 for every city except for Hialeah and Miami, Fla., and Honolulu, which are frequently covered by clouds.

For each city, a second piece of software developed by NPR aligned the satellite surface temperature data with the Census tracts. For each Census tract, it trimmed the geography to only the part contained within the city of interest’s boundaries, then removed any lakes, rivers, etc. It calculated a median temperature reading for each census tract. When all the tracts in a city were completed, it calculated a correlation coefficient (R) of the tracts to find the relationship between income and heat.

To determine which cities to highlight in the story, NPR chose the 10 cities with the strongest negative correlation of income and temperature.


## Instructions To Reproduce Analysis

- `pip install -r requirements.txt`
- `mkdir water`
- Download the [Natural Earth Ocean .shp file](https://www.naturalearthdata.com/downloads/10m-physical-vectors/) and [ArcGIS USA Detailed Water Bodies .shp files](https://www.arcgis.com/home/item.html?id=84e780692f644e2d93cefc80ae1eba3a) and place the contents of both into the `water directory you created`
- Download the manual images (explain!)
- `.sh mkfile.sh` (this will take a long time)