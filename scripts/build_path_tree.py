"""Tree training and building for basic path selection

This is not some crazy smart algorithm, but is designed simply
to update store all path possiblities that might arise while returning
simple score values.
"""

import jsonpickle
from scripts.package_pokemon import pokemon_from_txt
from automaxlair.path_tree import PathTree
import sys
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)


def argmax(pairs):
    """Function to return the argmax of a set of pairs"""
    return max(pairs, key=lambda x: x[1])[0]


def argmax_index(values):
    """Function to take advantage of argmax so you can use one list"""
    return argmax(enumerate(values))


if __name__ == "__main__":

    with open(base_dir + '/data/rental_pokemon.json', 'r', encoding='utf8') as file:
        rental_pokemon = jsonpickle.decode(file.read())

    with open(base_dir + '/data/boss_pokemon.json', 'r', encoding='utf8') as file:
        boss_pokemon = jsonpickle.decode(file.read())

    tree = PathTree(rental_pokemon=rental_pokemon, boss_pokemon=boss_pokemon)

    # save the tree to pickle
    with open(base_dir + '/data/path_tree.pickle', 'w', encoding='utf8') as file:
        file.write(jsonpickle.encode(tree, indent=4))

    legendary = 'articuno'

    test_paths = [
        ['rock', 'rock', 'rock'],
        ['rock', 'fire', 'fighting'],
        ['rock', 'normal', 'fighting'],
        ['dark', 'fire', 'fighting'],
        ['ground', 'fire', 'water'],
        ['water', 'electric', 'grass']
    ]

    path_scores = []

    for test_path in test_paths:
        path_scores.append(tree.score_path(legendary, test_path))

    best_idx = argmax(path_scores)

    print(
        f"Best path found to be {path_scores[path_scores]} for {test_paths[path_scores]}")
