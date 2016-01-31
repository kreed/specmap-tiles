#!/usr/bin/env python3

import geojson
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

with open('geoms.py', 'w') as f:
	f.write('market_geoms = ')
	geojson.dump(market_geoms, f)
	f.write('\ncounty_geoms = ')
	geojson.dump(county_geoms, f)
