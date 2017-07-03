from bs4 import BeautifulSoup
import requests, wikipedia, html2text, re, json

outfile = open('data/ships.json', 'w')
with open('data/ships.csv', 'r') as fh:
	fh.readline()
	
	for row in fh.readlines():
		page_url_override = False
		(name,callsign,wiki) = row.replace('\n', '').rsplit(',', 2)
		ship = {'name': name, 'callsign': callsign, 'wiki': wiki}
		
		if 'wikipedia' in ship['wiki']:
			title = ship['wiki'].split('/')[-1].replace('_', ' ')
			page = wikipedia.page(title)
			page_content = page.html()
			page_url_override = True
		else:
			try:
				res = wikipedia.search(name)
		
				if len(res) > 0:
					page = wikipedia.page(res[0])
					page_content = page.html()
					ship['wiki'] = page.url
			except wikipedia.exceptions.DisambiguationError:
				print('Disambiguation error for '+name+' ('+callsign+')')
				page_content = None
		
		if page_content and len(page_content) > 0:
			if 'IMO' in page_content or 'MMSI' in page_content or page_url_override:
				imo = re.search('imo:([0-9]{7})', page_content)
				if imo:
					ship['imo'] = imo.group(1)
				
				mmsi = re.search('mmsi:([0-9]{9})', page_content)
				if mmsi:
					ship['mmsi'] = mmsi.group(1)
				
				soup = BeautifulSoup(page_content, 'html.parser')
				infobox = soup.find('table', {'class': 'infobox'})
			
				for row in infobox.findAll('tr'):
					cells = row.findAll('td')
					
					if len(cells) > 1:
						label = cells[0].text.replace(':', '').lower()
						value = cells[1].text
						
						if label == 'maiden voyage' or label == 'completed' or label == 'launched':
							matches = re.search('([0-9]{4})', value)
							if matches:
								try:
									ship['year_built'] = int(matches.group(1))
								except ValueError:
									pass
						
						if label == 'owner' and 'cruise_line' not in ship:
							ship['cruise_line'] = value.split('(')[0].replace('\n', '').strip()
						
						if label == 'operator':
							ship['cruise_line'] = value.split('(')[0].replace('\n', '').strip()
						
						if label == 'decks':
							try:
								ship['decks'] = int(value.split(' ')[0].replace('\n', ''))
							except ValueError:
								pass
						
						if label == 'class and type':
							ship['class'] = value.replace('\n', '')
						
						if label == 'length':
							matches = re.search('^([0-9\.]+)[\s]+m', value.replace('\n', ''))
							
							if matches:
								try:
									ship['length'] = float(matches.group(1))
								except ValueError:
									pass
						
						if label == 'tonnage':
							matches = re.search('([0-9,]+)[\s]+GT', value)
							
							if matches:
								try:
									ship['gross_tonnage'] = int(matches.group(1).replace(',', ''))
								except ValueError:
									pass
						
						if label == 'capacity':
							matches = re.search('([0-9,]+)[\s]+passengers', value)
							
							if matches:
								try:
									ship['capacity'] = int(matches.group(1).replace(',', ''))
								except ValueError:
									pass
									
				if 'imo' in ship:
					headers = {
						'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
						'Accept-Encoding': ', '.join(('gzip', 'deflate')),
						'Accept': '*/*',
						'Connection': 'keep-alive',
					}
			
					url = 'https://www.marinetraffic.com/en/ais/details/ships/'+ship['imo']
					resp = requests.get(url, headers=headers)
			
					soup = BeautifulSoup(resp.text, 'html.parser')
					details = soup.find('div', {'id': 'vessel_details_general'})
					
					length = re.search('<span>Length Overall x Breadth Extreme: </span>[\s]+<b>([0-9,]+)m', resp.text)
					if length and ('length' not in ship or float(length.group(1)) != ship['length']):
						ship['length'] = float(length.group(1))
			
					if details:
						for item in details.findAll('li'):
							text = item.find('span').text
					
							['Vessel Type', 'Flag', 'Home Port']
					
							type = re.search('^Vessel Type: ([A-Z ]+)', text)
							if type:
								ship['vessel_type'] = type.group(1)
					
							flag = re.search('^Flag: ([A-Z ]+)', text)
							if flag:
								ship['flag'] = flag.group(1)
					
							port = re.search('^Home port: ([A-Z ]+)', text)
							if port:
								ship['home_port'] = port.group(1)
						
							tonnage = re.search('^Gross Tonnage: ([0-9,]+)', text)
							try:
								if tonnage and ('gross_tonnage' not in ship or int(tonnage.group(1)) != ship['gross_tonnage']):
									ship['gross_tonnage'] = int(tonnage.group(1))
							except ValueError:
								pass
							
							mmsi = re.search('^MMSI: ([0-9]{9})', text)
							try:
								if mmsi and ('mmsi' not in ship or mmsi.group(1) != ship['mmsi']):
									ship['mmsi'] = mmsi.group(1)
							except ValueError:
								pass
		
			else:
				print('No results for '+name+' ('+callsign+')')

		outfile.write(json.dumps(ship) + "\n")
outfile.close()
