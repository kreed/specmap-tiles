#!/usr/bin/env python3

from pprint import pprint
from tables import uls_tables
import csv
import csv
import geojson
import io
import pickle
import sqlite3
import sys
import zipfile

con = sqlite3.connect("l_market.sqlite")
cur = con.cursor()


with zipfile.ZipFile('l_market.zip', 'r') as inzip:
	for table, cols in uls_tables.items():
		cur.execute('DROP TABLE IF EXISTS ' + table)
		cur.execute('CREATE TABLE ' + table + '(' + ','.join(cols) + ')')
		with io.TextIOWrapper(inzip.open(table + '.dat'), encoding='latin-1') as infile:
			for row in infile:
				row = row.strip().split("|")
				if len(row) == len(cols):
					cur.execute('INSERT INTO ' + table + ' VALUES(' + (len(cols) * '?,')[:-1] + ')', row)

con.commit()
con.close()
