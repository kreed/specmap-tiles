Python scripts that parse the [FCC ULS databases](http://wireless.fcc.gov/uls/index.htm?job=transaction&page=weekly) and generate GeoJSON geometries. Used with [specmap-frontend](https://bitbucket.org/ceby/specmap-frontend) to create a map of wireless spectrum owners. [Demo here](http://kreed.org/specmap/)

#### Dependencies ####
* Python 3
* python-shapely
* python-geojson
* gdal
* sqlite3
#### Usage ####

Run fetch.sh to download FCC data and import into SQLite databases

Use ```./run.py [spectrum block]``` to create GeoJSON for a specific spectrum block and channel. For example ./run.py AWS1A will create AWS1A.geojson, containing geometries for all AWS1 block A markets. See table at the top of run.py for a list of supported spectrum blocks.
