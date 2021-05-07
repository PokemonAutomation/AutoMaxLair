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
from automaxlair.field import Field


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
        self.team_pokemon = {}
        self.HP = 1  # 1 = 100%
        self.num_caught = 0
        self.caught_pokemon = []
        self.all_encountered_pokemon = set()
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

        self.potential_boss_pokemon = self.rental_pokemon.copy()

    def __str__(self) -> str:
        """Print information about the current instance."""

        return (
            f'Path with boss {self.boss} and nodes: '
            f'{[[node.name for node in x] for x in self.paths]}'
        )

    def get_output_strings(self) -> List[str]:
        """Return a list of strings that visually represent the path when
        printed sequentially.
        """

        section_1 = [
            f'      ┌{self.paths[1][0].name:─<8}', 'START─┤        ',
            f'      └{self.paths[1][1].name:─<8}', '               ']
        if self.path_type == '2x3':
            section_2 = ['┬──', '└┮═', '─┼─', ' └─']
        elif self.path_type == '3x2':
            section_2 = ['┬──', '└┬─', '┬┶═', '└──']
        else:
            section_2 = ['┬──', '└──', '┬──', '└──']
        section_3 = [
            f'{self.paths[2][0].name:─<8}', f'{self.paths[2][1].name:─<8}',
            f'{self.paths[2][2].name:─<8}', f'{self.paths[2][3].name:─<8}']
        if self.path_type == '2x3':
            section_4 = ['┐┌─', '┴┼─', '┐╞═', '┴┴─']
        elif self.path_type == '3x2':
            section_4 = ['┬┬─', '┘╞═', '┬┼─', '┘└─']
        else:
            section_4 = ['─┬─', '┐╞═', '┼┼─', '┘└─']
        section_5 = [
            f'{self.paths[3][0].name:─<8}┐',
            f'{self.paths[3][1].name:─<8}┼─{self.paths[4][0].name}',
            f'{self.paths[3][2].name:─<8}┤', f'{self.paths[3][3].name:─<8}┘']
        all_sections = (section_1, section_2, section_3, section_4, section_5)
        output = []
        for i in range(4):
            output.append(''.join([x[i] for x in all_sections]))

        return output

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

    def prune_potential_minibosses(self) -> None:
        """Update the dict of rental Pokemon that may appear as future bosses.
        """

        # Start with a fresh copy of all rental Pokemon.
        self.potential_boss_pokemon = self.rental_pokemon.copy()
        # Then, remove all Pokemon that have previously been encountered
        for name_id in self.all_encountered_pokemon:
            self.potential_boss_pokemon.pop(name_id, None)
        # Finally, remove any Pokemon that doesn't fit the types of the
        # remaining chosen path.
        types_left = set([
            node.name for node in
            self.target_path[self.current_node_index + 1:]
        ])
        for name_id, pokemon in self.rental_pokemon.items():
            if types_left.isdisjoint(pokemon.type_ids):
                self.potential_boss_pokemon.pop(name_id, None)

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
            # Return a list of strings instead of object references.
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
            if self.path_type == '2x3':
                self.paths[1][0].downstream_nodes = [
                    self.paths[2][0], self.paths[2][1]]
                self.paths[1][1].downstream_nodes = [
                    self.paths[2][1], self.paths[2][2], self.paths[2][3]]
                self.paths[2][0].downstream_nodes = [
                    self.paths[3][0], self.paths[3][1], self.paths[3][2]]
                self.paths[2][1].downstream_nodes = [
                    self.paths[3][0], self.paths[3][1], self.paths[3][2]]
                self.paths[2][2].downstream_nodes = [
                    self.paths[3][2], self.paths[3][3]]
                self.paths[2][3].downstream_nodes = [
                    self.paths[3][2], self.paths[3][3]]
            elif self.path_type == '3x2':
                self.paths[1][0].downstream_nodes = [
                    self.paths[2][0], self.paths[2][1], self.paths[2][2]]
                self.paths[1][1].downstream_nodes = [
                    self.paths[2][2], self.paths[2][3]]
                self.paths[2][0].downstream_nodes = [
                    self.paths[3][0], self.paths[3][1]]
                self.paths[2][1].downstream_nodes = [
                    self.paths[3][0], self.paths[3][1]]
                self.paths[2][2].downstream_nodes = [
                    self.paths[3][0], self.paths[3][1]]
                self.paths[2][3].downstream_nodes = [
                    self.paths[3][1], self.paths[3][2], self.paths[3][3]]
            elif self.path_type == '2x2':
                self.paths[1][0].downstream_nodes = [
                    self.paths[2][0], self.paths[2][1]]
                self.paths[1][1].downstream_nodes = [
                    self.paths[2][2], self.paths[2][3]]
                self.paths[2][0].downstream_nodes = [
                    self.paths[3][0], self.paths[3][1]]
                self.paths[2][1].downstream_nodes = [
                    self.paths[3][1], self.paths[3][2], self.paths[3][3]]
                self.paths[2][2].downstream_nodes = [
                    self.paths[3][1], self.paths[3][2], self.paths[3][3]]
                self.paths[2][3].downstream_nodes = [
                    self.paths[3][1], self.paths[3][2], self.paths[3][3]]
            self.paths[3][0].downstream_nodes = [self.paths[4][0]]
            self.paths[3][1].downstream_nodes = [self.paths[4][0]]
            self.paths[3][2].downstream_nodes = [self.paths[4][0]]
            self.paths[3][3].downstream_nodes = [self.paths[4][0]]
