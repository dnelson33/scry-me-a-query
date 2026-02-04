from typing import TypedDict, List, Optional

class ScryQueryCard(TypedDict):
    scryfall_url: str
    image_uri: str

class PageInfo(TypedDict):
    page_number: int
    page_url: str
    
class CardSearchResponse(TypedDict):
    scryfall_url: str
    total_cards: int
    pages: List[PageInfo]
    cards: List[ScryQueryCard]