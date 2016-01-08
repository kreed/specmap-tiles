#!/usr/bin/env python3

import geojson
import os
import re
import sqlite3
import sys
import shapely.ops
from geoms import county_geoms, market_geoms
from shapely.geometry import mapping, shape, GeometryCollection, MultiPolygon, Polygon
from specrange import SpectrumRange, SpectrumRanges

from pprint import pprint

radio_service_map = {
	'700LA': ('WY', 'A', SpectrumRange(698,704), SpectrumRange(728,734)),
	'700LB': ('WY', 'B', SpectrumRange(704,710), SpectrumRange(734,740)),
	'700LC': ('WZ', 'C', SpectrumRange(710,716), SpectrumRange(740,746)),
	'700UC': ('WU', 'C', SpectrumRange(746,757), SpectrumRange(776,787)),
	'AWS1A': ('AW', 'A', SpectrumRange(1710,1720), SpectrumRange(2110,2120)),
	'AWS1B': ('AW', 'B', SpectrumRange(1720,1730), SpectrumRange(2120,2130)),
	'AWS1C': ('AW', 'C', SpectrumRange(1730,1735), SpectrumRange(2130,2135)),
	'AWS1D': ('AW', 'D', SpectrumRange(1735,1740), SpectrumRange(2135,2140)),
	'AWS1E': ('AW', 'E', SpectrumRange(1740,1745), SpectrumRange(2140,2145)),
	'AWS1F': ('AW', 'F', SpectrumRange(1745,1755), SpectrumRange(2145,2155)),
	'AWS3G': ('AT', 'G', SpectrumRange(1755,1760), SpectrumRange(2155,2160)),
	'AWS3H': ('AT', 'H', SpectrumRange(1760,1765), SpectrumRange(2160,2165)),
	'AWS3I': ('AT', 'I', SpectrumRange(1765,1770), SpectrumRange(2165,2170)),
	'AWS3J': ('AT', 'J', SpectrumRange(1770,1780), SpectrumRange(2170,2180)),
	'PCSA': ('CW', 'A', SpectrumRange(1850,1865), SpectrumRange(1930,1945)),
	'PCSD': ('CW', 'D', SpectrumRange(1865,1870), SpectrumRange(1945,1950)),
	'PCSB': ('CW', 'B', SpectrumRange(1870,1885), SpectrumRange(1950,1965)),
	'PCSE': ('CW', 'E', SpectrumRange(1885,1890), SpectrumRange(1965,1970)),
	'PCSF': ('CW', 'F', SpectrumRange(1890,1895), SpectrumRange(1970,1975)),
	'PCSC': ('CW', 'C', SpectrumRange(1895,1910), SpectrumRange(1975,1990)),
	'PCSG': ('CY', 'G', SpectrumRange(1910,1915), SpectrumRange(1990,1995)),
	'WCSA': ('WS', 'A', SpectrumRange(2305,2310), SpectrumRange(2350,2355)),
	'WCSB': ('WS', 'B', SpectrumRange(2310,2315), SpectrumRange(2355,2360)),
}

filename = sys.argv[1]
radio_service = os.path.basename(filename).replace('.geojson', '')
radio_service_code, block_code, uplink_range, downlink_range = radio_service_map[radio_service]

result = []

con = sqlite3.connect(os.path.dirname(os.path.realpath(__file__)) + "/l_market.sqlite")
cur = con.cursor()

