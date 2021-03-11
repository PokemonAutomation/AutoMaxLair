import package_pokemon
import score_pokemon
import time

if __name__ == '__main__':
    start = time.time()
    package_pokemon.main()
    end = time.time()
    print(f'package_pokemon took {end - start}')

    start = time.time()
    score_pokemon.main()
    end = time.time()
    print(f'score_pokemon took {end - start}')
