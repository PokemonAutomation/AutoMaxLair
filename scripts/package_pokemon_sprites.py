"""Collect images from pokesprite (linked submodule) and save them in a
ready-to-use pickle file.
"""

import pickle
import os
import pickle
import sys

import cv2
import jsonpickle

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath


def main():
    # We're working across a few directories, so store them for later use.
    base_dir = dirname(dirname(abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    image_dir = os.path.join(
        data_dir, 'pokesprite', 'pokemon-gen8', 'regular')

    # Load the rental Pokemon we need to build sprites for
    with open(
        os.path.join(data_dir, 'rental_pokemon.json'), 'r',
        encoding='utf8'
    ) as file:
        rental_pokemon = jsonpickle.decode(file.read())

    # Generate sprites of each rental Pokemon.
    all_images = []
    for name_id in rental_pokemon:
        # The name format isn't exactly between PokeAPI and pokesprite.
        # Therefore, manually convert where there are descrepencies.
        if name_id == 'basculin-red-striped':
            fn = 'basculin.png'
        elif name_id == 'gourgeist-average':
            fn = 'gourgeist.png'
        elif name_id == 'lycanroc-midday':
            fn = 'lycanroc.png'
        elif name_id == 'mimikyu-disguised':
            fn = 'mimikyu.png'
        elif name_id == 'toxtricity-amped':
            fn = 'toxtricity.png'
        elif name_id == 'indeedee-male':
            fn = 'indeedee.png'
        else:
            fn = name_id + '.png'
        # Start by loading the Pokemon's sprite and female sprite if it exists.
        species_images = []
        species_images.append(cv2.imread(
            os.path.join(image_dir, fn), cv2.IMREAD_UNCHANGED))
        if fn in os.listdir(os.path.join(image_dir, 'female')):
            species_images.append(cv2.imread(
                os.path.join(image_dir, 'female', fn), cv2.IMREAD_UNCHANGED))
        # Then, remove the alpha channel and add each image to the export list.
        for image in species_images:
            image = cv2.resize(
                image, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
            mask = image[:, :, 3] == 0
            image[mask] = [255, 255, 255, 255]
            all_images.append(
                (name_id, cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)))

        print(f'Finished processing {name_id}')

    # Save the sprites.
    with open(
        os.path.join(data_dir, 'pokemon_sprites.pickle'), 'wb'
    ) as file:
        pickle.dump(all_images, file)


if __name__ == '__main__':
    main()