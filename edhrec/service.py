from pyedhrec import EDHRec
from edhrec.types import EDHRecCommander
def get_edhrec_stats(card_name: str) -> EDHRecCommander:
    try:
        edhrec = EDHRec()
        card_data = edhrec.get_commander_data(card_name)
        if card_data:
            card = card_data.get('container', {}).get('json_dict', {}).get('card', {})
            response = {
                'rank': card.get('rank'),
                'commander_deck_count': card.get('num_decks'),
                'salt': card.get('salt'),
            }
            return response
    except Exception as e:
        print(f"Error fetching EDHRec data for {card_name}: {e}")

    return None