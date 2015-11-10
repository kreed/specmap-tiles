#!/usr/bin/env python3

import geojson
import re
import sqlite3
import sys
import shapely.ops
from geoms import county_geoms, market_geoms
from shapely.geometry import mapping, shape

from pprint import pprint

filename = sys.argv[1]
filename = filename.replace('.geojson', '')

radio_service_map = {
	'700LA': ('WY', 'A'),
	'700LB': ('WY', 'B'),
	'700LC': ('WZ', 'C'),
	'700UC': ('WU', 'C'),
	'AWS1A': ('AW', 'A'),
	'AWS1A1': ('AW', 'A', 1712.5),
	'AWS1A2': ('AW', 'A', 1717.5),
	'AWS1B': ('AW', 'B'),
	'AWS1B1': ('AW', 'B', 1722.5),
	'AWS1B2': ('AW', 'B', 1727.5),
	'AWS1C': ('AW', 'C'),
	'AWS1D': ('AW', 'D'),
	'AWS1E': ('AW', 'E'),
	'AWS1F': ('AW', 'F'),
	'AWS1F1': ('AW', 'F', 1747.5),
	'AWS1F2': ('AW', 'F', 1752.5),
	'AWS3G': ('AT', 'G'),
	'AWS3H': ('AT', 'H'),
	'AWS3I': ('AT', 'I'),
	'AWS3J1': ('AT', 'J', 1772.5),
	'AWS3J2': ('AT', 'J', 1777.5),
}

x = radio_service_map[filename]
radio_service, block = x[:2]
center_freq = x[2] if len(x) == 3 else None

result = []

con = sqlite3.connect("l_market.sqlite")
cur = con.cursor()

def canon_owner(owner):
	if owner.startswith('USCOC') or owner == 'King Street Wireless, LP' or owner == 'UNITED STATES CELLULAR OPERATING COMPANY LLC' or owner == 'CARROLL WIRELESS, LP' or owner == 'BARAT WIRELESS, L.P.':
		return 'US Cellular'
	if owner == 'T-Mobile License LLC' or owner == 'T-MOBILE LICENSE LLC':
		return 'T-Mobile'
	if owner == 'Iowa Wireless Services Holding Corporation':
		owner = 'iWireless'
	if owner == 'AT & T Mobility Spectrum LLC' or owner == 'AT&T Mobility Spectrum LLC' or owner == 'New Cingular Wireless PCS, LLC' or owner == 'AT&T Wireless Services 3 LLC':
		return 'AT&T'
	if owner.startswith('Cavalier'):
		return 'Cavalier'
	if owner.startswith('C700'):
		return 'Continuum 700'
	if owner == 'Cellular South Licenses, LLC':
		return 'C Spire'
	if owner == 'Cellco Partnership' or owner == 'Verizon Wireless (VAW) LLC' or owner == 'Alltel Communications, LLC':
		owner = 'Verizon'
	if owner == 'SNR Wireless LicenseCo, LLC' or owner == 'Northstar Wireless, LLC':
		owner = 'Dish Network'
	return owner

color_table = {
	'T-Mobile': '#ff00ff',
	'iWireless': '#ff9cff',
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
	'Dish Network': '#ff7794',
}

def feature_props(uls_no, call_sign, owner, market, population):
	props = {
		'market': market,
		'uls_number': uls_no,
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

q = ("SELECT HD.unique_system_identifier, call_sign, entity_name, market_code, population, sum(defined_area_population) "
	"FROM HD JOIN EN USING (call_sign) JOIN MK USING (call_sign) LEFT OUTER JOIN MP USING (call_sign) " +
	("JOIN MF USING (call_sign) WHERE lower_frequency<{0} AND upper_frequency>{0} AND ".format(center_freq) if center_freq else "WHERE ") +
	"license_status='A' AND radio_service_code=? AND channel_block=? AND entity_type='L' AND cancellation_date='' AND NOT call_sign LIKE 'L%' "
	"GROUP BY call_sign")
q = cur.execute(q, (radio_service, block))
for row in q.fetchall():
	uls_no, call_sign, owner, market, population, part_pop = row

	if market in ('REA012', 'CMA306', 'BEA176', 'MEA052'):
		# Gulf of Mexico
		continue

	if part_pop == None:
		# unpartitioned market
		geom = market_geoms[market]
	else:
		add_parts = []
		sub_parts = []

		q = ('SELECT market_partition_code, defined_partition_area, include_exclude_ind, partitioned_seq_num, MP.def_und_ind FROM MP ' +
			("JOIN MF USING (call_sign, partitioned_seq_num) WHERE lower_frequency<{0} AND upper_frequency>{0} AND ".format(center_freq) if center_freq else "WHERE ") +
			'call_sign=?')
		q = cur.execute(q, (call_sign,))
		for row in q.fetchall():
			part_market, area_name, inc_exc, part_seq, def_und = row

			if def_und == 'D':
				if inc_exc == 'I':
					match = re.match('(\d{5}): .*', area_name)
					if match:
						if not match.group(1) in county_geoms:
							print(call_sign, *row)
						add_parts.append(shape(county_geoms[match.group(1)]))
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

	props = feature_props(uls_no, call_sign, owner, market, population)
	result.append(geojson.Feature(properties=props, geometry=geom))

result = geojson.FeatureCollection(result)
with open(filename + '.geojson', 'w') as out:
	geojson.dump(result, out)

con.commit()
con.close()


