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
  creature_types = creature_types = [
    "Advisor", "Aetherborn", "Alien", "Ally", "Angel", "Antelope", "Ape", 
    "Archer", "Archon", "Armadillo", "Army", "Artificer", "Assassin", 
    "Assembly-Worker", "Astartes", "Atog", "Aurochs", "Avatar", "Azra", 
    "Badger", "Balloon", "Barbarian", "Bard", "Basilisk", "Bat", "Beaver", 
    "Bear", "Beast", "Beeble", "Beholder", "Berserker", "Bird", "Blinkmoth", 
    "Boar", "Bringer", "Brushwagg", "Camarid", "Camel", "Capybara", "Caribou", 
    "Carrier", "Cat", "Centaur", "Child", "Chimera", "Citizen", "Cleric", 
    "Clown", "Cockatrice", "Construct", "Coward", "Coyote", "Crab", "Crocodile", 
    "C'tan", "Custodes", "Cyberman", "Cyclops", "Dalek", "Dauthi", "Demigod", 
    "Demon", "Deserter", "Detective", "Devil", "Dinosaur", "Djinn", "Doctor", 
    "Dog", "Dragon", "Drake", "Dreadnought", "Drone", "Druid", "Dryad", "Dwarf", 
    "Efreet", "Egg", "Elder", "Eldrazi", "Elemental", "Elephant", "Elf", "Elk", 
    "Employee", "Eye", "Faerie", "Ferret", "Fish", "Flagbearer", "Fox", "Fractal", 
    "Frog", "Fungus", "Gamer", "Gargoyle", "Germ", "Giant", "Gith", "Glimmer", 
    "Gnoll", "Gnome", "Goat", "Goblin", "God", "Golem", "Gorgon", "Graveborn", 
    "Gremlin", "Griffin", "Guest", "Hag", "Halfling", "Hamster", "Harpy", 
    "Hellion", "Hero", "Hippo", "Hippogriff", "Homarid", "Homunculus", "Horror", 
    "Horse", "Human", "Hydra", "Hyena", "Illusion", "Imp", "Incarnation", 
    "Inkling", "Inquisitor", "Insect", "Jackal", "Jellyfish", "Juggernaut", 
    "Kavu", "Kirin", "Kithkin", "Knight", "Kobold", "Kor", "Kraken", "Lamia", 
    "Lammasu", "Leech", "Leviathan", "Lhurgoyf", "Licid", "Lizard", "Llama", 
    "Manticore", "Masticore", "Mercenary", "Merfolk", "Metathran", "Minion", 
    "Minotaur", "Mite", "Mole", "Monger", "Mongoose", "Monk", "Monkey", 
    "Moonfolk", "Mount", "Mouse", "Mutant", "Myr", "Mystic", "Nautilus", 
    "Necron", "Nephilim", "Nightmare", "Nightstalker", "Ninja", "Noble", 
    "Noggle", "Nomad", "Nymph", "Octopus", "Ogre", "Ooze", "Orb", "Orc", 
    "Orgg", "Otter", "Ouphe", "Ox", "Oyster", "Pangolin", "Peasant", "Pegasus", 
    "Pentavite", "Performer", "Pest", "Phelddagrif", "Phoenix", "Phyrexian", 
    "Pilot", "Pincher", "Pirate", "Plant", "Porcupine", "Possum", "Praetor", 
    "Primarch", "Prism", "Processor", "Raccoon", "Rabbit", "Ranger", "Rat", 
    "Rebel", "Reflection", "Rhino", "Rigger", "Robot", "Rogue", "Sable", 
    "Salamander", "Samurai", "Sand", "Saproling", "Satyr", "Scarecrow", 
    "Scientist", "Scion", "Scorpion", "Scout", "Sculpture", "Serf", "Serpent", 
    "Servo", "Shade", "Shaman", "Shapeshifter", "Shark", "Sheep", "Siren", 
    "Skeleton", "Skunk", "Slith", "Sliver", "Sloth", "Slug", "Snail", "Snake", 
    "Soldier", "Soltari", "Spawn", "Specter", "Spellshaper", "Sphinx", "Spider", 
    "Spike", "Spirit", "Splinter", "Sponge", "Squid", "Squirrel", "Starfish", 
    "Surrakar", "Survivor", "Synth", "Tentacle", "Tetravite", "Thalakos", 
    "Thopter", "Thrull", "Tiefling", "Time Lord", "Toy", "Treefolk", "Trilobite", 
    "Triskelavite", "Troll", "Turtle", "Tyranid", "Unicorn", "Vampire", 
    "Varmint", "Vedalken", "Villain", "Volver", "Wall", "Walrus", "Warlock", 
    "Warrior", "Weasel", "Weird", "Werewolf", "Whale", "Wizard", "Wolf", 
    "Wolverine", "Wombat", "Worm", "Wraith", "Wurm", "Yeti", "Zombie", "Zubera"
  ]
  return random.choice(creature_types)