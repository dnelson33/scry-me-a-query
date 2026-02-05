from scryfall.api.types import ScryfallCardSearchRequest, ScryfallCardSearchResponse, ScryfallRandomCardRequest, ScryfallCard, ScryfallRulingsResponse
from typing import cast
import requests

BASE_URL='https://api.scryfall.com'
SCRYFALL_URL='https://scryfall.com/search'

def card_search_request(request: ScryfallCardSearchRequest) -> ScryfallCardSearchResponse:
    endpoint = 'cards/search'
    
    query_string = '&'.join([f"{key}={value}" for key, value in request.items() if value is not None])
    url = f"{BASE_URL}/{endpoint}?{query_string}"
    response = requests.get(url)
    scryfall_url = response.request.url.replace(f'{BASE_URL}/{endpoint}', SCRYFALL_URL)
    if response.status_code != 200:
        if response.status_code == 404:
            return cast(ScryfallCardSearchResponse, {"url": scryfall_url, "total_cards": 0, "has_more": False, "data": []})
        
        raise Exception(f'Error fetching data from Scryfall API\nStatus: {response.status_code}\nURL: {url}')
    data = response.json()
    data['url'] = scryfall_url
    return cast(ScryfallCardSearchResponse, data)


def random_card_request(request: ScryfallRandomCardRequest) -> ScryfallCard | None:
    endpoint = 'cards/random'
    
    query_string = '&'.join([f"{key}={str(value).strip()}" for key, value in request.items() if value is not None])
    url = f"{BASE_URL}/{endpoint}?{query_string}"
    response = requests.get(url)
    if response.status_code != 200:
        if response.status_code == 404:
            return None
        raise Exception(f'Error fetching data from Scryfall API\nStatus: {response.status_code}\nURL: {url}')
    data = response.json()
    return cast(ScryfallCard, data)

def card_rulings_request(url:str)->ScryfallRulingsResponse:
    response = requests.get(url)
    if response.status_code != 200:
        if response.status_code == 404:
            return None
        raise Exception(f'Error fetching data from Scryfall API\nStatus: {response.status_code}\nURL: {url}')
    data = response.json()
    return cast(ScryfallRulingsResponse, data)