from bs4 import BeautifulSoup
import requests

with open('data/ships.csv', 'r') as fh:
	# Skip header
	fh.readline()
	
	for row in fh.readlines():
		(name,callsign) = row.replace('\n', '').rsplit(',', 1)
		
		print('extracting for '+name)
		url = 'http://www.sailwx.info/shiptrack/shipdump.phtml?call='+callsign
		
		html = requests.get(url, headers={'referer': 'http://www.sailwx.info/shiptrack/shipposition.phtml?call='+callsign}).content
		print(len(html))
		soup = BeautifulSoup(html, 'html.parser')
		csv = soup.find_all('pre')[0].get_text().replace('\n', '', 1)
		
		with open('data/ships/'+callsign+'.csv', 'w') as out:
			out.write(csv)
