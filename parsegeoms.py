#!/usr/bin/env python3

# Usage: ./parsegeoms.py > geoms.py

import geojson
import shapely.ops
import sys
from shapely.geometry import mapping, shape

with open('cnty1990.geojson') as counties_file:
	counties = geojson.load(counties_file)

county_geoms = {}
markets = {}

for county in counties.features:
	p = county.properties
	fips = p['FIPS']

	county_geoms[fips] = county.geometry

	cma = 'CMA%03d' % int(p['CMA'])
	if not cma in markets:
		markets[cma] = []
	markets[cma].append(p['FIPS'])

	bea = 'BEA%03d' % int(p['BEA'])
	if not bea in markets:
		markets[bea] = []
	markets[bea].append(p['FIPS'])

	rea = 'REA%03d' % int(p['REA'])
	if not rea in markets:
		markets[rea] = []
	markets[rea].append(p['FIPS'])

	mea = 'MEA%03d' % int(p['MEA'])
	if not mea in markets:
		markets[mea] = []
	markets[mea].append(p['FIPS'])

market_geoms = {}

for market, mcounties in markets.items():
	features = []
	for fips in mcounties:
		if fips in county_geoms:
			features.append(shape(county_geoms[fips]))
		else:
			print('missing', fips)
	merged = shapely.ops.unary_union(features)
	market_geoms[market] = mapping(merged)

print('market_geoms =', geojson.dumps(market_geoms))
print('county_geoms =', geojson.dumps(county_geoms))
