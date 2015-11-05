var turf = require('turf');
var fs = require('fs');

var block = process.argv[2];

var file = fs.readFileSync('./700' + block + '.geojson', 'utf8');
var input = JSON.parse(file);
var map = {};

for (var i = 0; i < input.features.length; ++i) {
	var f = input.features[i]
	var hash = f.properties['market'] + f.properties['owner'];
	if (map[hash] == null) map[hash] = turf.featurecollection([]);
	map[hash].features.push(f);
}

var result = turf.featurecollection([]);

for (var market in map) {
	try {
		result.features.push(turf.merge(map[market]));
	} catch (e) {
		console.log(market);
		console.log(JSON.stringify(map[market]));
	}
}

fs.writeFileSync('./700' + block + '-merged.geojson', JSON.stringify(result));
