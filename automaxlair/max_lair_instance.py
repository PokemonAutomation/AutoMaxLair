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


class BossNode(object):
    """Data representing a node (i.e., a boss on the map of Dynamax Adventure
    paths.
    """
    def __init__(
        self,
        data: Tuple[str, Tuple[float, Tuple[int, int]]],
        row: int,
        col: int,
        downstream_nodes: List['BossNode'] = []
    ) -> None:
        self.name = data[0]
        self.match_value = data[1][0]
        self.coordinates = data[1][1]
        self.row = row
        self.col = col
        self.downstream_nodes = downstream_nodes

    def __str__(self) -> str:
        return self.name

    def get_all_downstream_paths(self) -> List['BossNode']:
        """Recursively retrieve a list of all paths through the den."""
        # If this is the end of the path, return just this node.
        if len(self.downstream_nodes) == 0:
            paths = [[self]]
        # Otherwise, get the paths from the downstream nodes.
        else:
            paths = []
            for node in self.downstream_nodes:
                for path in node.get_all_downstream_paths():
                    paths.append([self] + path)

        return paths


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
            [BossNode(('START', (0, (0, 0))), 0, 0)],
            [None, None], [None, None, None, None], [None, None, None, None],
            [BossNode((self.boss, (0, (0, 0))), 4, 0)]
        ]
        self.path_type = None
        self.target_path = []
        self.current_node = self.paths[0][0]
        self.current_node_index = 0

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
        with open(data_paths[5], 'r', encoding='utf8') as file:
            self.path_tree = jsonpickle.decode(file.read())

    def __str__(self) -> str:
        """Print information about the current instance."""
        fork_symbols = [
            ('       \\    /'),
            ('  \\   |   /  ' if self.path_type == '3x2' else '  \\   |')
            + ('\\     |     /' if self.path_type == '2x3' else '|     /')
        ]
        if self.path_type == '2x3':
            fork_symbols.append(
                '\\_____|_____/\\_____|\n' +
                '/     /      /     |'
            )
        elif self.path_type == '3x2':
            fork_symbols.append(
                '|_____/  \\____|____/\n' +
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
            f'{self.paths[3][0].name} {self.paths[3][1].name} '
            f'{self.paths[3][2].name} {self.paths[3][3].name}',
            fork_symbols[-2],
            f'{self.paths[2][0].name} {self.paths[2][1].name} '
            f'{self.paths[2][2].name} {self.paths[2][3].name}',
            fork_symbols[-3],
            f'   {self.paths[1][0].name}   {self.paths[1][1].name}',
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
        self.field = Field()
        if self.pokemon is not None:
            if self.pokemon.name_id == 'ditto':
                self.pokemon = self.rental_pokemon['ditto']
            self.pokemon.dynamax = False

    def get_paths(
        self,
        truncate: bool = False,
        name_only: bool = False
    ) -> List[List[BossNode]]:
        """Get a list of all paths through the den."""
        paths = self.current_node.get_all_downstream_paths()

        if truncate:
            # Strip out path start and boss.
            new_paths = []
            for path in paths:
                new_paths.append([
                    node for node in path if node.name not in (
                        'START', self.boss)])
            paths = new_paths

        if name_only:
            # Return a list of strings inatead of object references.
            new_paths = []
            for path in paths:
                new_paths.append(list(map(str, path)))
            paths = new_paths

        return paths

    def get_next_fork_offset(self) -> int:
        """Check how many times the bot should move the cursor over in order
        to navigate down the desired path.
        """

        if self.current_node_index + 1 < len(self.target_path):
            target_node = self.target_path[self.current_node_index + 1]
            return self.current_node.downstream_nodes.index(target_node)
        else:
            raise IndexError('No downstream path to select.')

    def advance_node(self) -> None:
        """Move to the next node in the desired path."""
        if self.current_node_index + 1 < len(self.target_path):
            self.current_node_index += 1
            self.current_node = self.target_path[self.current_node_index]
        else:
            raise IndexError('No downstream node to move to.')

    def update_paths(
        self,
        type_data: List[Tuple[str, Tuple[float, Tuple[int, int]]]],
        index: int
    ) -> None:
        """Update the internal path storage."""
        # Update the nodes with the supplied data.
        col_index = 0
        for result in type_data:
            row = index
            col = col_index
            self.paths[row][col] = BossNode(
                result, row, col
            )
            col_index += 1

        # If looking at the row of second bosses, use their relative positions
        # to compute the path type.
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
                standard_vals.keys(), key=lambda x: abs(x - diff))
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
                self.paths[2][1].downstream_nodes.insert(0, self.paths[3][0])
                self.paths[2][2].downstream_nodes.insert(0, self.paths[3][1])
                self.paths[2][3].downstream_nodes.insert(0, self.paths[3][1])
            elif self.path_type == '2x2':
                self.paths[2][1].downstream_nodes.append(self.paths[3][2])
                self.paths[2][1].downstream_nodes.append(self.paths[3][3])
                self.paths[2][2].downstream_nodes.insert(0, self.paths[3][1])
                self.paths[2][3].downstream_nodes.insert(0, self.paths[3][1])


class Field(object):
    def __init__(self) -> None:
        self.weather = "clear"
        self.terrain = "clear"

    def is_weather_clear(self) -> bool:
        return self.weather == "clear"

    def is_weather_sunlight(self) -> bool:
        return self.weather == "sunlight"

    def is_weather_rain(self) -> bool:
        return self.weather == "rain"

    def is_weather_sandstorm(self) -> bool:
        return self.weather == "sandstorm"

    def is_weather_hail(self) -> bool:
        return self.weather == "hail"

    def set_weather_clear(self) -> bool:
        self.weather = "clear"

    def set_weather_sunlight(self) -> bool:
        self.weather = "sunlight"

    def set_weather_rain(self) -> bool:
        self.weather = "rain"

    def set_weather_sandstorm(self) -> bool:
        self.weather = "sandstorm"

    def set_weather_hail(self) -> bool:
        self.weather = "hail"

    def is_terrain_clear(self) -> bool:
        return self.terrain == "clear"

    def is_terrain_electric(self) -> bool:
        return self.terrain == "electric"

    def is_terrain_grassy(self) -> bool:
        return self.terrain == "grassy"

    def is_terrain_misty(self) -> bool:
        return self.terrain == "misty"

    def is_terrain_psychic(self) -> bool:
        return self.terrain == "psychic"

    def set_terrain_clear(self) -> bool:
        self.terrain = "clear"

    def set_terrain_electric(self) -> bool:
        self.terrain = "electric"

    def set_terrain_grassy(self) -> bool:
        self.terrain = "grassy"

    def set_terrain_misty(self) -> bool:
        self.terrain = "misty"

    def set_terrain_psychic(self) -> bool:
        self.terrain = "psychic"
