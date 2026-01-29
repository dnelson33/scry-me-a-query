from typing import TypedDict, List, Optional
from enum import Enum

class ScyrfallImageUris(TypedDict):
    small: str
    normal: str
    large: str
    png: str
    art_crop: str
    border_crop: str
    
class ScryfallPrices(TypedDict):
    usd: str
    usd_foil: str
    eur: str
    tix: str

class ScryfallPurchaseUris(TypedDict):
    tcgplayer: str
    cardmarket: str
    cardhoarder: str

class ScryfallCardFace(TypedDict):
    name: str
    mana_cost: str
    type_line: str
    oracle_text: str
    colors: List[str]
    power: str
    toughness: str
    image_uris: ScyrfallImageUris
   
class ScryfallUnique(Enum):
    CARDS = 'cards'
    ART = 'art'
    PRINTS = 'prints'
    
class ScryfallOrder(Enum):
    NAME = 'name'
    RELEASED = 'released'
    COLOR = 'color'
    TYPE = 'type'
    CMC = 'cmc'
    POWER = 'power'
    TOUGHNESS = 'toughness'
    EDHREC = 'edhrec'

class ScryfallOrderDir(Enum):
    AUTO = 'auto'
    ASC = 'asc'
    DESC = 'desc'    
     
class ScryfallCard(TypedDict):
    id: str
    name: str
    released_at: str
    uri: str
    scryfall_uri: str
    image_uris: ScyrfallImageUris
    mana_cost: str
    cmc: float
    type_line: str
    oracle_text: str
    power: Optional[str]
    toughness: Optional[str]
    colors: List[str]
    color_identity: List[str]
    keywords: List[str]
    legalities: dict
    reserved: bool
    foil: bool
    nonfoil: bool
    game_changer: bool
    reprint: bool
    set_id: str
    set_name: str
    set_uri: str
    set_search_uri: str
    scryfall_set_uri: str
    rulings_uri: str
    prints_search_uri: str
    collector_number: str
    rarity: str
    artist: str
    flavor_text: str
    prices: ScryfallPrices
    purchase_uris: ScryfallPurchaseUris
    produced_mana: Optional[List[str]]
    card_faces: Optional[List[ScryfallCardFace]]

class ScryfallCardSearchRequest(TypedDict):
    q: Optional[str]
    order: Optional[ScryfallOrder]
    unique: Optional[ScryfallUnique] 
    dir: Optional[str]
    include_extras: Optional[bool]
    include_multilingual: Optional[bool]
    include_variations: Optional[bool]
    page: Optional[int]
    format: Optional[str]
    pretty: Optional[bool]
    
class ScryfallCardSearchResponse(TypedDict):
    url: str
    total_cards: int
    has_more: bool
    next_page: Optional[str]
    data: List[ScryfallCard]
    

class ScryfallRandomCardRequest(TypedDict):
    q: Optional[str]
    format: Optional[str]
    face: Optional[str]
    version: Optional[str]
    pretty: Optional[bool]