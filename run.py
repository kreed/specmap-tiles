#!/usr/bin/env python3

import geojson
import os
import re
import sqlite3
import sys
import shapely.ops
from geoms import county_geoms, market_geoms
from shapely.geometry import mapping, shape, GeometryCollection, MultiPolygon, Polygon
from specrange import SpectrumRanges

from pprint import pprint

radio_service_map = {
	'700LA': ('WY', 'A'),
	'700LB': ('WY', 'B'),
	'700LC': ('WZ', 'C'),
	'700UC': ('WU', 'C'),
	'AWS1A': ('AW', 'A'),
	'AWS1B': ('AW', 'B'),
	'AWS1C': ('AW', 'C'),
	'AWS1D': ('AW', 'D'),
	'AWS1E': ('AW', 'E'),
	'AWS1F': ('AW', 'F'),
	'AWS3G': ('AT', 'G'),
	'AWS3H': ('AT', 'H'),
	'AWS3I': ('AT', 'I'),
	'AWS3J': ('AT', 'J'),
	'PCSA': ('CW', 'A'),
	'PCSB': ('CW', 'B'),
	'PCSC': ('CW', 'C'),
	'PCSD': ('CW', 'D'),
	'PCSE': ('CW', 'E'),
	'PCSF': ('CW', 'F'),
	'PCSG': ('CY', 'G'),
}

filename = sys.argv[1]
x = radio_service_map[os.path.basename(filename).replace('.geojson', '')]
radio_service, block = x[:2]

result = []

con = sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + "/l_market.sqlite")
cur = con.cursor()

def canon_owner(owner, email):
	owner, email = owner.lower(), email.lower()

	if email.endswith('t-mobile.com'):
		return 'T-Mobile'
	if email.endswith('verizonwireless.com'):
		return 'Verizon'
	if email.endswith('att.com'):
		return 'AT&T'
	if email.endswith('sprint.com'):
		return 'Sprint'

	if owner.startswith('uscoc') or owner == 'king street wireless, lp' or owner == 'united states cellular operating company llc' or owner == 'carroll wireless, lp' or owner == 'barat wireless, l.p.' or owner == 'hardy cellular telephone company':
		return 'US Cellular'
	if owner.startswith('wirelessco') or 'sprint' in owner:
		return 'Sprint'
	if 't-mobile' in owner:
		return 'T-Mobile'
	if 'iowa wireless' in owner:
		return 'iWireless'
	if 'at&t' in owner or 'a t & t' in owner or 'cingular' in owner:
		return 'AT&T'
	if owner.startswith('cavalier'):
		return 'Cavalier'
	if owner.startswith('c700'):
		return 'Continuum 700'
	if owner == 'cellular south licenses, llc':
		return 'C Spire'
	if owner == 'cellco partnership' or 'verizon' in owner or 'alltell' in owner:
		return 'Verizon'
	if owner == 'snr wireless licenseco, llc' or owner == 'northstar wireless, llc':
		return 'Dish Network'
	return None

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

def feature_props(uls_no, call_sign, owner, email, market, population, freq):
	props = {
		'market': market,
		'uls_number': uls_no,
		'call_sign': call_sign,
		'population': '{:,}'.format(int(population)),
		'owner': owner,
		'downlink': freq.downlink(),
		'uplink': freq.uplink(),
	}

	common = canon_owner(owner, email)
	if common:
		props['owner_common_name'] = common
		if common in color_table:
			props['fill'] = color_table[common]

	return props

def parse_dms(d, m, s, direc):
	r = float(d) + float(m)/60 + float(s)/3600
	r = r * (-1 if direc in ('S', 'W') else 1)
	return round(r, 6)

def approx_within(needle, haystack):
	""" test if most of needle (>99.5%) is inside haystack """
	return needle.difference(haystack).area / needle.area < .005

q = ("SELECT HD.unique_system_identifier, call_sign, entity_name, email, market_code, population, submarket_code "
	"FROM HD JOIN EN USING (call_sign) JOIN MK USING (call_sign)"
	"WHERE radio_service_code=? AND channel_block=? "  # select the given spectrum block
	"AND entity_type='L' "                             # we want the owner (L), not the contact (CL)
	"AND license_status='A' AND cancellation_date='' " # exclude inactive licenses
	"AND NOT call_sign LIKE 'L%' "                     # exclude leases
	"AND NOT market_code IN ('REA012', 'CMA306', 'BEA176', 'MEA052')") # exclude Gulf of Mexico
