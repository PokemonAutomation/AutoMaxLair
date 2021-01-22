"""Init file for AutoMaxLair
Establishes logger and exposes functions to the `automaxlair`
name space.
"""

# Original code by denvoros

import logging as __logging

# define the logger for the package so that it can be imported and used elsewhere
logger = __logging.getLogger("automaxlair")

# imports for the matchup scoring functions
# from automaxlair.matchup_scoring import (
#     ability_damage_multiplier, type_damage_multiplier_single,
#     type_damage_multiplier, print_matchup_summary, select_best_move,
#     evaluate_matchup, calculate_move_score, calculate_average_damage,
#     calculate_damage, transform_ditto
# )
import automaxlair.matchup_scoring

# imports for the Pokemon data selection
from automaxlair.pokemon_classes import Pokemon

# imports for the Move data type
from automaxlair.pokemon_classes import Move

# import the maxlairinstance
from automaxlair.MaxLairInstance import MaxLairInstance