rm -rf water
mkdir water

curl -L  "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_ocean.zip" > tmp.zip
unzip tmp.zip -d "water"
rm -f tmp.zip

curl -L  "http://geodata.utc.edu/datasets/48c77cbde9a0470fb371f8c8a8a7421a_0.zip" > tmp.zip
unzip tmp.zip -d "water"
rm -f tmp.zip


