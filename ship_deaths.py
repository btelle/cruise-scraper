import requests, re, csv, time
from bs4 import BeautifulSoup

def firefox_request(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
        'Accept-Encoding': ', '.join(('gzip', 'deflate')),
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }
    
    return requests.get(url, headers=headers)

def get_tags(list_items):
    tags = []
    for li in list_items:
        tag = {}
        tag['url'] = li.find('a')['href']
        tag['slug'] = tag['url'].rsplit('/', 2)[1]
        tag['text'] = li.find('a').text
        tags.append(tag)
    
    return tags
    
def parse_page(url):
    """
    Parse a Cruise Ship Deaths article for relevant information.
    Returns dict
    Fields: date_published, death_time, death_type, deceased_name, deceased_age, deceased_gender, 
            is_passenger, is_crew, cruise_line, ship_name, ship_callsign, url
    """
    death_types = ['murder', 'overboard', 'suicide', 'natural', 'accident', 'illness', 'missing', 
                   'alcohol-related', 'drug-overdose', 'drowning', 'fire', 'sinking', 'norovirus']
    death_type_bc_mappings = {
        'murders': 'murder',
        'overboards': 'overboard',
        'suicides': 'suicide',
        'natural causes': 'natural',
        'accidental deaths': 'accident',
        'illness': 'illness',
        'port deaths': 'in-port',
        'missing presumed dead': 'missing',
        'overdoses': 'overdose',
        'disasters': 'disaster',
        'drowning': 'drowning',
        'fires': 'fire',
        'sinkings': 'sinking'
    }
    genders = ['male', 'female']
    cruise_lines = ['disney', ' of the seas', 'carnival', 'norwegian',  'princess', 'mv ', 'ms ']
    
    resp = firefox_request(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    first_graf = soup.find('div', {'class': 'entry-content'}).findAll('p')[0].text
    
    death = {'is_passenger': False, 'is_crew': False}
    death['date_published'] = soup.find('span', {'class': 'entry-meta-date'}).find('a').text
    death['deceased_name'] = first_graf.split(',')[0]
    death['url'] = url
    
    for tag in get_tags(soup.find('div', {'class': 'entry-tags'}).findAll('li')):
        if tag['slug'].startswith('time-of-death'):
            matches = re.match('time-of-death-([0-9]{4})', tag['slug'])
            if matches:
                death['death_time'] = matches.group(1)
        
        if tag['slug'] in death_types:
            death['death_type'] = tag['slug']
        
        if re.match('alcohol-related', tag['slug']):
            death['death_type'] = 'alcohol-related'
        elif re.match('suicidal', tag['slug']):
            death['death_type'] = 'suicide'
        
        if 'death_type' not in death:
            breadcrumb = soup.find('nav', {'class': 'mh-breadcrumb'}).findAll('span', {'itemprop': 'title'})[1]
            bc_key = breadcrumb.text.replace('Cruise Ship', '').strip().lower()
            
            if bc_key in death_type_bc_mappings:
                death['death_type'] = death_type_bc_mappings[bc_key]
        
        age_match = re.match('age-([0-9]+)', tag['slug'])
        if age_match:
            death['deceased_age'] = age_match.group(1)
        
        if tag['slug'] in genders:
            death['deceased_gender'] = tag['slug']
        
        if tag['slug'] == 'passenger':
            death['is_passenger'] = True
        
        if tag['slug'] == 'crew':
            death['is_crew'] = True
        
        if 'Cruise Line' in tag['text'] or 'Cruises' in tag['text']:
            death['ship_cruise_line'] = tag['text']
        else:
            for line in cruise_lines:
                if line in tag['text'].lower() and line != tag['text'].lower():
                    death['ship_name'] = tag['text']
    
    if 'ship_name' in death and death['ship_name'].lower() in callsign_lookup:
        death['ship_callsign'] = callsign_lookup[death['ship_name'].lower()]

    return death

callsign_lookup = {}
with open('data/cruise-ship-locations-QueryResult.csv', 'r') as fh:
    for row in [r.split(',') for r in fh.readlines()]:
        callsign_lookup[row[0]] = row[1].replace('\n', '')

base_url = 'https://www.cruiseshipdeaths.com/tag/{}/page/{}/'
columns = ['date_published', 'death_time', 'death_type', 'deceased_name', 'deceased_age', 'deceased_gender', 
            'is_passenger', 'is_crew', 'ship_cruise_line', 'ship_name', 'ship_callsign', 'url']
deaths = []

with open('data/output_deaths.csv', 'w') as fh:
    w = csv.DictWriter(fh, columns)
    w.writeheader()

    for year in range(2000, 2018):
        keep_extracting = True
        page = 1
        urls = []
        
        while keep_extracting:
            url = base_url.format(year, page)
            resp = firefox_request(url)

            if resp.status_code == 200:
                # get list of articles
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                for article in soup.findAll('article'):
                    urls.append(article.find('header').find('a')['href'])
                
                page += 1
                time.sleep(15)
            else:
                keep_extracting = False
        
        for article_url in urls:
            print(article_url)
            try:
                death_parsed = parse_page(article_url)
                deaths.append(death_parsed)
                w.writerow(death_parsed)

                time.sleep(30)
            except Exception as e:
                print('Uncaught exception {}'.format(e))

print("extracted {} deaths".format(len(deaths)))
