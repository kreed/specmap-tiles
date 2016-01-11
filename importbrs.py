#!/usr/bin/env python3

import io
import sqlite3
import zipfile
from tables import uls_tables

con = sqlite3.connect("l_mdsitfs.sqlite")
cur = con.cursor()

with zipfile.ZipFile('l_mdsitfs.zip', 'r') as inzip:
	for table, cols in uls_tables.items():
		cur.execute('DROP TABLE IF EXISTS ' + table)
		cur.execute('CREATE TABLE ' + table + '(' + ','.join(cols) + ')')
		with io.TextIOWrapper(inzip.open(table + '.dat'), encoding='latin-1') as infile:
			for row in infile:
				row = row.strip().split("|")
				if len(row) == len(cols):
					cur.execute('INSERT INTO ' + table + ' VALUES(' + (len(cols) * '?,')[:-1] + ')', row)

with open('fixbrs.dat') as infile:
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

con.commit()
con.close()
