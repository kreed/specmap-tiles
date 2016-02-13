#!/usr/bin/env python3

import io
import sqlite3
import sys
import zipfile
from tables import uls_tables

dbs = {
	'l_mk': ('l_market', 'fix.dat'),
	'l_cl': ('l_cell', 'fixcell.dat'),
	'l_mi': ('l_mdsitfs', 'fixbrs.dat'),
}

def insertrow(cur, table, values):
	params = ','.join('NULL' if v == '' else '?' for v in values)
	param_values = [v for v in values if v != '']
	cur.execute('INSERT INTO ' + table + ' VALUES(' + params + ')', param_values)

def deleterow(cur, table, values, cols):
	params = ' AND '.join(col.split(' ')[0] + (' ISNULL' if v == '' else '=?') for col, v in zip(cols, values))
	param_values = [v for v in values if v != '']
	cur.execute('DELETE FROM ' + table + ' WHERE ' + params, param_values)

def run(db, zip_file, is_update):
	db_name, fix_file = db

	con = sqlite3.connect(db_name + '.sqlite')
	cur = con.cursor()

	all_updated_records = set()

	with zipfile.ZipFile(zip_file, 'r') as inzip:
		for table, cols in uls_tables.items():
			if not is_update:
				cur.execute('DROP TABLE IF EXISTS ' + table)
			try:
				with io.TextIOWrapper(inzip.open(table + '.dat'), encoding='latin-1') as infile:
					updated_records = set()
					if not is_update:
						cur.execute('CREATE TABLE ' + table + '(' + ','.join(cols) + ')')
					for row in infile:
						row = row.strip().split("|")
						if len(row) == len(cols):
							uls_no = row[1]
							if is_update and not uls_no in updated_records:
								cur.execute('DELETE FROM ' + table + ' WHERE unique_system_identifier=?', (uls_no,))
								updated_records.add(uls_no)
							insertrow(cur, table, row)
					all_updated_records.update(updated_records)
			except KeyError:
				continue

	try:
		with open(fix_file) as infile:
			for row in infile:
				delete = False
				row = row.strip()
				if len(row) == 0 or row[0] == '#':
					continue
				elif row[0] == '-':
					delete = True
					row = row[1:]

				uls_no = row[1]
				if is_update and not uls_no in all_updated_records:
					continue

				row = row.split("|")
				table = row[0]
				cols = uls_tables[table]

				if len(row) == len(cols):
					if delete:
						deleterow(cur, table, row, cols)
					else:
						insertrow(cur, table, row)
	except FileNotFoundError:
		pass

	con.commit()
	con.close()

if len(sys.argv) == 2:
	update_file = sys.argv[1]
	db = dbs[update_file[:4]]
	run(db, update_file, True)
else:
	for db in dbs.values():
		run(db, db[0] + '.zip', False)
