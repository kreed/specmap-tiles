#!/usr/bin/env python3

import csv
from pprint import pprint

markets = {}

with open('FCCCNTY2K.txt', encoding='latin-1') as infile:
	incsv = csv.DictReader(infile)
	for line in incsv:
		cma = 'CMA%03d' % int(line['CMA'])
		if not cma in markets:
			markets[cma] = []
		markets[cma].append(line['FIPS'])

		bea = 'BEA%03d' % int(line['EA'])
		if not bea in markets:
			markets[bea] = []
		markets[bea].append(line['FIPS'])

print('markets = ', end='')
print(markets)
