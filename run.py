#!/usr/bin/env python3

import geojson
import os
import re
import sqlite3
import sys
from collections import defaultdict
from common_names import frn_table
from geoms import county_geoms, market_geoms, cell_geoms
from partcollection import PartitionCollection
from shapely.geometry import mapping, shape, GeometryCollection, MultiPolygon, Polygon
from specrange import SpectrumRange, SpectrumRanges

radio_service_map = {
	'700LA': ('WY', 'A', SpectrumRange(698,704), SpectrumRange(728,734)),
	'700LB': ('WY', 'B', SpectrumRange(704,710), SpectrumRange(734,740)),
	'700LC': ('WZ', 'C', SpectrumRange(710,716), SpectrumRange(740,746)),
	'700LD': ('WZ', 'D', None, SpectrumRange(716,722)),
	'700LE': ('WY', 'E', None, SpectrumRange(722,728)),
	'700UC': ('WU', 'C', SpectrumRange(746,757), SpectrumRange(776,787)),
	'SMR': (('YC','YH'), None, SpectrumRange(814,824), SpectrumRange(859,869)),
	'CellA': ('CL', 'A', SpectrumRanges(((824,835), (845,846.5))), SpectrumRanges(((869,880), (890,891.5)))),
	'CellB': ('CL', 'B', SpectrumRanges(((835,845), (846.5,849))), SpectrumRanges(((880,890), (891.5,894)))),
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
	'AWSH': ('AH', 'H', SpectrumRange(1915,1920), SpectrumRange(1995,2000)),
	'AWS3A1': ('AT', 'A1', SpectrumRange(1695,1700), None),
	'AWS3B1': ('AT', 'B1', SpectrumRange(1700,1710), None),
	'AWS4A': ('AD', 'A', None, SpectrumRanges(((2000,2010), (2180,2190)))),
	'AWS4B': ('AD', 'B', None, SpectrumRanges(((2010,2020), (2190,2200)))),
	'WCSA': ('WS', 'A', SpectrumRange(2305,2310), SpectrumRange(2350,2355)),
	'WCSB': ('WS', 'B', SpectrumRange(2310,2315), SpectrumRange(2355,2360)),
	'BRS': ('BR', None, None, None, SpectrumRange(2496, 2690)),
}

db_name = 'l_market'
filename = sys.argv[1]
radio_service = os.path.basename(filename).replace('.geojson', '')
block_info = radio_service_map[radio_service]
radio_service_code, block_code, uplink_range, downlink_range = block_info[:4]
tdd_range = None
if radio_service == 'BRS':
	db_name = 'l_mdsitfs'
	tdd_range = block_info[4]
elif radio_service.startswith('Cell'):
	db_name = 'l_cell'

result = []

con = sqlite3.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)), db_name + '.sqlite'))
cur = con.cursor()

owner_colors = {
	'T-Mobile': '#ff00ff',
	'iWireless': '#ff9cff',
	'C Spire': '#208dd9',
	'AT&T': '#00FFFF',
	'US Cellular': '#A5CCE8',
	'Continuum C700': '#00ff00',
	'Cavalier': '#009E60',
	"Sprint": '#FFFF00',
	"Verizon": '#ff0000',
	'Dish Network': '#ff7794',
}

def feature_props(uls_no, call_sign, owner, frn, market, population, freq):
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
	tdd = freq.findwithin(tdd_range)
	if tdd:
		props['tdd'] = tdd

	if frn in frn_table:
		dba = frn_table[frn]
		props['owner_dba'] = dba
		if dba in owner_colors:
			props['fill'] = owner_colors[dba]

	return props

def parse_dms(d, m, s, direc):
	r = float(d) + float(m)/60 + float(s)/3600
	r = r * (-1 if direc in ('S', 'W') else 1)
	return round(r, 6)

q = ("SELECT HD.unique_system_identifier, call_sign, entity_name, frn, market_code, market_name, population, submarket_code "
	"FROM HD JOIN EN USING (call_sign) JOIN MK USING (call_sign)")
if radio_service == 'SMR':
	q += "WHERE radio_service_code IN ('" + "','".join(radio_service_code) + "') "
