def owner_dba(owner, email):
	owner, email = owner.lower(), email.lower()

	if email.endswith('t-mobile.com'):
		return 'T-Mobile'
	if email.endswith('verizonwireless.com'):
		return 'Verizon'
	if email.endswith('att.com'):
		return 'AT&T'
	if email.endswith('sprint.com'):
		return 'Sprint'
	if email.endswith('wcc.net'):
		return 'West Central Wireless'
	if email.endswith('cellonenation.com'):
		return 'Cellular One (Chinook)'
	if email.endswith('dish.com') or email.endswith('dishnetwork.com'):
		return 'Dish Network'
	if email.endswith('viaero.com'):
		return 'Viaero Wireless'
	if email.endswith('claropr.com'):
		return 'Claro'
	if email.endswith('openmobilepr.com'):
		return 'Open Mobile'
	if email.endswith('commnetwireless.com'):
		return 'Commnet Wireless'
	if email.endswith('ptci.com'):
		return 'Pioneer Cellular'

	if owner.startswith('wirelessco') or 'sprint' in owner or 'nextel' in owner or 'nsac' in owner or 'fixed wireless holdings' in owner:
		return 'Sprint'
	if 'at&t' in owner or 'a t & t' in owner or 'cingular' in owner:
		return 'AT&T'
	if 't-mobile' in owner:
		return 'T-Mobile'
	if owner == 'cellco partnership' or 'verizon' in owner or 'alltell' in owner:
		return 'Verizon'
	if owner.startswith('uscoc') or 'united states cellular' in owner or 'king street wireless' in owner or 'carroll wireless' in owner or 'barat wireless' in owner or owner == 'hardy cellular telephone company':
		return 'US Cellular'
	if 'cellular south' in owner:
		return 'C Spire'
	if 'iowa wireless' in owner:
		return 'iWireless'
	if 'snr wireless' in owner or 'northstar wireless' in owner:
		return 'Dish Network'
	if owner.startswith('cavalier'):
		return 'Cavalier'
	if owner.startswith('c700'):
		return 'Continuum 700'
	if 'grain spectrum' in owner:
		return 'Grain Spectrum'
	if 'ab license co' in owner:
		return 'AB License Co'
	if 'ct cube' in owner or 'central texas telephone' in owner:
		return 'West Central Wireless'
	if 'infrastructure networks' in owner:
		return 'Infrastructure Networks'
	if 'alaska wireless network' in owner:
		return 'GCI'
	if 'mta communications' in owner:
		return 'MTA Communications'
	if 'north dakota network' in owner:
		return 'SRT Communications'
	if 'bluegrass' in owner:
		return 'Bluegrass Cellular'
	if 'east kentucky network' in owner or 'appalachian wireless' in owner:
		return 'Appalachian Wireless'
	if 'nemont communications' in owner:
		return 'Nemont'
	if 'triangle communication' in owner:
		return 'Triangle Communications'
	if 's&t telephone' in owner:
		return 'S&T Telephone Coop'
	return None

color_table = {
	'T-Mobile': '#ff00ff',
	'iWireless': '#ff9cff',
	'C Spire': '#208dd9',
	'AT&T': '#00FFFF',
	'US Cellular': '#A5CCE8',
	'AB License Co': '#00ff00',
	'Cavalier': '#009E60',
	'Continuum 700': '#BFFF00',
	"Sprint": '#FFFF00',
	"Verizon": '#ff0000',
	'Dish Network': '#ff7794',
}

def owner_color(owner_dba):
	return color_table.get(owner_dba, None)
