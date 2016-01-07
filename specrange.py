class SpectrumRange:
	def __init__(self, lower, upper):
		assert lower < upper, "%f-%f" % (lower, upper)
		self.lower, self.upper = lower, upper

	def overlaps(self, other):
		return (self.lower <= other.lower <= self.upper or
				other.lower <= self.lower <= other.upper)

	def union(self, other):
		assert self.overlaps(other)
		return SpectrumRange(min(self.lower, other.lower), max(self.upper, other.upper))

	def contains(self, other):
		return self.lower <= other.lower <= other.upper <= self.upper

	def difference(self, subfreq):
		assert self.contains(subfreq)
		if self.lower < subfreq.lower:
			yield SpectrumRange(self.lower, subfreq.lower)
		if self.upper > subfreq.upper:
			yield SpectrumRange(subfreq.upper, self.upper)

	def __repr__(self):
		return "{:g}-{:g}".format(self.lower, self.upper)

	def __hash__(self):
		return hash((self.lower, self.upper))

	def __eq__(self, other):
		return (self.lower, self.upper) == (other.lower, other.upper)

	def __lt__(self, other):
		return self.lower < other.lower

class SpectrumRanges:
	@classmethod
	def fromstr(cls, s):
		rngs = []
		for pair in s.split(','):
			lower, upper = [ float(f) for f in pair.split('-') ]
			if lower != upper:
				rngs.append(SpectrumRange(lower, upper))
		return cls(rngs)

	def __init__(self, ranges):
		rngs = []

		def add(item):
			for i in range(len(rngs)):
				if rngs[i].overlaps(item):
					new = rngs[i].union(item)
					del rngs[i]
					add(new)
					return
			rngs.append(item)

		for r in ranges:
			add(r)

		self.ranges = tuple(sorted(rngs))

	def downlink(self):
		return ','.join([ repr(e) for e in self.ranges[:len(self.ranges)//2] ])

	def uplink(self):
		return ','.join([ repr(e) for e in self.ranges[len(self.ranges)//2:] ])

	def contains(self, otherrngs):
		for otherrng in otherrngs.ranges:
			found = False
			for thisrng in self.ranges:
				if thisrng.contains(otherrng):
					found = True
					break
			if not found:
				return False
		return True

	def difference(self, otherrngs):
		assert self.contains(otherrngs)

		newrngs = []

		for thisrng in self.ranges:
			subrng = None
			for otherrng in otherrngs.ranges:
				if thisrng.contains(otherrng):
					subrng = otherrng
					break
			if subrng:
				newrngs.extend(thisrng.difference(subrng))
			else:
				newrngs.append(thisrng)

		return SpectrumRanges(newrngs)

	def __repr__(self):
		return ','.join([ str(e) for e in self.ranges])

	def __hash__(self):
		return hash(self.ranges)

	def __eq__(self, other):
		return self.ranges == other.ranges
