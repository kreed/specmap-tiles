#!/usr/bin/env python3

import geojson
import pickle
import sys
from pprint import pprint

color_table = {
	'T-Mobile': '#ff00ff',
	'C Spire': '#208dd9',
	'AT&T': '#00FFFF',
	'Leap Licenseco Inc.': '#00FFFF',
	'Horry Telephone Cooperative, Inc.': '#00FFFF',
	'US Cellular': '#A5CCE8',
	'AB License Co LLC': '#00ff00',
	'Cavalier': '#009E60',
	'Continuum 700': '#BFFF00',
	"Sprint": '#FFFF00',
	"Verizon": '#ff0000',
}

block = sys.argv[1]

with open('700%s.pickle' % block, 'rb') as dump:
	owners = pickle.load(dump)

with open('gz_2010_us_050_00_5m.json') as counties_file:
	counties = geojson.load(counties_file)

for i in reversed(range(len(counties.features))):
	county = counties.features[i]
	fips = county.properties['STATEFP'] + county.properties['COUNTYFP']
	try:
		county.properties = owners[fips]
		county.properties['population'] = '{:,}'.format(int(county.properties['population']))
		if county.properties['owner'] in color_table:
			county.properties['fill'] = color_table[county.properties['owner']]
	except KeyError:
		print('missing', fips)
		del counties.features[i]

with open('700%s.geojson' % block, 'w') as out:
	geojson.dump(counties, out)
