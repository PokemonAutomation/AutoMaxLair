"""Object for storing and processing information related to a Dynamax
Adventure in Pokemon Sword and Shield: the Crown Tundra.
"""

#   MaxLairInstance
#       Eric Donders
#       Contributions from Miguel Tavera and Discord users denvoros and pifopi
#       Last updated 2021-01-08
#       Created 2020-11-20

from typing import List

import jsonpickle


class MaxLairInstance:
    """An object for storing and processing information related to a Dynamax
    Adventure in Pokemon Sword and Shield: the Crown Tundra.
    """

    # pylint: disable=too-many-instance-attributes
    # This class is a storage container, so having many attributes is sensible.

    def __init__(self, data_paths: List) -> None:
        self.pokemon = None
        self.HP = 1  # 1 = 100%
        self.num_caught = 0
        self.caught_pokemon = []
        self.lives = 4
        self.path_pokemon_types = [
            [None, None], [None, None, None, None], [None, None, None, None]]
        self.path_type = None

        self.reset_stage()
        # Load precalculated resources for choosing Pokemon and moves
        with open(data_paths[0], 'r', encoding='utf8') as file:
            self.boss_pokemon = jsonpickle.decode(file.read())
        with open(data_paths[1], 'r', encoding='utf8') as file:
            self.rental_pokemon = jsonpickle.decode(file.read())
        with open(data_paths[2], 'r', encoding='utf8') as file:
            self.boss_matchups = jsonpickle.decode(file.read())
        with open(data_paths[3], 'r', encoding='utf8') as file:
            self.rental_matchups = jsonpickle.decode(file.read())
        with open(data_paths[4], 'r', encoding='utf8') as file:
            self.rental_scores = jsonpickle.decode(file.read())

    def reset_stage(self) -> None:
        """Reset after a battle."""
        self.move_index = 0
        self.dmax_timer = -1
        self.opponent = None
        self.dynamax_available = False
        if self.pokemon is not None:
            if self.pokemon.name_id == 'ditto':
                self.pokemon = self.rental_pokemon['ditto']
            self.pokemon.dynamax = False

    def update_pokemon_types(self, type_data: List, index: int) -> None:
        """Update the internal path storage."""
        self.path_pokemon_types[index] = type_data

        if index == 1:
            y_values = []
            for result in type_data:
                y_values.append(result[1][1][1])
            max_val = max(y_values)
            min_val = min(y_values)
            diff = max_val - min_val
            # Standard values provided by MaruBatsu72
            standard_vals = {135: '2x2', 180: '2x3', 65: '3x2'}
            closest_match = min(
                standard_vals.keys(), key=lambda x: abs(x-diff))
            self.path_type = standard_vals[closest_match]