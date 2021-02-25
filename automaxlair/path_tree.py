import logging
import pickle
import sys
import os

from typing import List, Tuple
# We need to import some things from the parent directory.
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, os.path.join(base_dir, 'automaxlair'))

# Needs to be lower than path insert.
from automaxlair import matchup_scoring  # noqa: E402


TYPE_LIST = [
    'normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting',
    'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost',
    'dragon', 'dark', 'steel', 'fairy']


class PathTree():
    """A basic tree object for determining a better path to follow

    Upon initialization, it takes all of the available rental pokemon and boss
    pokemon and builds up a tree that gives a score for each possible path
    of three types (for example, 'fire', 'grass', 'water') for each boss Pokemon
    available.

    Do note that this tree does *not* take into account potential party members!
    This is merely a basic tree that provides simple pre-calculated scores to help
    determine a path that's potentially more likely than always choosing the left-most
    path.

    There is certainly room here to improve upon this algorithm by including
    the current team, the chance that someone will take the pokemon, and more.
    But for now, a simple tree structure that stores scores for each is better
    than nothing.

    As for using this tree, it should be trained automatically with a distributed
    pickle file for loading in later. Once the pickle is loaded (or the tree trained)
    it is just a matter of calling the `score_path` method with a list that contains
    your path. Make sure the path is formatted in the following way:
    ['boss', 'type1', 'type2', 'type3'] with strings identical to those
    found in TYPE_LIST (shouldn't be a problem for the rest of the script).
    """

    def __init__(self, load_tree_path=None, rental_pokemon=None, boss_pokemon=None):

        # TREE DEPTH OVERRIDE
        self.tree_depth = 1

        # find all of the pokemon by type, both primary and secondary
        if rental_pokemon is not None:
            self.rental_by_type = {}
            for type_name in TYPE_LIST:
                pokemon_names_by_type = []
                logging.info(f"Now finding Pokemon by {type_name} type!")
                for pokemon_name, pokemon in rental_pokemon.items():
                    if type_name in pokemon.type_ids:
                        pokemon_names_by_type.append(pokemon_name)
                self.rental_by_type[type_name] = pokemon_names_by_type
        elif load_tree_path is None:
            raise AttributeError(
                "Either rental pokemon or load tree needs to be added!")

        if load_tree_path is None:
            self._build_tree(rental_pokemon, boss_pokemon)
        else:
            self.base_node = pickle.load(load_tree_path)

    def score_path(self, legendary: str, path: list) -> float:
        """Return the pre-calculated score for a particular path

        This method tells the stored tree to traverse its paths for
        the current legendary, the first type in the path, the second
        type in the path, and then the third type in the path.

        The results can then be combined 

        boss: 'articuno'
        path: ['type1', 'type2', 'type3']
        """

        if self.tree_depth == 1:
            legendary_tree_node = self.base_node.get_node_for_key(legendary)

            # then build up the scores and scale them based on position
            outscore = 0.0
            for ii, type_name in enumerate(path):
                base_score = legendary_tree_node.get_node_for_key(type_name)
                # the formula for now helps weight the order you find
                # the type in, so deeper paths might be more useful
                # since you get a PP restore *and* type advantage
                outscore += (1.0 + (ii * 0.1)) * base_score
            
            return outscore

        else:
            return self.base_node.traverse_node([legendary] + path, 0)

    def get_best_path(
        self, legendary: str, path_list: List[List[str]]
    ) -> Tuple[float, List[str], List[float]]:
        """Choose the best path out of a list of paths."""
        path_scores = []
        for path in path_list:
            path_scores.append(self.score_path(legendary, path))
        best_index = path_scores.index(max(path_scores))
        return best_index, path_list[best_index], path_scores

    def _build_tree(self, rental_pokemon, boss_pokemon):
        self.base_node = TreeNode(legendary=True)

        for ii, (legendary_name, legendary) in enumerate(boss_pokemon.items()):
            print(
                f"{ii+1:02d}/{len(boss_pokemon)} : Calculating for {legendary_name}")
            self.base_node.add_node(legendary_name, self._build_node_for_types(
                current_score=0.0, legendary=legendary, rental_pokemon=rental_pokemon, path_num=0
            ))

    def _build_node_for_types(self, current_score, legendary, rental_pokemon, path_num=0):

        current_node = TreeNode(legendary=False)

        for type_name in TYPE_LIST:
            # calculate the score
            # if path_num == 2:
            #     print(f"{type_name} ", end="" if type_name != 'fairy' else "\n")
            # else:
            #     print(f"{'  '*path_num} path {path_num+1} : {type_name}",
            #           end="\n" if path_num < 1 else "\n      ")

            possible_pokemon = []
            for pokemon_name in self.rental_by_type[type_name]:
                possible_pokemon.append(rental_pokemon[pokemon_name])

            type_score = self.calculate_score(possible_pokemon, legendary)
            # there are only a total of three paths, so we only add nodes to the tree
            # if we're less than 2 (ex. 0 and 1 for first two paths)
            # if path_num < 2:
            #     # then pass through the tree to the next node through a recursive process to
            #     # build up the tree
            #     current_node.add_node(type_name, self._build_node_for_types(
            #         current_score=current_score+type_score, legendary=legendary, rental_pokemon=rental_pokemon,
            #         path_num=path_num+1
            #     ))
            # else:
            #     current_node.add_node(type_name, current_score + type_score)
            
            # FOR NOW, NO RECURSION - TODO: modify algorithm for this to make sense
            current_node.add_node(type_name, type_score)

        return current_node

    def calculate_score(self, possible_pokemon, legendary):
        # just pass things through some kind of algorithm that determines an average score
        # *just* based on type

        the_score = 0.0

        for pokemon in possible_pokemon:
            the_score += matchup_scoring.evaluate_matchup(pokemon, legendary)

        the_score /= len(possible_pokemon)

        return the_score


class TreeNode:
    def __init__(self, legendary=False):
        if legendary:
            self.hash_table = {}
        else:
            self.hash_table = {key: None for key in TYPE_LIST}

    def add_node(self, key, value):
        self.hash_table[key] = value

    def traverse_node(self, list_of_decisions, current_idx=0):

        if type(self.hash_table[list_of_decisions[current_idx]]) == TreeNode:
            return self.hash_table[list_of_decisions[current_idx]].traverse_node(list_of_decisions, current_idx+1)
        else:
            return self.hash_table[list_of_decisions[current_idx]]
        
    def get_node_for_key(self, key):
        # no matter what, this only returns what is assigned to the hash table
        # for that particular key
        return self.hash_table[key]
