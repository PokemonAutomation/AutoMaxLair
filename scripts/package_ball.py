"""Collect ball images from pokesprite (linked submodule) and save them in a
ready-to-use pickle file.
"""

import os
import pickle
import sys

from typing import Dict
from os.path import dirname, abspath

import jsonpickle
import cv2
import pokebase as pb

base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)

from automaxlair.ball import Ball  # noqa: E402


def main():
    """Build Ball dictionaries and pickle the results.
    """

    image_dir = os.path.join(base_dir, 'data', 'pokesprite', 'items', 'ball')

    balls_id = ['beast-ball', 'dive-ball', 'dream-ball', 'dusk-ball',
                'fast-ball', 'friend-ball', 'great-ball', 'heal-ball',
                'heavy-ball', 'level-ball', 'love-ball', 'lure-ball',
                'luxury-ball', 'master-ball', 'moon-ball', 'nest-ball',
                'net-ball', 'poke-ball', 'premier-ball', 'quick-ball',
                'repeat-ball', 'safari-ball', 'sport-ball', 'timer-ball',
                'ultra-ball']
    balls: Dict[str, Ball] = {}
    ball_images = {}

    for ball_id in balls_id:
        # Load the sprite for the ball
        image_fn = ball_id.split('-')[0] + '.png'
        ball_image = cv2.imread(
            os.path.join(image_dir, image_fn), cv2.IMREAD_UNCHANGED)
        # Double the sprite size to match what is shown in game.
        ball_image = cv2.resize(
            ball_image, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        # Convert transparent pixels to black as they appear in game.
        mask = ball_image[:, :, 3] == 0
        ball_image[mask] = [0, 0, 0, 0]
        ball_images[ball_id] = cv2.cvtColor(ball_image, cv2.COLOR_BGRA2BGR)

        resource = pb.APIResource('item', ball_id)

        names = {}
        for entry in resource.names:
            names[entry.language.name] = entry.name
        balls[resource.name] = Ball(resource.name, names)
        print(f'Finished loading {ball_id}')

    # Pickle the Pokemon dictionaries for later use.
    with open(
        os.path.join(base_dir, 'data', 'balls.json'), 'w', encoding='utf8'
    ) as file:
        file.write(jsonpickle.encode(balls, indent=4))

    with open(
        os.path.join(base_dir, 'data', 'ball_sprites.pickle'), 'wb'
    ) as file:
        pickle.dump(ball_images, file)
    print('Finished packaging balls!')


if __name__ == '__main__':
    main()