def owner_dba(owner, email):
	owner, email = owner.lower(), email.lower()

	if email.endswith('t-mobile.com'):
		return 'T-Mobile'
	if email.endswith('verizonwireless.com'):
		return 'Verizon'
	if email.endswith('att.com'):
		return 'AT&T'
	if email.endswith('sprint.com'):
		return 'Sprint'
	if email.endswith('wcc.net'):
		return 'West Central Wireless'
	if email.endswith('cellonenation.com'):
		return 'Cellular One (Chinook)'
	if email.endswith('dish.com') or email.endswith('dishnetwork.com'):
		return 'Dish Network'

	if owner.startswith('wirelessco') or 'sprint' in owner or 'nextel' in owner:
		return 'Sprint'
	if 'at&t' in owner or 'a t & t' in owner or 'cingular' in owner:
		return 'AT&T'
	if 't-mobile' in owner:
		return 'T-Mobile'
	if owner == 'cellco partnership' or 'verizon' in owner or 'alltell' in owner:
		return 'Verizon'
	if owner.startswith('uscoc') or 'united states cellular' in owner or 'king street wireless' in owner or 'carroll wireless' in owner or 'barat wireless' in owner or owner == 'hardy cellular telephone company':
		return 'US Cellular'
	if 'cellular south' in owner:
		return 'C Spire'
	if 'iowa wireless' in owner:
		return 'iWireless'
	if 'snr wireless' in owner or 'northstar wireless' in owner:
		return 'Dish Network'
	if owner.startswith('cavalier'):
		return 'Cavalier'
	if owner.startswith('c700'):
		return 'Continuum 700'
	if 'grain spectrum' in owner:
		return 'Grain Spectrum'
	if 'ab license co' in owner:
		return 'AB License Co'
	if 'ct cube' in owner or 'central texas telephone' in owner:
		return 'West Central Wireless'
	if 'infrastructure networks' in owner:
		return 'Infrastructure Networks'
	if 'alaska wireless network' in owner:
		return 'GCI'
	if 'mta communications' in owner:
		return 'MTA Communications'
	if 'north dakota network' in owner:
		return 'SRT Communications'
	if 'bluegrass' in owner:
		return 'Bluegrass Cellular'
	if 'east kentucky network' in owner or 'appalachian wireless' in owner:
		return 'Appalachian Wireless'
	if 'nemont communications' in owner:
		return 'Nemont'
	return None

color_table = {
	'T-Mobile': '#ff00ff',
	'iWireless': '#ff9cff',
	'C Spire': '#208dd9',
	'AT&T': '#00FFFF',
	'US Cellular': '#A5CCE8',
	'AB License Co': '#00ff00',
	'Cavalier': '#009E60',
	'Continuum 700': '#BFFF00',
	"Sprint": '#FFFF00',
	"Verizon": '#ff0000',
	'Dish Network': '#ff7794',
}

def feature_props(uls_no, call_sign, owner, email, market, population, freq):
	props = {
		'block': radio_service,
		'market': market,
		'uls_number': uls_no,
		'call_sign': call_sign,
		'owner': owner,
	}

	if population:
		props['population'] = '{:,}'.format(int(population))

	downlink = freq.findwithin(downlink_range)
	if downlink:
		props['downlink'] = downlink
	uplink = freq.findwithin(uplink_range)
	if uplink:
		props['uplink'] = uplink

	dba = owner_dba(owner, email)
	if dba:
		props['owner_dba'] = dba
		if dba in color_table:
			props['fill'] = color_table[dba]

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
q = cur.execute(q, (radio_service_code, block_code))
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

			if def_und == 'D':
				assert inc_exc == 'I', "defined exclude not implemented"
				match = re.match('(\d{5}): .*', area_name)
				if match:
					assert match.group(1) in county_geoms, "missing county %s %s %s" % (call_sign, part_market, area_name)
					geom = shape(county_geoms[match.group(1)])
				else:
					geom = shape(market_geoms[part_market])
			else:
				part_pop = None
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
		pops = [ p[1] for p in parts ]
		pop = None if None in pops else sum(pops)
		freqs[freq] = (geom, pop)

	for freq, parts in sub_parts.items():
		geom = shapely.ops.unary_union([ p[0] for p in parts ])

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
						freqs[add_freq] = (add_geom.union(intersection), None)
					else:
						freqs[add_freq] = (remaining_geom, None)

				parent_geom, parent_pop = freqs[f]
				freqs[f] = (parent_geom.difference(remaining_geom), None)

				remaining_geom = remaining_geom.difference(parent_geom)
				if remaining_geom.area / geom.area < .01:
					break

		if intersects > 1:
			print(uls_no, call_sign, 'intersects:', intersects)

		if remaining_geom.area / geom.area >= .01:
			print(uls_no, call_sign, "large remaining exclude geometry (%.3f%% of original area)" % (100 * remaining_geom.area / geom.area))

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


