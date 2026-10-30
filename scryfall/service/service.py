from scryfall.api import card_search_request, random_card_request, card_rulings_request
from scryfall.api.types import ScryfallCardSearchRequest, ScryfallCardSearchResponse, ScryfallCard, ScryfallOrder, ScryfallUnique
from scryfall.service.types import CardSearchResponse, PageInfo, ScryQueryCard, CardRulingsResponse, RandomCardRulingResponse
import re
from typing import List, Tuple
from random import randint

ORDER_PATTERN = re.compile(r'(?<!\w)order:(\S+)', re.IGNORECASE)
FORMAT_PATTERN = re.compile(r'(?<!\w)(?:f|format|legal):\S+', re.IGNORECASE)
VALID_ORDERS = {order.value for order in ScryfallOrder}

def _prepare_query(search_text: str) -> Tuple[str, str]:
    """Split Scryfall modifiers out of a user query before it is encoded.

    Modifiers must be parsed from the raw text: once the query is URL-encoded,
    tokens like ``order:cmc`` become ``order%3Acmc`` and no longer match.
    """
    q = (search_text or '').strip()
    order = ScryfallOrder.EDHREC.value

    match = ORDER_PATTERN.search(q)
    if match:
        candidate = match.group(1).lower()
        if candidate in VALID_ORDERS:
            order = candidate
        q = (q[:match.start()] + q[match.end():]).strip()

    # Respect any explicit format/legality filter, including f:any. Otherwise
    # default searches to Commander-legal cards.
    if not FORMAT_PATTERN.search(q):
        q = f'{q} f:edh'.strip()

    return re.sub(r'\s+', ' ', q).strip(), order

def card_search(search_text:str, page:int=None, unique:ScryfallUnique=None) -> CardSearchResponse:
    q, order = _prepare_query(search_text)

    request: ScryfallCardSearchRequest = {
        'q': q,
        'order': order,
        'page': page,
        'unique': unique.value if unique else None
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
        'q': search_text or ''
    })
    return _map_card(api_response)
    
def get_rulings(card: ScryQueryCard)->CardRulingsResponse:
    rulings_url = card['rulings_url']
    
    if not rulings_url:
        rulings = []
    else:
        api_response = card_rulings_request(card['rulings_url'])
        rulings = [{ 'ruling_text': r.get('comment'), 'published_at': r.get('published_at'), 'source': r.get('source') } for r in api_response.get('data', [])]
    
    return {
        'card': card,
        'rulings': rulings
    }
    
def get_random_card_ruling(search_text: str)->RandomCardRulingResponse:
    card = random_card(search_text)
    rulings_response = get_rulings(card)
    rulings = rulings_response.get('rulings', [])
    rulings_count = len(rulings)
    if rulings_response and rulings_count > 0:
        rnd = randint(0, rulings_count - 1)
        return {
            'card': card,
            'ruling': rulings[rnd]
        }
    return {
        'card': card,
        'ruling': None
    }
    
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
    if scryfall_card.get('card_faces'):
        front = scryfall_card['card_faces'][0]
        back = scryfall_card['card_faces'][1] if len(scryfall_card['card_faces']) > 1 else front
        image_uri = front.get('image_uris', {}).get('normal') or scryfall_card.get('image_uris', {}).get('normal', '')
        oracle_text = f'{front['oracle_text']}\n // \n{back['oracle_text']}'
        type_line = f'{front['type_line']} // {back['type_line']}' if back.get('type_line') else front.get('type_line')
        mana_cost = f'{front.get('mana_cost')} // {back.get('mana_cost')}' if back.get('mana_cost') else front.get('mana_cost')
    else:
        image_uri = scryfall_card.get('image_uris', {}).get('normal')
        oracle_text = scryfall_card.get('oracle_text')
        mana_cost = scryfall_card.get('mana_cost')
        type_line = scryfall_card.get('type_line')
    
    
    prices = scryfall_card.get('prices', {})
    price = prices.get("usd", prices.get("usd_foil", None))
    
    return {
        'scryfall_url': scryfall_card['scryfall_uri'],
        'image_uri': image_uri,
        'name': scryfall_card['name'],
        'mana_cost': mana_cost,
        'type_line': type_line,
        'oracle_text': oracle_text,
        'price': float(price) if price else None,
        'price_foil': float(prices.get("usd_foil")) if prices.get("usd_foil") else None,
        'flavor_text': scryfall_card.get('flavor_text'),
        'rulings_url': scryfall_card.get('rulings_uri'),
        'cmc': scryfall_card.get('cmc', 0)
    }