elif radio_service == 'BRS':
	q += "WHERE radio_service_code=? "
else:
	q += "WHERE radio_service_code=? AND channel_block=? "
q += ("AND entity_type='L' "                          # we want the owner (L), not the contact (CL)
	"AND license_status='A' "                          # active licenses
	"AND NOT call_sign LIKE 'L%' "                     # exclude leases
	"AND NOT market_code IN ('REA012', 'CMA306', 'BEA176', 'MEA052', 'BTA494', 'BTA495')") # exclude Gulf of Mexico
if radio_service == 'SMR':
	q = cur.execute(q)
elif radio_service == 'BRS':
	q = cur.execute(q, (radio_service_code,))
else:
	q = cur.execute(q, (radio_service_code, block_code))

for uls_no, call_sign, owner, frn, market, market_name, market_pop, submarket_code in q.fetchall():
	print(uls_no, call_sign)

	if radio_service.startswith('Cell'):
		freq = SpectrumRanges(uplink_range.ranges + downlink_range.ranges)
		if not call_sign in cell_geoms:
			print('missing CGSA geom')
			continue
		props = feature_props(uls_no, call_sign, owner, frn, market, None, freq)
		result.append(geojson.Feature(properties=props, geometry=cell_geoms[call_sign]))
		continue

	if radio_service == 'SMR' and submarket_code == 0:
		# SMR has different sequence numbers for each freqency pair even though each one covers the same area
		q = ("SELECT partitioned_seq_num, def_und_ind, GROUP_CONCAT(lower_frequency||'-'||upper_frequency) FROM MF WHERE call_sign=? GROUP BY def_und_ind")
	else:
		q = ("SELECT partitioned_seq_num, def_und_ind, GROUP_CONCAT(lower_frequency||'-'||upper_frequency) FROM MF WHERE call_sign=? GROUP BY partitioned_seq_num, def_und_ind")
	q = cur.execute(q, (call_sign,)).fetchall()

	if len(q) == 0:
		print(uls_no, call_sign, "no frequencies given")
		continue

	if market_name == 'P35 GSA':
		# 35 mile radius around a coordinate. These are tiny, and seem to overlap with BTA markets, so just skip them for now.
		continue

	if [ seq_num for seq_num, def_und, freq in q if seq_num.startswith('ISA') ]:
		# need geo data for Iowa Study Areas
		print(uls_no, call_sign, "skipping Iowa Study Area")
		continue

	part_count = len(q)
	add_parts = defaultdict(list)
	sub_parts = defaultdict(list)

	for seq_num, def_und, freq in q:
		freq = SpectrumRanges.fromstr(freq)

		if ((not downlink_range or not freq.findwithin(downlink_range)) and
				(not uplink_range or not freq.findwithin(uplink_range)) and
				(not tdd_range or not freq.findwithin(tdd_range))):
			print(uls_no, call_sign, "skipping out of range license")
			part_count -= 1
			continue

		if submarket_code == 0:
			assert len(q) == 1, "%s submarket_code is 0 but license has multiple partitions" % call_sign
			props = feature_props(uls_no, call_sign, owner, frn, market, market_pop, freq)
			result.append(geojson.Feature(properties=props, geometry=market_geoms[market.replace('EAG70', 'EAG00')]))
			part_count -= 1
			break

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
			dest_list[freq].append((geom, part_pop))

	if part_count > 0:
		assert len(add_parts) > 0, "no geometries included %s" % call_sign

		partitions = PartitionCollection()
		partitions.add_parts(add_parts)
		partitions.subtract_parts(sub_parts)

		for freq, geom, population in partitions.items():
			if type(geom) is GeometryCollection:
				print(uls_no, call_sign, "removing non-polygons from geometry")
				geom = MultiPolygon([ p for p in geom if type(p) is Polygon ])

			props = feature_props(uls_no, call_sign, owner, frn, market, population, freq)
			result.append(geojson.Feature(properties=props, geometry=mapping(geom)))

result = geojson.FeatureCollection(result)
with open(filename, 'w') as out:
	geojson.dump(result, out)

con.commit()
con.close()


