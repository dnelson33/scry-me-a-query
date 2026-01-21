import requests

BASE_URL='https://api.scryfall.com/cards/search'
SITE_LINK='https://scryfall.com/search'

def scryfall_query(search_text) -> tuple[dict, str]:
    if 'order' in search_text:
        order = search_text.split('order:')[1].split()[0]
    else:
        order = 'edhrec'
    
    query_params = f'q={search_text}&order={order}'
    url = f'{BASE_URL}?{query_params}'
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f'Error fetching data from Scryfall API: {response.status_code}')
    data = response.json()
    site_url = f'{response.url.replace(BASE_URL, SITE_LINK)}'
    return (data, site_url)
    