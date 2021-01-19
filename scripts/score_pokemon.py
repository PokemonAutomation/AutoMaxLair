# Score Pokemon
#   Eric Donders
#   2021-01-15

import sys
import pickle

# We need to import some class definitions from the parent directory.
from os.path import dirname, abspath, join
base_dir = dirname(dirname(abspath(__file__)))
sys.path.insert(1, base_dir)
sys.path.insert(1, base_dir+'\\automaxlair')

from automaxlair import Pokemon, Move, matchup_scoring

#import matchup_scoring



def main():
    rental_pokemon = pickle.load(open(base_dir+'/data/rental_pokemon.pickle', 'rb'))
    boss_pokemon = pickle.load(open(base_dir+'/data/boss_pokemon.pickle', 'rb'))

    rental_matchup_LUT = {}
    boss_matchup_LUT = {}
    rental_pokemon_scores = {}
    total_score = 0

    # Iterate through all rental Pokemon and calculate scores against all the
    # other rental Pokemon and all boss Pokemon. Also calculate an average score
    # against other rental Pokemon which is helpful for picking generalists at
    # the start of a new run.

    for attacker_id in tuple(rental_pokemon):
        attacker = rental_pokemon[attacker_id]
        # First iterate through all boss Pokemon and score the interactions.
        matchups = {}
        for defender_id in tuple(boss_pokemon):
            defender = boss_pokemon[defender_id]
            matchups[defender_id] = matchup_scoring.evaluate_matchup(attacker, defender, rental_pokemon)
        boss_matchup_LUT[attacker_id] = matchups

        # Then, iterate through all rental Pokemon and score the interactions.
        matchups = {}
        attacker_score = 0
        for defender_id in tuple(rental_pokemon):
            defender = rental_pokemon[defender_id]
            matchups[defender_id] = matchup_scoring.evaluate_matchup(attacker, defender, rental_pokemon)
            # We sum the attacker's score which will later be normalized.
            attacker_score += matchups[defender_id]

        # Store the scores in a convenient lookup table.   
        rental_matchup_LUT[attacker_id] = matchups
        rental_pokemon_scores[attacker_id] = attacker_score

        # Keep a total of all the attackers' scores which is used to normalized
        # the individual scores such that the average is 1.
        total_score += attacker_score

        print(f'Finished computing matchups for {attacker}')

    # Normalize the total scores.
    for key in rental_pokemon_scores:
        rental_pokemon_scores[key] /= (total_score/len(rental_pokemon))
        
        
    # Pickle the score lookup tables for later use.
    with open(base_dir+'/data/boss_matchup_LUT.pickle', 'wb') as file:
        pickle.dump(boss_matchup_LUT, file)
    with open(base_dir+'/data/rental_matchup_LUT.pickle', 'wb') as file:
        pickle.dump(rental_matchup_LUT, file)
    with open(base_dir+'/data/rental_pokemon_scores.pickle', 'wb') as file:
        pickle.dump(rental_pokemon_scores, file)
    print('Finished scoring Pokemon!')

if __name__ == '__main__':
    main()