#!/usr/bin/env python3

import pickle
import re
import sqlite3
import sys
from markets import markets
from pprint import pprint

county_owners = {}
block = sys.argv[1]

con = sqlite3.connect("l_market.sqlite")
cur = con.cursor()

def canon_owner(owner):
	if owner.startswith('USCOC') or owner == 'King Street Wireless, LP' or owner == 'UNITED STATES CELLULAR OPERATING COMPANY LLC':
		return 'US Cellular'
	if owner == 'T-Mobile License LLC':
		return 'T-Mobile'
	if owner == 'AT & T Mobility Spectrum LLC' or owner == 'AT&T Mobility Spectrum LLC' or owner == 'New Cingular Wireless PCS, LLC':
		return 'AT&T'
	if owner.startswith('Cavalier'):
		return 'Cavalier'
	if owner.startswith('C700'):
		return 'Continuum 700'
	if owner == 'Cellular South Licenses, LLC':
		return 'C Spire'
	return owner

for row in cur.execute("SELECT call_sign, entity_name, market_code, population FROM HD JOIN EN USING (call_sign) JOIN MK USING (call_sign) LEFT OUTER JOIN MP USING (call_sign) WHERE MP.call_sign IS NULL AND license_status='A' AND radio_service_code='WY' AND channel_block=? AND entity_type='L' AND cancellation_date='' AND NOT call_sign LIKE 'L%'", block):
	call_sign, owner, market, population = row
	for fips in markets[market]:
		county_owners[fips] = {'market': market, 'call_sign': call_sign, 'population': population, 'owner': canon_owner(owner)}

for row in cur.execute("SELECT call_sign, entity_name, market_code, market_partition_code, defined_partition_area, part_pop FROM HD JOIN EN USING (call_sign) JOIN MK USING (call_sign) JOIN MP USING (call_sign) JOIN (SELECT call_sign, sum(defined_area_population) AS part_pop FROM MP GROUP BY call_sign) USING (call_sign) WHERE license_status='A' AND radio_service_code='WY' AND channel_block=? AND entity_type='L' AND cancellation_date='' AND defined_partition_area!='' AND NOT call_sign LIKE 'L%'", block):
	call_sign, owner, market, market_partition, county, population = row
	if (call_sign == 'WQIZ639'):
		# special case for Seattle market because we don't handle coordinate partitions yet (T-Mobile owns both partitions anyway)
		for fips in markets[market]:
			county_owners[fips] = {'market': market, 'call_sign': call_sign, 'population': population, 'owner': canon_owner(owner)}
	elif market == market_partition:
		match = re.match('(\d+): [A-Z ]+, [A-Z]{2}', county)
		if match:
			fips = match.group(1)
			county_owners[fips] = {'market': market, 'call_sign': call_sign, 'population': population, 'owner': canon_owner(owner)}
		else:
			print('reject non-county', row)
	else:
		print('reject market mismatch', row)

with open('700%s.pickle' % block, 'wb') as dump:
	pickle.dump(county_owners, dump)

con.commit()
con.close()
