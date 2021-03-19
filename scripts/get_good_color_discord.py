import jsonpickle
import requests
from PIL import Image
import numpy as np
import sys
from os.path import abspath, dirname, join

base_dir = dirname(dirname(abspath(__file__)))


def palette(img):
    """
    Return palette in descending order of frequency
    """
    arr = np.asarray(img)
    palette, index = np.unique(asvoid(arr).ravel(), return_inverse=True)
    palette = palette.view(arr.dtype).reshape(-1, arr.shape[-1])
    count = np.bincount(index)
    order = np.argsort(count)
    return palette[order[::-1]]


def asvoid(arr):
    """View the array as dtype np.void (bytes)
    This collapses ND-arrays to 1D-arrays, so you can perform 1D operations on them.
    http://stackoverflow.com/a/16216866/190597 (Jaime)
    http://stackoverflow.com/a/16840350/190597 (Jaime)
    Warning:
    >>> asvoid([-0.]) == asvoid([0.])
    array([False], dtype=bool)
    """
    arr = np.ascontiguousarray(arr)
    return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))


if __name__ == "__main__":

    with open(join(base_dir, 'data', 'boss_pokemon.json'), 'r', encoding='utf8') as file:
        boss_pokemon = jsonpickle.decode(file.read())

    boss_colors = {}

    for boss_name in boss_pokemon.keys():
        # get the image from pokemondb

        url = f"https://img.pokemondb.net/sprites/home/shiny/{boss_name}.png"
        img = Image.open(requests.get(url, stream=True).raw)

        the_pal = palette(img)[:10, :-1]

        # find the best color that isn't all 0's or 255's
        for pal_test in the_pal:
            if np.mean(pal_test) > 245 or np.mean(pal_test) < 10:
                # if np.all(pal_test == np.array([0, 0, 0])) or \
                #         np.all(pal_test == np.array([255, 255, 255])) or \
                #         np.all(pal_test == np.array([255, 255, 255])) or \
                #         np.all(pal_test == np.array([254, 254, 254])):
                continue
            else:
                col_use = pal_test
                break

        boss_colors[boss_name] = col_use.tolist()

    # NOTE: some of them were bad so i hand selected these ones
    boss_colors['buzzwole'] = [72, 209, 80]
    boss_colors['dialga'] = [177, 255, 177]
    boss_colors['giratina-altered'] = [219, 195, 159]
    boss_colors['lugia'] = [203, 106, 147]
    boss_colors['lunala'] = [187, 12, 51]
    boss_colors['mesprit'] = [245, 108, 128]
    boss_colors['mewtwo'] = [121, 193, 99]
    boss_colors['moltres'] = [230, 126, 145]
    boss_colors['tapu-fini'] = [125, 153, 182]
    boss_colors['tapu-bulu'] = [232, 222, 112]
    boss_colors['tapu-lele'] = [255, 172, 176]
    boss_colors['tapu-koko'] = [244, 160, 107]
    boss_colors['thundurus-incarnate'] = [159, 174, 216]
    boss_colors['tornadus-incarnate'] = [121, 159, 83]
    boss_colors['xerneas'] = [34, 177, 227]
    boss_colors['xurkitree'] = [129, 173, 200]
    boss_colors['zygarde-50'] = [41, 186, 149]

    # then save it as a json
    with open(join(base_dir, "data", 'boss_colors.json'), 'w', encoding='utf8') as f:
        f.write(jsonpickle.encode(boss_colors, indent=4))
