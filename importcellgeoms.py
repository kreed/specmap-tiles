#!/usr/bin/env python3

import geojson
from shapely.geometry import mapping, shape

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

with open('cellgeoms.py', 'w') as f:
	f.write('\ncell_geoms = ')
	geojson.dump(cell_geoms, f)
