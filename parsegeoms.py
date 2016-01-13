#!/usr/bin/env python3

# Usage: ./parsegeoms.py > geoms.py

import geojson
import shapely.ops
import sys
from collections import defaultdict
from shapely.geometry import mapping, shape

with open('cnty1990.geojson') as counties_file:
	counties = geojson.load(counties_file)

county_geoms = {}
markets = defaultdict(list)

for county in counties.features:
	p = county.properties
	fips = p['FIPS']

	county_geoms[fips] = county.geometry

	cma = 'CMA%03d' % int(p['CMA'])
	markets[cma].append(p['FIPS'])

	bea = 'BEA%03d' % int(p['BEA'])
	markets[bea].append(p['FIPS'])

	rea = 'REA%03d' % int(p['REA'])
	markets[rea].append(p['FIPS'])

	mea = 'MEA%03d' % int(p['MEA'])
	markets[mea].append(p['FIPS'])

	bta = 'BTA%03d' % int(p['BTA'])
	markets[bta].append(p['FIPS'])

	mta = 'MTA%03d' % int(p['MTA'])
	markets[mta].append(p['FIPS'])

	eag = 'EAG%03d' % int(p['EAG'])
	markets[eag].append(p['FIPS'])

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

cell_geoms = {}

for filename in ('A_Block_CGSA.geojson', 'B_Block_CGSA.geojson'):
	with open(filename) as cell_file:
		cells = geojson.load(cell_file)

		for cell in cells.features:
			if cell.properties['VERSION'] == 'Current':
				call_sign = cell.properties['CALL_SIGN']
				if call_sign in cell_geoms:
					cell_geoms[call_sign] = mapping(shape(cell.geometry).union(shape(cell_geoms[call_sign])))
				else:
					cell_geoms[call_sign] = cell.geometry

print('cell_geoms =', geojson.dumps(cell_geoms))
