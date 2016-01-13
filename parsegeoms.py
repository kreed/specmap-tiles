#!/usr/bin/env python3

import geojson
import sys
from collections import defaultdict
from shapely.ops import unary_union
from shapely.geometry import mapping, shape

with open('cnty1990.geojson') as counties_file:
	counties = geojson.load(counties_file)

county_geoms = {}
markets = defaultdict(list)

for county in counties.features:
	p = county.properties
	fips = p['FIPS']

	county_geoms[fips] = county.geometry

	for market_type in ('CMA', 'BEA', 'REA', 'MEA', 'BTA', 'MTA', 'EAG'):
		code = '%s%03d' % (market_type, int(p[market_type]))
		markets[code].append(fips)

market_geoms = {}

for market, mcounties in markets.items():
	merged = unary_union([ shape(county_geoms[fips]) for fips in mcounties ])
	market_geoms[market] = mapping(merged)

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

with open('geoms.py', 'w') as f:
	f.write('market_geoms = ')
	geojson.dump(market_geoms, f)
	f.write('\ncounty_geoms = ')
	geojson.dump(county_geoms, f)
	f.write('\ncell_geoms = ')
	geojson.dump(cell_geoms, f)
