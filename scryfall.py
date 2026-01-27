import requests

BASE_URL='https://api.scryfall.com/cards/search'
SITE_LINK='https://scryfall.com/search'

def scryfall_query(search_text) -> tuple[dict, str]:
    if 'order' in search_text:
        order = search_text.split('order:')[1].split()[0]
    else:
        order = 'edhrec'
    
    if not any(x in search_text for x in ['legal:', 'format:', 'f:']):
        search_text += ' f:edh'
    
    query_params = f'q={search_text}&order={order}'
    url = f'{BASE_URL}?{query_params}'
    
    response = requests.get(url)
    site_url = f'{response.url.replace(BASE_URL, SITE_LINK)}'
    
    if response.status_code != 200:
        if response.status_code == 404:
            return (None, site_url)
        raise Exception(f'Error fetching data from Scryfall API\nStatus: {response.status_code}\nURL: {url}')
    data = response.json()
    
    return (data, site_url)
    