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
from automaxlair.field import Field


def test_terrain(rental_pokemon, boss_pokemon):
    print('Terrain tests')
    field_clear = Field()
    field_clear.set_terrain_clear()

    field_electric = Field()
    field_electric.set_terrain_electric()

    field_psychic = Field()
    field_psychic.set_terrain_psychic()

    field_grassy = Field()
    field_grassy.set_terrain_grassy()

    field_misty = Field()
    field_misty.set_terrain_misty()
    print('electric move (clear / electric / psychic / grassy / misty)')
    for field in [field_clear, field_electric, field_psychic, field_grassy, field_misty]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['electabuzz'], 1, boss_pokemon['guzzlord'], field)
        print(f'Damage is {dmg}')

    print('rising voltage (clear / electric / psychic / grassy / misty)')
    for field in [field_clear, field_electric, field_psychic, field_grassy, field_misty]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['electabuzz'], 0, boss_pokemon['guzzlord'], field)
        print(f'Damage is {dmg}')

    print('psychic move (clear / electric / psychic / grassy / misty)')
    for field in [field_clear, field_electric, field_psychic, field_grassy, field_misty]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['slowbro'], 3, rental_pokemon['electabuzz'], field)
        print(f'Damage is {dmg}')

    print('expanding force (clear / electric / psychic / grassy / misty)')
    for field in [field_clear, field_electric, field_psychic, field_grassy, field_misty]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['slowbro'], 0, rental_pokemon['electabuzz'], field)
        print(f'Damage is {dmg}')

    print('dragon move (clear / electric / psychic / grassy / misty)')
    for field in [field_clear, field_electric, field_psychic, field_grassy, field_misty]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['charmeleon'], 1, rental_pokemon['electabuzz'], field)
        print(f'Damage is {dmg}')

    print('grass move (clear / electric / psychic / grassy / misty)')
    for field in [field_clear, field_electric, field_psychic, field_grassy, field_misty]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['tangela'], 2, rental_pokemon['electabuzz'], field)
        print(f'Damage is {dmg}')


def test_weather(rental_pokemon, boss_pokemon):
    print('Weather tests')
    field_clear = Field()
    field_clear.set_weather_clear()

    field_rain = Field()
    field_rain.set_weather_rain()

    field_sandstorm = Field()
    field_sandstorm.set_weather_sandstorm()

    field_sunlingt = Field()
    field_sunlingt.set_weather_sunlight()

    field_hail = Field()
    field_hail.set_weather_hail()
    print('Solar beam (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['exeggutor'], 1, boss_pokemon['guzzlord'], field)
        print(f'Damage is {dmg}')

    print('Water attack (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['vaporeon'], 0, boss_pokemon['guzzlord'], field)
        print(f'Damage is {dmg}')

    print('Fire attack (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['flareon'], 0, boss_pokemon['guzzlord'], field)
        print(f'Damage is {dmg}')

    print('Weather ball attack vs ground type (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['roselia'], 2, rental_pokemon['marowak'], field)
        print(f'Damage is {dmg}')

    print('Weather ball attack vs flying type (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['roselia'], 2, rental_pokemon['unfezant'], field)
        print(f'Damage is {dmg}')

    print('Weather ball attack vs grass type (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['roselia'], 2, rental_pokemon['ivysaur'], field)
        print(f'Damage is {dmg}')

    print('Special attack vs rock type (clear / rain / sandstorm / sun / hail)')
    for field in [field_clear, field_rain, field_sandstorm, field_sunlingt, field_hail]:
        dmg = matchup_scoring.calculate_damage(rental_pokemon['roselia'], 0, rental_pokemon['sudowoodo'], field)
        print(f'Damage is {dmg}')


def test_field(rental_pokemon, boss_pokemon):
    print('Fields tests')
    test_weather(rental_pokemon, boss_pokemon)
    test_terrain(rental_pokemon, boss_pokemon)


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
        rental_pokemon['pelipper'], boss_pokemon['groudon'], Field(), rental_pokemon
    )
    salazzle = rental_pokemon['salazzle']
    print('Regular matchup:')
    matchup_scoring.print_matchup_summary(
        salazzle, boss_pokemon['kartana'], Field(), rental_pokemon
    )
    print('Max move scores:')
    salazzle.dynamax = True
    matchup_scoring.print_matchup_summary(
        salazzle, boss_pokemon['kartana'], Field(), rental_pokemon
    )
    print('Sap Sipper:')
    matchup_scoring.print_matchup_summary(
        rental_pokemon['tsareena'], rental_pokemon['azumarill'], Field(), rental_pokemon
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

    print('________________________________________')
    test_field(rental_pokemon, boss_pokemon)


if __name__ == '__main__':
    main()
