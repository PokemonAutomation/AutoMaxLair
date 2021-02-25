"""Tree training and building for basic path selection

This is not some crazy smart algorithm, but is designed simply
to update store all path possiblities that might arise while returning
simple score values.
"""

import sys
from os.path import abspath, dirname

base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)

import jsonpickle
from automaxlair.path_tree import PathTree

from scripts.package_pokemon import pokemon_from_txt


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
    with open(base_dir + '/data/path_tree.json', 'w', encoding='utf8') as file:
        file.write(jsonpickle.encode(tree, indent=4))

    legendary = 'articuno'

    test_paths = [
        ['rock', 'rock', 'rock'],
        ['rock', 'fire', 'fighting'],
        ['rock', 'normal', 'rock'],
        ['dark', 'fire', 'fighting'],
        ['ground', 'fire', 'water'],
        ['water', 'electric', 'grass'],
        ['fire', 'rock', 'fire']
    ]

    path_scores = []

    for test_path in test_paths:
        path_scores.append(tree.score_path(legendary, test_path))

    print(path_scores)

    best_idx = argmax_index(path_scores)

    print(
        f"Best path found to be {test_paths[best_idx]} with score {path_scores[best_idx]} for {legendary}")
