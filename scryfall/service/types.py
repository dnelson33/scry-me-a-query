from typing import TypedDict, List, Optional

class ScryQueryCard(TypedDict):
    scryfall_url: str
    image_uri: str
    name: str
    mana_cost: Optional[str]
    type_line: str
    oracle_text: Optional[str]
    price: Optional[float]
    price_foil: Optional[float]
    flavor_text: Optional[str]
    rulings_url: Optional[str]
    cmc: Optional[float]
    

class PageInfo(TypedDict):
    page_number: int
    page_url: str
    
class CardSearchResponse(TypedDict):
    scryfall_url: str
    total_cards: int
    pages: List[PageInfo]
    cards: List[ScryQueryCard]

class CardRuling(TypedDict):
    ruling_text: str
    source: str
    published_at: str
        
class CardRulingsResponse(TypedDict):
    card: ScryQueryCard
    rulings: List[CardRuling]
    
class RandomCardRulingResponse(TypedDict):
    card: ScryQueryCard
    ruling: Optional[CardRuling]