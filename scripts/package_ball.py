import sys
import jsonpickle
import pokebase as pb
from typing import List
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)

from automaxlair.ball import Ball


def main():
    """Build Ball dictionaries and pickle the results.
    """

    balls_id = ['beast-ball', 'dive-ball', 'dream-ball', 'dusk-ball',
                'fast-ball', 'friend-ball', 'great-ball', 'heal-ball',
                'heavy-ball', 'level-ball', 'love-ball', 'lure-ball',
                'luxury-ball', 'master-ball', 'moon-ball', 'nest-ball',
                'net-ball', 'poke-ball', 'premier-ball', 'quick-ball',
                'repeat-ball', 'safari-ball', 'sport-ball', 'timer-ball',
                'ultra-ball']
    balls: List[Ball] = []

    for ball_id in balls_id:
        resource = pb.APIResource('item', ball_id)

        names = {}
        for entry in resource.names:
            names[entry.language.name] = entry.name
        balls.append(Ball(resource.name, names))
        print(f'Finished loading {ball_id}')

    # Pickle the Pokemon dictionaries for later use.
    with open(base_dir + '/data/balls.json', 'w', encoding='utf8') as file:
        file.write(jsonpickle.encode(balls, indent=4))
    print('Finished packaging Ball!')


if __name__ == '__main__':
    main()
