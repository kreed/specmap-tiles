#!/usr/bin/env python3

import csv
import io
import zipfile
from collections import defaultdict
from pprint import pprint

common_names = defaultdict(set)

with zipfile.ZipFile('fcc-license-view-data-csv-format.zip', 'r') as inzip:
	with inzip.open('fcc_lic_vw.csv') as infile:
		incsv = csv.DictReader(io.TextIOWrapper(infile))
		for row in incsv:
			frn = row['FRN']
			common_name = row['COMMON_NAME']
			if frn and common_name:
				common_names[common_name].add(frn)

with open('fcc_common_names.py', 'w') as f:
	f.write('fcc_common_names = ')
	pprint(common_names, stream=f)
