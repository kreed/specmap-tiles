#!/usr/bin/env python3

import csv
import io
import zipfile

owners = {}

common_names = [
	('C-Spire', 'Cellular South'),
	('AT&T',),
	('Sprint', 'Sprint Nextel', 'Clearwire', 'FIXED WIRELESS HOLDINGS, LLC'),
	('Verizon', 'Verizon Wireless'),
	('T-Mobile',),
	('US Cellular',),
	('Viaero Wireless',),
	('GCI', 'GCI Communication Corp.'),
	('Dish Network', 'EchoStar'),
	('AB License Co', 'AB License Co LLC'),
	('Cellular One of East Texas',),
	('SRT Communications',),
	('Commnet Wireless', 'Commnet Four Corners, LLC'),
	('West Central Wireless', 'Central Texas Telephone Coop (CTTC)'),
	('MTA Solutions', 'MTA Wireless'),
	('iWireless', 'i Wireless', 'West Iowa Wireless'),
	('América Móvil', 'America Movil'),
	('Pioneer Cellular', 'Pioneer Enid Cellular'),
	('Nemont', 'Sagebrush Cellular'),
	('Appalachian Wireless',),
	('S&T Telephone',),
	('Bluegrass Cellular',),
]

# FCC doesn't have common names associated with these FRNs yet
frns = {
	'0001637222': 'Triangle Communications',
	'0001696319': 'Pioneer Cellular',
	'0010584589': 'Sprint',
	'0015019003': 'US Cellular',
	'0015024565': 'AT&T',
	'0015991664': 'Open Mobile',
	'0021004817': 'Dish Network',
	'0021818133': 'GCI',
	'0021991161': 'Infrastructure Networks',
	'0022389647': 'Grain Spectrum',
	'0022389670': 'Grain Spectrum',
	'0022415855': 'AT&T',
	'0022683619': 'AT&T',
	'0022804140': 'AB License Co',
	'0023125057': 'Dish Network',
	'0023541717': 'Grain Spectrum',
	'0023684533': 'Dish Network',
	'0023907074': 'Dish Network',
	'0023917453': 'Dish Network',
	'0024532509': 'Continuum C700',
	'0024537284': 'Continuum C700',
	'0024537300': 'Continuum C700',
	'0024537318': 'Continuum C700',
	'0024537334': 'Continuum C700',
	'0024537375': 'Continuum C700',
	'0024537383': 'Continuum C700',
	'0024537425': 'Continuum C700',
	'0024537433': 'Continuum C700',
	'0024537466': 'Continuum C700',
	'0024703779': 'Cavalier',
	'0024703787': 'Cavalier',
	'0024703795': 'Cavalier',
	'0024703803': 'Cavalier',
	'0024703811': 'Cavalier',
	'0024703829': 'Cavalier',
	'0024703837': 'Cavalier',
	'0024703845': 'Cavalier',
	'0024703852': 'Cavalier',
	'0024703860': 'Cavalier',
	'0024703878': 'Cavalier',
	'0024703894': 'Cavalier',
	'0024703902': 'Cavalier',
	'0024703910': 'Cavalier',
	'0024703928': 'Cavalier',
	'0024703936': 'Cavalier',
	'0024703944': 'Cavalier',
	'0024703951': 'Cavalier',
	'0024703969': 'Cavalier',
	'0024703977': 'Cavalier',
	'0024703985': 'Cavalier',
	'0024703993': 'Cavalier',
	'0024864746': 'Grain Spectrum',
}

common_names_map = {}

for names in common_names:
	for name in names:
		common_names_map[name.upper()] = names[0]

with zipfile.ZipFile('fcc-license-view-data-csv-format.zip', 'r') as inzip:
	with inzip.open('fcc_lic_vw.csv') as infile:
		incsv = csv.DictReader(io.TextIOWrapper(infile))
		for row in incsv:
			frn = row['FRN']
			common_name = row['COMMON_NAME']
			if frn and common_name in common_names_map:
				frns[frn] = common_names_map[common_name]

with open('common_names.py', 'w') as f:
	f.write('frn_table = ')
	f.write(repr(frns))
