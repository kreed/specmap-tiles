#!/usr/bin/env python3

import io
import sqlite3
import zipfile
from tables import uls_tables

dbs = (
	('l_market', 'fix.dat'),
	('l_cell', 'fixcell.dat'),
	('l_mdsitfs', 'fixbrs.dat'),
)

for db, fixes in dbs:
	con = sqlite3.connect(db + '.sqlite')
	cur = con.cursor()

	with zipfile.ZipFile(db + '.zip', 'r') as inzip:
		for table, cols in uls_tables.items():
			cur.execute('DROP TABLE IF EXISTS ' + table)
			try:
				with io.TextIOWrapper(inzip.open(table + '.dat'), encoding='latin-1') as infile:
					cur.execute('CREATE TABLE ' + table + '(' + ','.join(cols) + ')')
					for row in infile:
						row = row.strip().split("|")
						if len(row) == len(cols):
							cur.execute('INSERT INTO ' + table + ' VALUES(' + (len(cols) * '?,')[:-1] + ')', row)
			except KeyError:
				continue

	try:
		with open(fixes) as infile:
			for row in infile:
				delete = False
				if row[0] == '-':
					delete = True
					row = row[1:]

				row = row.strip().split("|")
				table = row[0]
				cols = uls_tables[table]

				if len(row) == len(cols):
					if delete:
						cur.execute('DELETE FROM ' + table + ' WHERE ' + (' AND '.join([ col.split(' ')[0] + '=?' for col in cols ])), row)
					else:
						cur.execute('INSERT INTO ' + table + ' VALUES(' + (len(cols) * '?,')[:-1] + ')', row)
	except FileNotFoundError:
		pass

	con.commit()
	con.close()
