# Score Pokemon
#   Eric Donders
#   Multiprocessing and logging implemented with help from denvoros.
#   2021-01-15

import logging
import logging.handlers
import multiprocessing as mp
import os
import jsonpickle
import sys
import time

# We need to import some things from the parent directory.
from os.path import dirname, abspath
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, base_dir + '\\automaxlair')

from automaxlair import matchup_scoring  # Needs to be lower than path insert.


# Config values for the log and multiprocessing.
LOG_NAME = 'packagePokemon'
ENABLE_DEBUG_LOGS = True
MAX_NUM_THREADS = mp.cpu_count() - 1


def compute_scores(attacker):
    """Computes the scores of a single rental Pokemon against all other rental
    Pokemon and all boss Pokemon. Called by the multiprocessing pool.
    Parameters:
        attacker (Pokemon): the rental Pokemon to be scored.
    """

    logger = logging.getLogger(LOG_NAME)

    attacker_id = attacker.name_id

    # Load a separate dictionary for each process because elements get popped
    # and re-added during the matchup scoring process.
    with open(base_dir + '/data/rental_pokemon.json', 'r', encoding='utf8') as file:
        rental_pokemon = jsonpickle.decode(file.read())
    with open(base_dir + '/data/boss_pokemon.json', 'r', encoding='utf8') as file:
        boss_pokemon = jsonpickle.decode(file.read())

    # First iterate through all boss Pokemon and score the interactions.
    boss_matchups = {}
    for defender_id in tuple(boss_pokemon):
        defender = boss_pokemon[defender_id]
        score = matchup_scoring.evaluate_matchup(
            attacker, defender, rental_pokemon
        )
        boss_matchups[defender_id] = score
        logger.debug(
            f'Matchup between {attacker_id} and {defender_id}: {score:.2f}'
        )

    # Then, iterate through all rental Pokemon and score the interactions.
    rental_matchups = {}
    rental_score = 0
    for defender_id in tuple(rental_pokemon):
        defender = rental_pokemon[defender_id]
        score = matchup_scoring.evaluate_matchup(
            attacker, defender, rental_pokemon
        )
        rental_matchups[defender_id] = score
        # We sum the attacker's score which will later be normalized.
        rental_score += score
        logger.debug(
            f'Matchup between {attacker_id} and {defender_id}: {score:.2f}'
        )

    # Return the results as a tuple which will be unpacked and repacked in
    # dicts later, with the first element (the Pokemon's name identifier) as
    # the key and the other elements as values in their respective dicts.
    logger.info(f'Finished computing matchups for {attacker}')
    return (attacker_id, boss_matchups, rental_matchups, rental_score)


def worker_init(q):
    """Basic function that initializes the thread workers to know where to send
    logs to.
    Parameters:
        q (multiprocessing.Queue): The queue object used for  multiprocessing.
    """

    # All records from worker processes go to qh and then into q.
    qh = logging.handlers.QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    logger.addHandler(qh)


def main():
    """Main function that loads the Pokemon data files, uses a multiprocessing
    pool to compute their matchups, and saves the results.
    Parameters:
        q (multiprocessing.Queue): The queue object used for multiprocessing.

    """

    # Configure the logger.
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s: %(message)s'
    )

    # Configure the console, which will print logged information.
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)

    # Configure the file handler, which will save logged information.
    fileHandler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(base_dir, 'logs', 'packagePokemonScript.log'),
        when='midnight',
        backupCount=30
    )
    fileHandler.setFormatter(formatter)
    fileHandler.setLevel(logging.DEBUG if ENABLE_DEBUG_LOGS else logging.INFO)

    # Add the handlers to the logger so that it will both print messages to the
    # console as well as save them to a log file.
    logger.addHandler(console)
    logger.addHandler(fileHandler)

    # Configure the queue and listener that will receive information to be
    # logged from all of the processes.
    q = mp.Queue()
    ql = logging.handlers.QueueListener(q, console, fileHandler)
    ql.start()

    logger.info('Started scoring Pokemon.')

    with open(base_dir + '/data/rental_pokemon.json', 'r', encoding='utf8') as file:
        rental_pokemon = jsonpickle.decode(file.read())

    # Iterate through all rental Pokemon and calculate scores against all the
    # other rental Pokemon and all boss Pokemon. Also calculate an average
    # score against other rental Pokemon which is helpful for picking
    # generalists at the start of a new run.
    pool = mp.Pool(MAX_NUM_THREADS, worker_init, [q])
    results_dump = pool.imap(compute_scores, rental_pokemon.values())
    pool.close()
    pool.join()

    # Unpack the computed results and repack in dicts which will be pickled.
    rental_matchup_LUT = {}
    boss_matchup_LUT = {}
    rental_pokemon_scores = {}
    total_score = 0
    for name_id, boss_matchups, rental_matchups, rental_score in results_dump:
        boss_matchup_LUT[name_id] = boss_matchups
        rental_matchup_LUT[name_id] = rental_matchups
        rental_pokemon_scores[name_id] = rental_score
        total_score += rental_score

    # Normalize the total scores.
    for key in rental_pokemon_scores:
        rental_pokemon_scores[key] /= (total_score / len(rental_pokemon))

    ql.stop()

    # Pickle the score lookup tables for later use.
    with open(base_dir + '/data/boss_matchup_LUT.json', 'w', encoding='utf8') as file:
        file.write(jsonpickle.encode(boss_matchup_LUT, indent=4))
    with open(base_dir + '/data/rental_matchup_LUT.json', 'w', encoding='utf8') as file:
        file.write(jsonpickle.encode(rental_matchup_LUT, indent=4))
    with open(base_dir + '/data/rental_pokemon_scores.json', 'w', encoding='utf8') as file:
        file.write(jsonpickle.encode(rental_pokemon_scores, indent=4))


if __name__ == '__main__':
    # Call main, then clean up.
    start_time = time.time()
    main()
    end_time = time.time()
    logger = logging.getLogger(LOG_NAME)
    logger.info(f'Finished scoring Pokemon, taking {end_time - start_time} s.')
