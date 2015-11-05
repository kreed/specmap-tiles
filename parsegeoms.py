#!/usr/bin/env python3

# Usage: ./parsegeoms.py > geoms.py

import geojson
import shapely.ops
import sys
from markets import markets
from shapely.geometry import mapping, shape

with open('gz_2010_us_050_00_5m.json') as counties_file:
	counties = geojson.load(counties_file)

county_geoms = {}

for county in counties.features:
	fips = county.properties['STATEFP'] + county.properties['COUNTYFP']
	county_geoms[fips] = county.geometry

market_geoms = {}

for market, mcounties in markets.items():
	features = []
	for fips in mcounties:
		if fips.startswith('99'):
			# Gulf of Mexico
			pass
		elif fips in county_geoms:
			features.append(shape(county_geoms[fips]))
		else:
			print('missing', fips)
	merged = shapely.ops.unary_union(features)
	market_geoms[market] = mapping(merged)

print('market_geoms =', geojson.dumps(market_geoms))
print('county_geoms =', geojson.dumps(county_geoms))
