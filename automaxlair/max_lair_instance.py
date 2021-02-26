"""Object for storing and processing information related to a Dynamax
Adventure in Pokemon Sword and Shield: the Crown Tundra.
"""

#   MaxLairInstance
#       Eric Donders
#       Contributions from Miguel Tavera and Discord users denvoros and pifopi
#       Last updated 2021-01-08
#       Created 2020-11-20

from typing import List, Tuple

import jsonpickle


class MaxLairInstance:
    """An object for storing and processing information related to a Dynamax
    Adventure in Pokemon Sword and Shield: the Crown Tundra.
    """

    # pylint: disable=too-many-instance-attributes
    # This class is a storage container, so having many attributes is sensible.

    def __init__(self, boss: str, data_paths: List[str]) -> None:
        self.boss = boss
        self.pokemon = None
        self.HP = 1  # 1 = 100%
        self.num_caught = 0
        self.caught_pokemon = []
        self.lives = 4
        self.paths = [
            [_BossNode(('', (0, (0, 0))), 0, 0)],
            [None, None], [None, None, None, None], [None, None, None, None],
            [_BossNode(('', (0, (0, 0))), 4, 0)]
        ]
        self.path_type = None
        self.location = (0, 0)

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

    def __str__(self) -> str:
        """Print information about the current instance."""
        fork_symbols = [
            ('    \\          /'),
            ('\\     |     /' if self.path_type == '3x2' else '\\     |')
            + ('\\     |     /' if self.path_type == '2x3' else '|     /')
        ]
        if self.path_type == '2x3':
            fork_symbols.append(
                '\\_____|_____/\\_____|\n' +
                '/     /      /     |'
            )
        elif self.path_type == '3x2':
            fork_symbols.append(
                '|_____/\\_____|_____/\n' +
                '|     \\      |     \\'
            )
        elif self.path_type == '2x2':
            fork_symbols.append(
                '|   /  \\_____|_____/\n' +
                '|  /   /     |     \\'
            )
        fork_symbols.append('   /    /    \\    \\')
        output = [
            f'\n        {self.boss}',
            fork_symbols[-1],
            f'{self.paths[3][0].type_id} {self.paths[3][1].type_id} '
            f'{self.paths[3][2].type_id} {self.paths[3][3].type_id}',
            fork_symbols[-2],
            f'{self.paths[2][0].type_id} {self.paths[2][1].type_id} '
            f'{self.paths[2][2].type_id} {self.paths[2][3].type_id}',
            fork_symbols[-3],
            f'     {self.paths[1][0].type_id}  {self.paths[1][1].type_id}',
            fork_symbols[-4],
            '       START'
        ]

        return'\n'.join(output)

    def reset_stage(self) -> None:
        """Reset after a battle."""
        self.move_index = 0
        self.dmax_timer = -1
        self.opponent = None
        self.dynamax_available = False
        self.weather = Weather()
        self.terrain = Terrain()
        if self.pokemon is not None:
            if self.pokemon.name_id == 'ditto':
                self.pokemon = self.rental_pokemon['ditto']
            self.pokemon.dynamax = False

    def update_paths(
        self,
        type_data: List[Tuple[str, Tuple[float, Tuple[int, int]]]],
        index: int
    ) -> None:
        """Update the internal path storage."""

        col_index = 0
        for result in type_data:
            row = index
            col = col_index
            self.paths[row][col] = _BossNode(
                result, row, col
            )
            col_index += 1

        if index == 2:
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

        # Rebuild the path network after reassigning all of the nodes.
        if index == 3 and self.path_type is not None:
            self.paths[0][0].downstream_nodes = [
                self.paths[1][0], self.paths[1][1]]
            self.paths[1][0].downstream_nodes = [
                self.paths[2][0], self.paths[2][1]]
            self.paths[1][1].downstream_nodes = [
                self.paths[2][2], self.paths[2][3]]
            self.paths[2][0].downstream_nodes = [
                self.paths[3][0], self.paths[3][1]]
            self.paths[2][1].downstream_nodes = [
                self.paths[3][1]]
            self.paths[2][2].downstream_nodes = [
                self.paths[3][2], self.paths[3][3]]
            self.paths[2][3].downstream_nodes = [
                self.paths[3][2], self.paths[3][3]]
            self.paths[3][0].downstream_nodes = [self.paths[4][0]]
            self.paths[3][1].downstream_nodes = [self.paths[4][0]]
            self.paths[3][2].downstream_nodes = [self.paths[4][0]]
            self.paths[3][3].downstream_nodes = [self.paths[4][0]]
            if self.path_type == '2x3':
                self.paths[1][1].downstream_nodes.insert(0, self.paths[2][1])
                self.paths[2][0].downstream_nodes.append(self.paths[3][2])
                self.paths[2][1].downstream_nodes.insert(0, self.paths[3][0])
                self.paths[2][1].downstream_nodes.append(self.paths[3][2])
            elif self.path_type == '3x2':
                self.paths[1][0].downstream_nodes.append(self.paths[2][2])
                self.paths[2][1].downstream_nodes.append(0, self.paths[3][0])
                self.paths[2][2].downstream_nodes.insert(0, self.paths[3][1])
                self.paths[2][3].downstream_nodes.insert(0, self.paths[3][1])
            elif self.path_type == '2x2':
                self.paths[2][1].downstream_nodes.append(self.paths[3][2])
                self.paths[2][1].downstream_nodes.append(self.paths[3][3])
                self.paths[2][2].downstream_nodes.insert(0, self.paths[3][1])
                self.paths[2][3].downstream_nodes.insert(0, self.paths[3][1])


