"""Init file for AutoMaxLair
Establishes logger and exposes functions to the `automaxlair`
name space.
"""

# Original code by denvoros

import logging as __logging

import automaxlair.da_controller
import automaxlair.matchup_scoring
import automaxlair.max_lair_instance

# define the logger for the package so that it can be imported and used elsewhere
logger = __logging.getLogger("automaxlair")
