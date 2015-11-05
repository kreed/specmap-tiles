#!/usr/bin/env python3

import geojson
import re
import sqlite3
import sys
import shapely.ops
from geoms import county_geoms, market_geoms
from shapely.geometry import mapping, shape

from pprint import pprint

radio_service = sys.argv[1]
block = sys.argv[2]
result = []

con = sqlite3.connect("l_market.sqlite")
cur = con.cursor()

def canon_owner(owner):
	if owner.startswith('USCOC') or owner == 'King Street Wireless, LP' or owner == 'UNITED STATES CELLULAR OPERATING COMPANY LLC' or owner == 'CARROLL WIRELESS, LP':
		return 'US Cellular'
	if owner == 'T-Mobile License LLC' or owner == 'T-MOBILE LICENSE LLC':
		return 'T-Mobile'
	if owner == 'AT & T Mobility Spectrum LLC' or owner == 'AT&T Mobility Spectrum LLC' or owner == 'New Cingular Wireless PCS, LLC':
		return 'AT&T'
	if owner.startswith('Cavalier'):
		return 'Cavalier'
	if owner.startswith('C700'):
		return 'Continuum 700'
	if owner == 'Cellular South Licenses, LLC':
		return 'C Spire'
	if owner == 'Cellco Partnership' or owner == 'Verizon Wireless (VAW) LLC' or owner == 'Alltel Communications, LLC':
		owner = 'Verizon'
	return owner

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

def feature_props(call_sign, owner, market, population):
	props = {
		'market': market,
		'call_sign': call_sign,
		'population': '{:,}'.format(int(population)),
		'owner': canon_owner(owner),
	}
	if props['owner'] in color_table:
		props['fill'] = color_table[props['owner']]
	return props

def parse_dms(d, m, s, direc):
	r = float(d) + float(m)/60 + float(s)/3600
	r = r * (-1 if direc in ('S', 'W') else 1)
	return round(r, 6)

def lookup_county(fips):
	if fips == '02231':
		codes = '02282','02105','02230'
	elif fips == '02201':
		codes = '02198','02275'
	elif fips == '02280':
		codes = '02195',
	elif fips == '51560':
		# merged with 51005
		codes = ()
	elif fips == '51780':
		# merged with 51083
		codes = ()
	elif fips == '51515':
		# merged with 51019
		codes = ()
	elif fips == '12025':
		codes = '12086',
	else:
		codes = fips,
	return [ shape(county_geoms[f]) for f in codes ]

q = cur.execute("SELECT call_sign, entity_name, market_code, population, sum(defined_area_population) FROM HD JOIN EN USING (call_sign) JOIN MK USING (call_sign) LEFT OUTER JOIN MP USING (call_sign) WHERE license_status='A' AND radio_service_code=? AND channel_block=? AND entity_type='L' AND cancellation_date='' AND NOT call_sign LIKE 'L%' GROUP BY call_sign", (radio_service, block))
for row in q.fetchall():
	call_sign, owner, market, population, part_pop = row

	if part_pop == None:
		# unpartitioned market
		geom = market_geoms[market]
	else:
		add_parts = []
		sub_parts = []

		q = cur.execute('SELECT market_partition_code, defined_partition_area, include_exclude_ind, partitioned_seq_num, def_und_ind FROM MP WHERE call_sign=?', (call_sign,))
		for row in q.fetchall():
			part_market, area_name, inc_exc, part_seq, def_und = row

			if def_und == 'D':
				if inc_exc == 'I':
					match = re.match('(\d{5}): .*', area_name)
					if match:
						if not match.group(1) in county_geoms:
							print(call_sign, *row)
						add_parts = add_parts + lookup_county(match.group(1))
					else:
						print('non-county partition', row, file=sys.stderr)
						add_parts.append(shape(market_geoms[part_market]))
				else:
					print('FIXME: defined exclude not implemeted', file=sys.stderr)
					sys.exit(-1)
			else:
				points = []
				for row in cur.execute('SELECT partition_lat_degrees, partition_lat_minutes, partition_lat_seconds, partition_lat_direction, partition_long_degrees, partition_long_minutes, partition_long_seconds, partition_long_direction, partition_sequence_number FROM MC WHERE call_sign=? AND undefined_partitioned_area=? ORDER BY partition_sequence_number', (call_sign, part_seq)):
					lat = parse_dms(*row[0:4])
					lng = parse_dms(*row[4:8])
					points.append((lng, lat))
				points.append(points[0])
				f = shape(geojson.Polygon([points]))
				if not f.is_valid:
					print(call_sign, part_seq, 'invalid geometry', file=sys.stderr)
					f = f.buffer(0)
				if inc_exc == 'I':
					add_parts.append(f)
				else:
					sub_parts.append(f)

		geom = shapely.ops.unary_union(add_parts)
		if len(sub_parts):
			sub_merged = shapely.ops.unary_union(sub_parts)
			geom = geom.difference(sub_merged)
		geom = mapping(geom)
		population = part_pop

	props = feature_props(call_sign, owner, market, population)
	result.append(geojson.Feature(properties=props, geometry=geom))

def filename(rd, block):
	if rd == 'WY' or rd == 'WZ':
		name = '700'
	elif rd == 'WU':
		name = '700U'
	elif rd == 'AW':
		name = 'AWS'
	return name + block + '.geojson'

result = geojson.FeatureCollection(result)
with open(filename(radio_service, block), 'w') as out:
	geojson.dump(result, out)

con.commit()
con.close()