class _BossNode(object):
    """Data representing a node (i.e., a boss on the map of Dynamax Adventure
    paths.
    """
    def __init__(
        self,
        data: Tuple[str, Tuple[float, Tuple[int, int]]],
        row: int,
        col: int,
        downstream_nodes: List = []
    ) -> None:
        self.type_id = data[0]
        self.match_value = data[1][0]
        self.coordinates = data[1][1]
        self.row = row
        self.col = col
        self.downstream_nodes = downstream_nodes


class Weather(object):
    clear = 0
    sunlight = 1
    rain = 2
    sandstorm = 3
    hail = 4

    def __init__(
        self
    ) -> None:
        self.weather_index = 0

    def is_clear(self) -> bool:
        return self.weather_index == self.clear

    def is_sunlight(self) -> bool:
        return self.weather_index == self.sunlight

    def is_rain(self) -> bool:
        return self.weather_index == self.rain

    def is_sandstorm(self) -> bool:
        return self.weather_index == self.sandstorm

    def is_hail(self) -> bool:
        return self.weather_index == self.hail

    def set_clear(self) -> bool:
        self.weather_index = self.clear

    def set_sunlight(self) -> bool:
        self.weather_index = self.sunlight

    def set_rain(self) -> bool:
        self.weather_index = self.rain

    def set_sandstorm(self) -> bool:
        self.weather_index = self.sandstorm

    def set_hail(self) -> bool:
        self.weather_index = self.hail


class Terrain(object):
    clear = 0
    electric = 1
    grassy = 2
    misty = 3
    psychic = 4

    def __init__(
        self
    ) -> None:
        self.terrain_index = 0

    def is_clear(self) -> bool:
        return self.terrain_index == self.clear

    def is_electric(self) -> bool:
        return self.terrain_index == self.electric

    def is_grassy(self) -> bool:
        return self.terrain_index == self.grassy

    def is_misty(self) -> bool:
        return self.terrain_index == self.misty

    def is_psychic(self) -> bool:
        return self.terrain_index == self.psychic

    def set_clear(self) -> bool:
        self.terrain_index = self.clear

    def set_electric(self) -> bool:
        self.weather_index = self.electric

    def set_grassy(self) -> bool:
        self.weather_index = self.grassy

    def set_misty(self) -> bool:
        self.weather_index = self.misty

    def set_psychic(self) -> bool:
        self.weather_index = self.psychic