q = cur.execute(q, (radio_service, block))
for uls_no, call_sign, owner, email, market, market_pop, submarket_code in q.fetchall():
	print(uls_no, call_sign)

	q = ("SELECT partitioned_seq_num, def_und_ind, GROUP_CONCAT(lower_frequency||'-'||upper_frequency) FROM MF WHERE call_sign=? GROUP BY partitioned_seq_num, def_und_ind")
	q = cur.execute(q, (call_sign,)).fetchall()

	if len(q) == 0:
		print(uls_no, call_sign, "no frequencies given")
		continue

	if [ seq_num for seq_num, def_und, freq in q if seq_num.startswith('ISA') ]:
		# need geo data for Iowa Study Areas
		print(uls_no, call_sign, "skipping Iowa Study Area")
		continue

	if submarket_code == 0:
		assert len(q) == 1, "%s submarket_code is 0 but license has multiple partitions" % call_sign
		props = feature_props(uls_no, call_sign, owner, email, market, market_pop, SpectrumRanges.fromstr(q[0][2]))
		result.append(geojson.Feature(properties=props, geometry=market_geoms[market]))
		continue

	add_parts = {}
	sub_parts = {}

	for seq_num, def_und, freq in q:
		freq = SpectrumRanges.fromstr(freq)

		q = ('SELECT market_partition_code, defined_partition_area, defined_area_population, include_exclude_ind FROM MP WHERE call_sign=? AND partitioned_seq_num=? AND def_und_ind=?')
		q = cur.execute(q, (call_sign, seq_num, def_und)).fetchall()

		assert len(q) > 0, "no partition info %s %s %s" % (call_sign, seq_num, def_und)
		for part_market, area_name, part_pop, inc_exc in q:
			if part_pop == '':
				part_pop = 0

			if def_und == 'D':
				assert inc_exc == 'I', "defined exclude not implemented"
				match = re.match('(\d{5}): .*', area_name)
				if match:
					assert match.group(1) in county_geoms, "missing county %s %s %s" % (call_sign, part_market, area_name)
					geom = shape(county_geoms[match.group(1)])
				else:
					geom = shape(market_geoms[part_market])
			else:
				points = []
				for row in cur.execute('SELECT partition_lat_degrees, partition_lat_minutes, partition_lat_seconds, partition_lat_direction, partition_long_degrees, partition_long_minutes, partition_long_seconds, partition_long_direction, partition_sequence_number FROM MC WHERE call_sign=? AND undefined_partitioned_area=? ORDER BY partition_sequence_number', (call_sign, seq_num)):
					lat = parse_dms(*row[0:4])
					lng = parse_dms(*row[4:8])
					points.append((lng, lat))
				points.append(points[0])
				geom = shape(geojson.Polygon([points]))
				if not geom.is_valid:
					print(uls_no, call_sign, 'invalid geometry, partition', seq_num)
					geom = geom.buffer(0)

			dest_list = add_parts if inc_exc == 'I' else sub_parts
			if not freq in dest_list:
				dest_list[freq] = []
			dest_list[freq].append((geom, part_pop))

	assert len(add_parts) > 0, "no geometries included %s" % call_sign

	freqs = {}

	for freq, parts in add_parts.items():
		geom = shapely.ops.unary_union([ p[0] for p in parts ])
		pop = sum([ p[1] for p in parts ])
		freqs[freq] = (geom, pop)

	for freq, parts in sub_parts.items():
		geom = shapely.ops.unary_union([ p[0] for p in parts ])
		pop = sum([ p[1] for p in parts ])

		intersects = 0
		remaining_geom = geom
		for f in list(freqs.keys()):
			if not f.contains(freq):
				continue

			intersection = remaining_geom.intersection(freqs[f][0])
			if intersection.area / geom.area > .01:
				intersects += 1

				if f != freq:
					add_freq = f.difference(freq)
					if add_freq in freqs:
						add_geom, add_pop = freqs[add_freq]
						freqs[add_freq] = (add_geom.union(intersection), add_pop + pop)
					else:
						freqs[add_freq] = (remaining_geom, pop)

				parent_geom, parent_pop = freqs[f]
				freqs[f] = (parent_geom.difference(remaining_geom), parent_pop - pop)

				remaining_geom = remaining_geom.difference(parent_geom)
				if remaining_geom.area / geom.area < .01:
					break

		if remaining_geom.area / geom.area >= .01:
			with open('rem.geojson', 'w') as out:
				features = geojson.FeatureCollection([ geojson.Feature(properties={'freq':str(e[0])},geometry=mapping(e[1][0])) for e in [(freq,(remaining_geom,pop))]])
				geojson.dump(features, out)

		if intersects > 1:
			print(uls_no, call_sign, 'intersects:', intersects)

		if uls_no != 8938: # this license has some bogus geodata with a large overlapping area
			assert remaining_geom.area / geom.area < .01, "large remaining geom %s %s" % (uls_no, call_sign)

	for freq, part in freqs.items():
		geom, population = part

		if type(geom) is GeometryCollection:
			print(uls_no, call_sign, "removing non-polygons from geometry")
			geom = MultiPolygon([ p for p in geom if type(p) is Polygon ])

		props = feature_props(uls_no, call_sign, owner, email, market, population, freq)
		result.append(geojson.Feature(properties=props, geometry=mapping(geom)))

result = geojson.FeatureCollection(result)
with open(filename, 'w') as out:
	geojson.dump(result, out)

con.commit()
con.close()


