import time
import package_ball
import package_pokemon
import package_pokemon_sprites
import score_pokemon
import get_good_color_discord


if __name__ == '__main__':
    start = time.time()
    package_ball.main()
    end = time.time()
    print(f'package_ball took {end - start} s')

    start = time.time()
    package_pokemon.main()
    end = time.time()
    print(f'package_pokemon took {end - start} s')

    start = time.time()
    score_pokemon.main()
    end = time.time()
    print(f'score_pokemon took {end - start} s')

    start = time.time()
    package_pokemon_sprites.main()
    end = time.time()
    print(f'package_pokemon_sprites took {end - start} s')

    start = time.time()
    get_good_color_discord.main()
    end = time.time()
    print(f'get_good_color_discord took {end - start} s')
