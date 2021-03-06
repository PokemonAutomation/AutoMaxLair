"""Script for testing and viewing stored Pokemon and matchups."""

import os
import pickle
import sys
import jsonpickle

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, os.path.join(base_dir, 'automaxlair'))

from automaxlair import matchup_scoring  # noqa: E402


def main():
    with open(
        os.path.join(base_dir, 'data', 'boss_pokemon.json'), 'r',
        encoding='utf8'
    ) as file:
        boss_pokemon = jsonpickle.decode(file.read())
    with open(
        os.path.join(base_dir, 'data', 'rental_pokemon.json'), 'r',
        encoding='utf8'
    ) as file:
        rental_pokemon = jsonpickle.decode(file.read())
    with open(
        os.path.join(base_dir, 'data', 'boss_matchup_LUT.json'), 'r',
        encoding='utf8'
    ) as file:
        boss_matchups = jsonpickle.decode(file.read())
    with open(
        os.path.join(base_dir, 'data', 'rental_matchup_LUT.json'), 'r',
        encoding='utf8'
    ) as file:
        rental_matchups = jsonpickle.decode(file.read())
    with open(
        os.path.join(base_dir, 'data', 'rental_pokemon_scores.json'), 'r',
        encoding='utf8'
    ) as file:
        rental_scores = jsonpickle.decode(file.read())

    # Test retrieval of a rental Pokemon
    rental_pokemon['stunfisk-galar'].print_verbose()
    print('________________________________________')

    # Test retrieval of a boss Pokemon
    boss_pokemon['mewtwo'].print_verbose()
    print('________________________________________')

    # Test retrieval of rental Pokemon matchups
    print(
        'Matchup for Chansey against Golurk (poor): '
        f'{rental_matchups["chansey"]["golurk"]}')
    print(
        'Matchup for Carkol against Butterfree (good): '
        f'{rental_matchups["carkol"]["butterfree"]}')
    print('________________________________________')

    # Test retrieval of boss Pokemon matchups
    print(
        'Matchup for Jynx against Heatran (poor): '
        f'{boss_matchups["jynx"]["heatran"]}')
    print(
        'Matchup for Golurk against Raikou (good): '
        f'{boss_matchups["golurk"]["raikou"]}')
    print('________________________________________')

    # Test retrieval of rental Pokemon scores
    print(f'Score for Jigglypuff (poor): {rental_scores["jigglypuff"]}')
    print(f'Score for Doublade (good): {rental_scores["doublade"]}')
    print('________________________________________')

    # Test move selection
    print('Wide Guard utility:')
    matchup_scoring.print_matchup_summary(
        rental_pokemon['pelipper'], boss_pokemon['groudon'], rental_pokemon
    )
    salazzle = rental_pokemon['salazzle']
    print('Regular matchup:')
    matchup_scoring.print_matchup_summary(
        salazzle, boss_pokemon['kartana'], rental_pokemon
    )
    print('Max move scores:')
    salazzle.dynamax = True
    matchup_scoring.print_matchup_summary(
        salazzle, boss_pokemon['kartana'], rental_pokemon
    )
    print('Sap Sipper:')
    matchup_scoring.print_matchup_summary(
        rental_pokemon['tsareena'], rental_pokemon['azumarill'], rental_pokemon
    )
    print('________________________________________')

    # Ensure all rental Pokemon have sprites
    with open(
        os.path.join(base_dir, 'data', 'pokemon_sprites.pickle'), 'rb'
    ) as file:
        pokemon_sprites = pickle.load(file)
    pokemon_sprites_dict = dict(pokemon_sprites)
    for name_id in rental_pokemon:
        if pokemon_sprites_dict.get(name_id) is None:
            raise KeyError(f'ERROR: no image found for: {name_id}')
    print('Successfully tested Pokemon sprite importing without errors.')


if __name__ == '__main__':
    main()
