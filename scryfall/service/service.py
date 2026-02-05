from scryfall.api import card_search_request, random_card_request
from scryfall.api.types import ScryfallCardSearchRequest, ScryfallCardSearchResponse, ScryfallCard, ScryfallOrder
from scryfall.service.types import CardSearchResponse, PageInfo, ScryQueryCard
import re
from typing import List

def card_search(search_text:str, page:int=None) -> CardSearchResponse:
    q = search_text
    order = ScryfallOrder.EDHREC.value
    
    # Get order from search_text and remove it from q
    m = re.search(r'(?<!\w)order:(\S+)', search_text)
    if m:
        order = m.group(1)
        q = re.sub(r'(?<!\w)order:\S+', '', q).strip()
    
    # Get format from search_text and remove it from q if it is 'any'
    if not any(x in q for x in ['legal:', 'format:', 'f:']):
        q += ' f:edh'
    if 'f:any' in search_text:
        q = q.replace('f:any', '')
          
    request: ScryfallCardSearchRequest = {
        'q': q,
        'order': order,
        'page': page
    }
    api_response = card_search_request(request)
    
    card_search_response: CardSearchResponse = {
        'scryfall_url': api_response['url'],
        'total_cards': api_response['total_cards'],
        'pages': _get_pages(api_response),
        'cards': [_map_card(card) for card in api_response['data']]
    }
    return card_search_response

def random_card(search_text:str) -> ScryQueryCard:
    api_response = random_card_request({
        'q': search_text
    })
    return _map_card(api_response)
    
    
def _get_pages(api_response: ScryfallCardSearchResponse) -> List[PageInfo]:
    if not api_response.get('next_page'):
        return [{ 'page_number': 1, 'page_url': api_response['url'] }]
    
    pages = []
    total_cards = api_response['total_cards']
    cards_per_page = len(api_response['data'])
    total_pages = total_cards // cards_per_page
    
    base_url = api_response['next_page']
    for page_number in range(1, total_pages):
        page_url = re.sub('page=\\d*', f'page={page_number}', base_url)
        pages.append({
            'page_number': page_number,
            'page_url': page_url
        })
    return pages

def _map_card(scryfall_card: ScryfallCard) -> ScryQueryCard:
    image_uri = scryfall_card.get('image_uris', {}).get('png')
    if not image_uri and scryfall_card.get('card_faces'):
        image_uri = scryfall_card['card_faces'][0].get('image_uris', {}).get('png', '')
    
    prices = scryfall_card.get('prices', {})
    price = prices.get("usd", prices.get("usd_foil", None))
    
    return {
        'scryfall_url': scryfall_card['scryfall_uri'],
        'image_uri': image_uri,
        'name': scryfall_card['name'],
        'mana_cost': scryfall_card.get('mana_cost'),
        'type_line': scryfall_card.get('type_line'),
        'oracle_text': scryfall_card.get('oracle_text'),
        'price': float(price) if price else None,
        'price_foil': float(prices.get("usd_foil")) if prices.get("usd_foil") else None
    }
