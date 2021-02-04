# Package Pokemon
#   Version 2
#   Eric Donders
#   2021-01-10
#   Read information on rental and boss Pokemon and construct dictionaries
#   which are stored as pickle files

import sys
import pickle

from typing import Tuple
from automaxlair import Pokemon, Move

import pokebase as pb

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)


def extract_name_dict(names_resource) -> dict:
    """Takes a names API resource and return a dict with the language as the key
    and the name as the value.
    """
    name_dict = {}
    for entry in names_resource:
        name_dict[entry.language.name] = entry.name

    return name_dict


def calculate_power(power, name_id: str) -> Tuple[float, float]:
    """Calculate base power and a correction factor that is applied to the base
    power of a move. This correction factor accounts for discrepencies between
    the base power of a move and its actual damage output in a turn. Examples
    where the base power is not reflective include: a) multi-hit moves, b)
    multi-turn moves, and c) moves that require certain conditions (e.g.,
    Dream Eater).
    """

    # The base power is the supplied power except for variable power moves
    # where we estimate an average power of 65 and status moves whose power
    # must be converted to 0 if it is None.
    base_power = power if name_id not in ('electro-ball', 'gyro-ball') else 65
    if base_power is None:
        base_power = 0

    # Calculate correction factor based on matching strings in the effect.
    factor = 1.0
    # Account for multi-turn moves.
    if (name_id in ('fly', 'dive', 'dig', 'bounce', 'sky-attack', 'solar-beam',
                    'hyper-beam', 'giga-impact', 'meteor-beam', 'razor-wind')):
        factor = 0.5
    elif name_id == 'future-sight':
        factor = 0.3
    # Account for conditional moves that require certain conditions
    # (Steel Roller, Dream Eater, Belch, etc.).
    elif name_id in ('steel-roller', 'dream-eater', 'belch'):
        factor = 0
    elif name_id == 'focus-punch':
        factor = 0.75
    # Account for multi-strike moves.
    elif name_id in ('bonemerang', 'double-hit', 'double-iron-bash',
                     'double-kick', 'dragon-darts', 'dual-chop',
                     'dual-wingbeat', 'gear-grind', 'twineedle'
                     ):
        factor = 2
    elif name_id in ('arm-thrust', 'barrage', 'bone-rush', 'bullet-seed',
                     'comet-punch', 'double-slap', 'fury-attack',
                     'fury-swipes', 'icicle-spear', 'pin-missile',
                     'rock-blast', 'scale-shot', 'spike-cannon',
                     'tail-slap', 'water-shuriken'):
        factor = 3.167
    elif name_id == 'triple-axel':
        factor = 5.23

    return base_power, factor


def get_moves(move_resource):
    """Build Move objects (base and Max) from a supplied API resource."""

    # Extract important values from the move resource.
    id_num = move_resource.id_
    name_id = move_resource.name
    names = extract_name_dict(move_resource.names)
    type_ = move_resource.type.name
    category = move_resource.damage_class.name
    accuracy_raw = move_resource.accuracy
    accuracy = 1 if accuracy_raw is None else accuracy_raw / 100
    PP = move_resource.pp
    effect = ''
    for entry in move_resource.effect_entries:
        if entry.language.name == 'en':
            effect = entry.short_effect
    probability = move_resource.effect_chance
    target = move_resource.target.name
    is_spread = target in ('all-other-pokemon', 'all-opponents')
    base_power, correction_factor = calculate_power(
        move_resource.power, name_id
    )

    # Then create a new Move object (and corresponding Max Move)
    # and add it to the list.
    move = Move(id_num, name_id, names, type_, category, base_power, accuracy,
                PP, effect, probability, is_spread, correction_factor
                )
    max_move = get_max_move(move)

    return move, max_move


