#!/bin/sh
./query.py $1
./map.py $1
node merge.js $1
