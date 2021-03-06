from shapely.ops import unary_union

class PartitionCollection:
	def __init__(self):
		self.parts = {}

	def add_parts(self, table):
		for freq, parts in table.items():
			geom = unary_union([ p[0] for p in parts ])
			pops = [ p[1] for p in parts ]
			pop = None if None in pops else sum(pops)

			intersects = 0
			for f in list(self.parts.keys()): # copy the key list because we may change the dict
				new_contains_existing = freq.contains(f)
				existing_contains_new = f.contains(freq)
				if not new_contains_existing and not existing_contains_new:
					continue

				intersection = geom.intersection(self.parts[f][0])

				if intersection.area / geom.area > .01:
					intersects += 1

					if existing_contains_new:
						geom.difference(intersection)
						pop = None
					else:
						self.parts[f] = (self.parts[f][0].difference(intersection), None)

			if intersects > 0:
				print('add intersects:', intersects)

			self.parts[freq] = (geom, pop)

	def subtract_parts(self, table):
		for freq, parts in table.items():
			geom = unary_union([ p[0] for p in parts ])

			intersects = 0
			remaining_geom = geom
			for f in list(self.parts.keys()): # copy the key list because we may change the dict
				add_contains = f.contains(freq)
				sub_contains = freq.contains(f)
				if not add_contains and not sub_contains:
					continue

				intersection = remaining_geom.intersection(self.parts[f][0])
				if intersection.area / geom.area > .01:
					intersects += 1

					if add_contains and not sub_contains:
						add_freq = f.difference(freq)
						if add_freq in self.parts:
							add_geom, add_pop = self.parts[add_freq]
							self.parts[add_freq] = (add_geom.union(intersection), None)
						else:
							self.parts[add_freq] = (remaining_geom, None)

					parent_geom, parent_pop = self.parts[f]
					self.parts[f] = (parent_geom.difference(remaining_geom), None)

					remaining_geom = remaining_geom.difference(parent_geom)
					if remaining_geom.area / geom.area < .01:
						break

			if intersects > 1:
				print('subtract intersects:', intersects)

			if remaining_geom.area / geom.area >= .01:
				print("large remaining exclude geometry (%.3f%% of original area)" % (100 * remaining_geom.area / geom.area))

	def items(self):
		return [ (freq,) + part for freq, part in self.parts.items() ]
