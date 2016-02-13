#!/bin/bash
url=http://wireless.fcc.gov/uls/data/complete
files='l_market.zip l_cell.zip l_mdsitfs.zip'

for i in $files; do
	wget -N $url/$i
done

url=http://wireless.fcc.gov/services/cellular
files='A_Block_CGSA B_Block_CGSA'

for i in $files; do
	rm -rf $i $i.geojson
	wget -N $url/$i.zip
	unzip -d $i $i.zip
	ogr2ogr -f geojson $i.geojson $i/$i.shp
	rm -r $i
done

./importcellgeoms.py
./import.py
