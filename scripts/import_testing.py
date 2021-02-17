import jsonpickle
import sys

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, base_dir + '\\automaxlair')

from automaxlair import matchup_scoring


def main():
    with open(base_dir + '/data/boss_pokemon.json', 'r', encoding='utf8') as file:
        boss_pokemon = jsonpickle.decode(file.read())
    with open(base_dir + '/data/rental_pokemon.json', 'r', encoding='utf8') as file:
        rental_pokemon = jsonpickle.decode(file.read())
    with open(base_dir + '/data/boss_matchup_LUT.json', 'r', encoding='utf8') as file:
        boss_matchups = jsonpickle.decode(file.read())
    with open(base_dir + '/data/rental_matchup_LUT.json', 'r', encoding='utf8') as file:
        rental_matchups = jsonpickle.decode(file.read())
    with open(base_dir + '/data/rental_pokemon_scores.json', 'r', encoding='utf8') as file:
        rental_scores = jsonpickle.decode(file.read())

    # Test retrieval of a rental Pokemon
    rental_pokemon['stunfisk-galar'].print_verbose()
    print('________________________________________')

    # Test retrieval of a boss Pokemon
    boss_pokemon['mewtwo'].print_verbose()
    print('________________________________________')

    # Test retrieval of rental Pokemon matchups
    print(
        f'Matchup for Chansey against Golurk (poor): {rental_matchups["chansey"]["golurk"]}')
    print(
        f'Matchup for Carkol against Butterfree (good): {rental_matchups["carkol"]["butterfree"]}')
    print('________________________________________')

    # Test retrieval of boss Pokemon matchups
    print(
        f'Matchup for Jynx against Heatran (poor): {boss_matchups["jynx"]["heatran"]}')
    print(
        f'Matchup for Golurk against Raikou (good): {boss_matchups["golurk"]["raikou"]}')
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


if __name__ == '__main__':
    main()
