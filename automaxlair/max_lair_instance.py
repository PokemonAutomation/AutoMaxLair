#   MaxLairInstance
#       Eric Donders
#       Contributions from Miguel Tavera and Discord users denvoros and pifopi
#       Last updated 2021-01-08
#       Created 2020-11-20

import logging
import pickle
import sys
import time
from datetime import datetime
from typing import List, Tuple, TypeVar, Iterable, Optional

import cv2
import enchant
import pytesseract

from .pokemon_classes import Pokemon
from serial import Serial
from cv2 import VideoCapture
from configparser import ConfigParser
from threading import Lock, Event
Image = TypeVar('cv2 image')
Rectangle = Tuple[Tuple[float, float], Tuple[float, float]]


class MaxLairInstance:
    """An object for storing and processing information related to a Dynamax
    Adventure in Pokemon Sword and Shield: the Crown Tundra.
    """

    def __init__(self, data_paths) -> None:
        self.pokemon = None
        self.HP = 1  # 1 = 100%
        self.num_caught = 0
        self.caught_pokemon = []
        self.lives = 4
        self.reset_stage()
        # Load precalculated resources for choosing Pokemon and moves
        with open(data_paths[0], 'rb') as boss_file:
            self.boss_pokemon = pickle.load(boss_file)
        with open(data_paths[1], 'rb') as rental_file:
            self.rental_pokemon = pickle.load(rental_file)
        with open(data_paths[2], 'rb') as boss_matchup_file:
            self.boss_matchups = pickle.load(boss_matchup_file)
        with open(data_paths[3], 'rb') as rental_matchup_file:
            self.rental_matchups = pickle.load(rental_matchup_file)
        with open(data_paths[4], 'rb') as rental_score_file:
            self.rental_scores = pickle.load(rental_score_file)

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