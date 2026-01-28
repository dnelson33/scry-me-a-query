import random

def get_random_color_identity():
    colors = ['W', 'U', 'B', 'R', 'G']
    identity = ''
    for color in colors:
        if random.choice([True, False]):
            identity += color
    if identity == '':
        identity = random.choice(colors)
    return identity

def get_random_creature_type():
#   TODO: Replace with https://api.scryfall.com/catalog/creature-types on load.
    return False;