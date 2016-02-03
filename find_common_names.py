#!/usr/bin/env python3

import csv
import io
import zipfile
from fcc_common_names import fcc_common_names
from pprint import pprint

owners = {}

# List of common names to import from FCC license view data. Multiple entries
# per row will all be merged under the first name.
common_names = [
	('C Spire', 'Cellular South'),
	('AT&T',),
	('Sprint', 'Sprint Nextel', 'Clearwire', 'FIXED WIRELESS HOLDINGS, LLC'),
	('Verizon', 'Verizon Wireless', 'Binghamton MSA Limited Partnership', 'Duluth MSA Limited Partnership', 'ANDERSON CELLTELCO', 'DANVILLE CELLULAR TELEPHONE COMPANY LIMITED PARTNERSHIP', 'NEW MEXICO RSA 3 LIMITED PARTNERSHIP', 'Missouri RSA 2 Limited Partnership', 'GTE MOBILNET OF TEXAS RSA #17 LIMITED PARTNERSHIP', 'ILLINOIS RSA 6 AND 7 LIMITED PARTNERSHIP', 'Southern Indiana RSA Limited Partnership', 'Virginia RSA 5 Limited Partnership', 'Pittsburgh SMSA Limited Partnership', 'Seattle SMSA Limited Partnership', 'Syracuse SMSA Limited Partnership', 'New Hampshire RSA 2 Partnership', 'NYNEX Mobile Limited Partnership 2', 'GTE MOBILNET OF SANTA BARBARA LIMITED PARTNERSHIP', 'CALIFORNIA RSA NO. 4 LIMITED PARTNERSHIP', 'IDAHO RSA NO. 2 LIMITED PARTNERSHIP'),
	('T-Mobile',),
	('US Cellular',),
	('Viaero Wireless',),
	('GCI', 'GCI Communication Corp.'),
	('Dish Network', 'EchoStar'),
	('AB License Co', 'AB License Co LLC'),
	('Cellular One of East Texas',),
	('SRT Communications',),
	('Commnet Wireless / Choice Wireless', 'Commnet Four Corners, LLC', 'Commnet Wireless'),
	('West Central Wireless', 'Central Texas Telephone Coop (CTTC)', 'CENTRAL TEXAS COMMUNICATIONS, INC.', 'CGKC&H NO. 2 RURAL CELLULAR LIMITED PARTNERSHIP', 'FIVE STAR WIRELESS'),
	('MTA Solutions', 'MTA Wireless'),
	('iWireless', 'i Wireless', 'West Iowa Wireless'),
	('América Móvil', 'America Movil'),
	('Pioneer Cellular', 'Pioneer Enid Cellular'),
	('Nemont', 'Sagebrush Cellular'),
	('Appalachian Wireless',),
	('S&T Telephone',),
	('Bluegrass Cellular',),
	('Carolina West Wireless',),
	('Smithville Communications', 'Smithville Telephone'),
	('Hilbert Communications',),
	('Cameron Communications', 'Cameron'),
	('Cellcom',),
	('Big Bend Telephone',),
	('ClearTalk Wireless', 'Flat Wireless'),
	('Pine Cellular',),
	('NEP Cellcorp'),
	('VTel Wireless', 'VTel Wireless, Inc.'),
	('DoCoMo Pacific', 'GUAMCELL'),
	('IT&E', 'PTI Pacifica'),
	('Innovative Communications',),
	('James Valley Telecommunications', 'James Valley Cooperative Telephone'),
	('Kennebec Telephone Company', 'Kennebec Telephone'),
	('Norvado', 'Chequamegon Communications Cooperative'),
	('Union Wireless', 'Union Telephone'),
	('nTelos', 'NTELOS LICENSES INC.'),
	('Wilkes Communications', 'Wilkes Cellular'),
	('West Carolina Tel', 'West Carolina Rural Telephone Coop'),
	('Cellular One of Arizona', 'SMITH BAGLEY'),
	('PTCI', 'Panhandle Telephone'),
	('United Telcom',),
	('Indigo Wireless',),
	('Chariton Valley',),
	('DTC Wireless', 'ADVANTAGE CELLULAR'),
	('Thumb Cellular',),
]

# FCC doesn't have common names associated with these FRNs yet
frns = {
	'0001601079': 'Strata Networks',
	'0001618008': 'Leaco / NMobile',
	'0001630532': 'Silver Star Communications',
	'0001637222': 'Triangle Communications',
	'0001649110': 'Peoples Telephone Coop',
	'0001696319': 'Pioneer Cellular',
	'0001754209': 'Pine Belt Wireless',
	'0001835073': 'SouthernLINC Wireless',
	'0001855352': 'SouthernLINC Wireless',
	'0001886944': 'Horry Telephone Cooperative',
	'0002837136': 'AT&T',
	'0003801362': 'WUE, Inc',
	'0004242475': 'iConnect',
	'0010584589': 'Sprint',
	'0011458999': 'GTA Teleguam',
	'0015019003': 'US Cellular',
	'0015024565': 'AT&T',
	'0015991664': 'Open Mobile',
	'0021004817': 'Dish Network',
	'0021472915': 'Kennebec Telephone Company',
	'0021818133': 'GCI',
	'0021991161': 'Infrastructure Networks',
	'0022183347': 'Northeast Wireless Networks',
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

for names in common_names:
	for name in names:
		for frn in fcc_common_names.get(name.upper(), []):
			if not frn in frns:
				frns[frn] = names[0]

with open('common_names.py', 'w') as f:
	f.write('frn_table = ')
	pprint(frns, stream=f)