def get_max_move(move):
    """Return the Max Move corresponding to the supplied regular move."""

    # Change the ID to the ID of the appropriate Max Move.
    if move.category == 'status':
        name_id = 'max-guard'
        type_id = 'normal'
        base_power = 0
    else:
        name_id = {'normal': 'max-strike', 'fighting': 'max-knuckle',
                   'flying': 'max-airstream', 'poison': 'max-ooze',
                   'ground': 'max-quake', 'rock': 'max-rockfall',
                   'bug': 'max-flutterby', 'ghost': 'max-phantasm',
                   'steel': 'max-steelspike', 'fire': 'max-flare',
                   'water': 'max-geyser', 'grass': 'max-overgrowth',
                   'electric': 'max-lightning', 'psychic': 'max-mindstorm',
                   'ice': 'max-hailstorm', 'dragon': 'max-wyrmwind',
                   'dark': 'max-darkness', 'fairy': 'max-starfall'
                   }[move.type_id]
        type_id = move.type_id

        # Calculate base power based on the original move.
        if type_id == 'fighting' or type_id == 'poison':
            if move.base_power < 10:
                base_power = 0
            elif move.base_power <= 40:
                base_power = 70
            elif move.base_power <= 50:
                base_power = 75
            elif move.base_power <= 60:
                base_power = 80
            elif move.base_power <= 70:
                base_power = 85
            elif move.base_power <= 100:
                base_power = 90
            elif move.base_power <= 140:
                base_power = 95
            else:
                base_power = 100
        else:
            if move.base_power < 10:
                base_power = 0
            elif move.base_power <= 40:
                base_power = 90
            elif move.base_power <= 50:
                base_power = 100
            elif move.base_power <= 60:
                base_power = 110
            elif move.base_power <= 70:
                base_power = 120
            elif move.base_power <= 100:
                base_power = 130
            elif move.base_power <= 140:
                base_power = 140
            else:
                base_power = 150

    # TODO: update the actual names with translations.

    # TODO: look up actual ID of the max move

    max_move_resource = pb.APIResource('move', name_id)
    id_num = max_move_resource.id_
    names = extract_name_dict(max_move_resource.names)

    # Instantiate a new move using the parameters calculated above.
    max_move = Move(id_num, name_id, names, type_id, move.category, base_power,
                    1, move.PP, '', 0
                    )
    return max_move


def pokemon_from_txt(filename: str, level: int) -> dict:
    """Generate a dictionary of Pokemon objects (with their names as the keys)
    from a text file.

    Each line of the file contains information on the pokemon in the format:
    pokemon-name,ability,*move-name where there is a variable number of moves.
    """

    pokemon_dict = {}

    with open(filename, 'r') as file:
        for line in file:
            # Unpack each line and then build the corresponding Pokemon using
            # PokeAPI (includes stats, names in all languages, et cetera).
            name_id, ability_id, *move_ids = line.strip('\n').split(',')

            # Information can be supplied as strings (e.g., 'stunfisk-galar')
            # or as numeric identifiers. Convert the numbers to ints if
            # appropriate.
            try:
                move_id_list = []
                name_id = int(name_id)
                ability_id = int(ability_id)
                for move_id in move_ids:
                    move_id_list.append(int(move_id))
                move_ids = tuple(move_id_list)
            except ValueError:
                # IDs were supplied as strings so continue.
                pass

            # Fetch information on the Pokemon from PokeAPI
            variant_resource = pb.APIResource('pokemon', name_id)
            variant_name = variant_resource.name
            species_name = variant_resource.species.name
            species_resource = pb.APIResource('pokemon-species', species_name)
            ability_resource = pb.APIResource('ability', ability_id)
            id_num = variant_resource.id_
            move_resources = []
            for move_id in move_ids:
                move_resources.append(pb.APIResource('move', move_id))

            # Load the Pokemon's types into a list.
            type_ids = []
            type_names = []
            for entry in variant_resource.types:
                type_name = entry.type.name
                type_ids.append(type_name)
                type_resource = pb.APIResource('type', type_name)
                type_names.append(extract_name_dict(type_resource.names))

            # Load the Pokemon's base stats into a list.
            stats = variant_resource.stats
            base_stats = (stats[0].base_stat, stats[1].base_stat,
                          stats[2].base_stat, stats[3].base_stat,
                          stats[4].base_stat, stats[5].base_stat
                          )

            # Load all of the Pokemon's names into a dict with the language as
            # the key.
            names = extract_name_dict(species_resource.names)

            # Load all of the ability's names into a dict with the language as
            # the key.
            ability_name_id = ability_resource.name
            # ability_num = ability_resource.id_
            abilities = extract_name_dict(ability_resource.names)

            # Construct a Move object for each move and store it in a list.
            moves = []
            max_moves = []
            for move_resource in move_resources:
                move, max_move = get_moves(move_resource)
                moves.append(move)
                max_moves.append(max_move)

            # Finally, create a new Pokemon object from the assembled
            # information and add it to the dict.
            pokemon = Pokemon(id_num, variant_name, names, ability_name_id,
                              abilities, type_ids, type_names, base_stats,
                              moves, max_moves, level=level
                              )
            pokemon_dict[variant_name] = pokemon

            # pokemon.print_verbose()  # DEBUG
            print(f'Finished loading {variant_name}')

    return pokemon_dict


def main():
    """Build Pokemon dictionaries from the text files and pickle the
    results.
    """

    rental_pokemon = pokemon_from_txt(base_dir + '/data/rental_pokemon.txt', 65)
    boss_pokemon = pokemon_from_txt(base_dir + '/data/boss_pokemon.txt', 70)

    # Pickle the Pokemon dictionaries for later use.
    with open(base_dir + '/data/rental_pokemon.pickle', 'wb') as file:
        pickle.dump(rental_pokemon, file)
    with open(base_dir + '/data/boss_pokemon.pickle', 'wb') as file:
        pickle.dump(boss_pokemon, file)
    print('Finished packaging Pokemon!')


if __name__ == '__main__':
    main()
