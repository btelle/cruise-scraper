import requests, json, time

api_key = 'AIzaSyAj4QfwThTfPttoh_LaRzIx5U10onljk-Y'
url = 'https://maps.googleapis.com/maps/api/geocode/json'

outfile = open('data/cities.json', 'w')

with open('data/cities.csv', 'r') as fh:
	fh.readline()
	
	for city in fh.readlines():
		params = {
			'address': city.strip(),
			'key': api_key
		}
		
		out = {
			'city': city.strip()
		}
		
		resp = requests.get(url, params=params)
		
		obj = resp.json()
		if obj['status'] == 'OK':
			out['lat'] = obj['results'][0]['geometry']['location']['lat']
			out['lon'] = obj['results'][0]['geometry']['location']['lng']
			out['id'] = obj['results'][0]['place_id']
			
			for r in obj['results'][0]['address_components']:
				if 'country' in r['types']:
					out['country_code'] = r['short_name']
					out['country'] = r['long_name']
		outfile.write(json.dumps(out) + "\n")
		time.sleep(2)
outfile.close()