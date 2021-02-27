# Pokemon
#   Eric Donders
#   2020-11-27
import math
import copy
from typing import Dict, List, Tuple


class Pokemon():
    def __init__(self,
                 id_num: int,
                 name_id: str,
                 names: Dict[str, str],
                 ability_name_id: str,
                 abilities: Dict[str, str],
                 type_ids: List[str],
                 types: List[Dict[str, str]],
                 base_stats: Tuple[int, int, int, int, int, int],
                 moves,
                 max_moves,
                 level: int = 100,
                 IVs: Tuple[int, int, int, int, int, int] = (
                     15, 15, 15, 15, 15, 15),
                 EVs: Tuple[int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0),
                 nature: Tuple[int, int, int, int,
                               int, int] = (1, 1, 1, 1, 1, 1)
                 ):
        self.id_num = id_num
        self.name_id = name_id
        self.names = names
        self.ability_name_id = ability_name_id
        self.abilities = abilities
        self.type_ids = type_ids
        self.types = types
        self.base_stats = base_stats
        self.moves = moves
        self.max_moves = max_moves
        self.level = level
        self.ivs = IVs
        self.evs = EVs
        self.nature = nature

        self.PP = []
        for move in moves:
            self.PP.append(move.PP)

        self.restore()
        self.reset_stats()

    def __str__(self):
        return self.name_id

    def __copy__(self):
        copied_pokemon = type(self)(self. id_num, self.name_id, self.names,
                                    self.ability_name_id, self.abilities, self.type_ids, self.types,
                                    self.base_stats, self.moves, self.max_moves, self.level, self.ivs,
                                    self.evs, self.nature
                                    )
        copied_pokemon.PP = copy.deepcopy(self.PP)
        copied_pokemon.HP = copy.deepcopy(self.HP)
        copied_pokemon.status = self.status
        copied_pokemon.stat_modifiers = self.stat_modifiers
        copied_pokemon.dynamax = self.dynamax
        return copied_pokemon

    def print_verbose(self):
        """Print a detailed summary of the Pokemon."""
        print(f'ID number: {self.id_num}')
        print(f'Name identifier: {self.name_id}')
        print('Translations')
        for language, name in self.names.items():
            print(f'\t{language}: {name}')
        print(f'Ability identifier: {self.ability_name_id}')
        print('Translations')
        for language, name in self.abilities.items():
            print(f'\t{language}: {name}')
        for i in range(len(self.type_ids)):
            print(f'Type {i+1}: {self.type_ids[i]}')
            for language, name in self.types[i].items():
                print(f'\t{language}: {name}')
        print('Base stats:')
        for stat in self.base_stats:
            print(f'\t{stat}')
        for move in self.moves:
            move.print_verbose()
        for max_move in self.max_moves:
            max_move.print_verbose()
        print(f'Level: {self.level}')
        print('PP:')
        for value in self.PP:
            print(f'\t{value}')

    def restore(self):
        """Restore HP, PP, and status effects."""
        self.HP = 1
        for i in range(len(self.PP)):
            self.PP[i] = self.moves[i].PP
        self.status = None

    def reset_stats(self):
        """Reset stat changes."""
        self.stat_modifiers = (None, 0, 0, 0, 0, 0)
        self.recalculate_stats()
        self.dynamax = False

    def adjust_stats(self, modification):
        for i in range(1, 6):
            self.stat_modifiers[i] += modification[i]
        self.recalculate_stats()

    def recalculate_stats(self):
        self.stats = [(math.floor((2 * self.base_stats[0] + self.ivs[0] + math.floor(
            self.evs[0] / 4)) * self.level / 100) + self.level + 10) * self.HP]
        for i in range(1, 6):
            self.stats.append(math.floor((math.floor(
                (2 * self.base_stats[i] + self.ivs[i] + math.floor(self.evs[i] / 4)) * self.level / 100) + 5) * self.nature[i]))
            if self.stat_modifiers[i] >= 0:
                if self.stat_modifiers[i] > 6:
                    self.stat_modifiers[i] = 6
                self.stats[i] *= (2 + self.stat_modifiers[i]) / 2
            elif self.stat_modifiers[i] < 0:
                if self.stat_modifiers[i] < -6:
                    self.stat_modifiers[i] = -6
                self.stats[i] *= 2 / (2 + self.stat_modifiers[i])

    def get_name(self, language: str) -> str:
        """Return the name of the Pokemon in a given language.
        Returns the name ID if no value exists for the supplied language.
        """

        return self.names.get(language, self.name_id)

    def get_ability(self, language: str) -> str:
        """Return the ability of the Pokemon in a given language.
        Returns the ability ID if no value exists for the supplied language.
        """

        return self.abilities.get(language, self.ability_name_id)

    def get_types(self, language: str) -> List[str]:
        """Return the types of the Pokemon in a given language.
        Returns the type IDs if no value exists for the supplied language.
        """

        types = []
        for i in range(len(self.types)):
            types.append(self.types[i].get(language, self.type_ids[i]))
        return types

    def __repr__(self) -> str:
        return f"<'{self.name_id}' Pokemon Object>"


class Move():
    def __init__(self, id_num: int, name_id: str, names: Dict[str, str],
                 type_id: str, category: str, base_power: float, accuracy: float,
                 PP: int, effect: str, probability: float, is_spread: bool = False,
                 correction_factor: float = 1
                 ):
        self.id_num = id_num
        self.name_id = name_id
        self.names = names
        self.type_id = type_id
        self.category = category
        self.base_power = base_power
        self.accuracy = accuracy
        self.PP = PP
        self.effect = effect
        self.probability = probability
        self.is_spread = is_spread
        self.correction_factor = correction_factor

        self.power = base_power * correction_factor

    def __str__(self):
        return self.name_id

    def __copy__(self):
        return type(self)(self.id_num, self.name_id, self.names, self.type_id,
                          self.category, self.base_power, self.accuracy, self.PP, self.effect,
                          self.probability, self.is_spread, self.correction_factor
                          )

    def print_verbose(self):
        """Print a detailed summary of the Move."""
        print(f'ID number: {self.id_num}')
        print(f'Name identifier: {self.name_id}')
        print('Translations')
        for language, name in self.names.items():
            print(f'\t{language}: {name}')
        print(f'Type identifier: {self.type_id}')
        print(f'Category: {self.category}')
        print(f'BP: {self.base_power}')
        print(f'Accuracy: {int(self.accuracy*100)}')
        print(f'PP: {self.PP}')
        print(f'Effect: {self.effect}')
        print(f'Probability: {self.probability}')
        print(f'Spread move: {self.is_spread}')
        print(f'Correction factor: {self.correction_factor}')
        print(f'Adjusted power: {self.power}')

    def __repr__(self) -> str:
        return f"<'{self.name_id}' Move object>"
