# Package_Pokemon
#   Eric Donders
#   2020-11-27
#   Read information on Pokemon and construct sets of rental and boss Pokemon used in Dynamax Adventures

from Pokemon_Data.Pokemon import Pokemon
from Pokemon_Data.Move import Move
from Pokemon_Data import matchup_scoring
from copy import copy
import csv, pickle

spread_move_list = []
with open('Pokemon_Data/Spread_moves.txt', newline='\n') as tsvfile:
    spamreader = csv.reader(tsvfile, delimiter='\t', quotechar='"')
    for row in spamreader:
        spread_move_list.append(row[0])
print('Read and processed spread move file.')

move_list = {}
with open('Pokemon_Data/Moves.csv', newline='\n') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar = '"')
    for row in spamreader:
        Name = row[0]
        Type = row[1].title()
        Category = row[2]
        if row[3] == '?':
            Power = 0
        else:
            Power = int(row[3])
        if row[4] == '?':
            Accuracy = 1
        else:
            Accuracy = float(row[4])/100
        if row[5] == '?':
            PP = 0
        else:
            PP = int(row[5])
        TM = row[6]
        Effect = row[7]
        if row[8] == '?':
            Probability = 0
        else:
            Probability = int(row[8])
        multiplier = 1
        if 'the user, the stronger' in Effect:
            Power = 65  # Applies to Electro Ball, Heavy Slam, Gyro Ball, etc.
        if ('on first turn' in Effect) or ('next turn' in Effect) or ('second turn' in Effect):
            multiplier *= 0.5
        if ('consumed' in Effect) or ('Fails' in Effect) or ('Can only be' in Effect):
            multiplier = 0
        if ('twice in one turn' in Effect) or ('twice in a row' in Effect):
            multiplier *= 2
        elif 'Hits 2-5 times' in Effect:
            multiplier *= 2.2575
        elif 'Attacks thrice with more power each time.' in Effect:
            multiplier *= 94.14/20/Accuracy
        elif '2 turns later' in Effect:
            multiplier *= 1/3
        move_list[Name] = Move(Name, Type, Category, Power, Accuracy, PP, TM, Effect, Probability, is_spread=(Name in spread_move_list), correction_factor=multiplier)
print('Read and processed move file.')

max_move_list = {}
status_max_move = None
with open('Pokemon_Data/Max_moves.txt', newline='\n') as tsvfile:
    spamreader = csv.reader(tsvfile, delimiter='\t', quotechar = '"')
    for row in spamreader:
        Name = row[0]
        Type = row[1].title()
        Effect = row[2]
        if Name != 'Max Guard':
            max_move_list[Type] = Move(Name, Type, 0, 0, 1, None, None, Effect, 100)
        else:
            status_max_move = Move(Name, Type, 'Status', 0, 1, None, None, Effect, 100)
print('Read and processed max move file.')

pokemon_base_stats = {}
with open('Pokemon_Data/All_Pokemon_stats.txt', newline='\n') as tsvfile:
    spamreader = csv.reader(tsvfile, delimiter='\t', quotechar='"')
    for row in spamreader:
        Name = row[2]
        stats = (int(row[3]), int(row[4]), int(row[5]), int(row[6]), int(row[7]), int(row[8]))
        pokemon_base_stats[Name] = stats
print('Read and processed Pokemon stats file.')

pokemon_types = {}
with open('Pokemon_Data/Pokemon_types.csv', newline='\n') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        Name = row[0]
        types = (row[1], row[2])
        pokemon_types[Name] = types
print('Read and processed Pokemon types file.')

rental_pokemon = {}
with open('Pokemon_Data/Rental_Pokemon.txt', newline='\n') as file:
    spamreader = csv.reader(file)
    i=0
    dump = []
    for row in spamreader:
        dump.append(row)
    while i < len(dump):
        while len(dump[i]) == 0:
            i += 1
        name = dump[i][0]
        i += 1
        while len(dump[i]) > 0:
            i += 1
        while len(dump[i]) == 0:
            i += 1
        ability = dump[i][0]
        i += 1
        level = int(dump[i][0].split()[1])
        i += 2
        moves = []
        max_moves = []
        while i < len(dump) and len(dump[i]) > 0:
            move = copy(move_list[dump[i][0]])
            moves.append(move)
            if ability == 'Skill Link' and 'Hits 2-5 times' in move.effect:
                move.power *= 5/2.1575
            if move.base_power > 0:
                max_move = copy(max_move_list[move.type])
                max_move.power = matchup_scoring.get_max_move_power(move)
            else:
                max_move = copy(status_max_move)
            max_move.category = move.category
            max_move.PP = move.PP
            max_moves.append(max_move)
            i += 1
        counter = 2
        if name in rental_pokemon:
            print('WARNING: Duplicate entry: '+name)
        rental_pokemon[name] = Pokemon(name,ability,pokemon_types[name],pokemon_base_stats[name],moves,max_moves,level)
print('Read and processed rental Pokemon file.')

boss_pokemon = {}
with open('Pokemon_Data/Boss_Pokemon.txt', newline='\n') as file:
    spamreader = csv.reader(file)
    i=0
    dump = []
    for row in spamreader:
        dump.append(row)
    while i < len(dump):
        while len(dump[i]) == 0:
            i += 1
        name = dump[i][0]
        i += 1
        while len(dump[i]) > 0:
            i += 1
        while len(dump[i]) == 0:
            i += 1
        ability = dump[i][0]
        i += 1
        level = int(dump[i][0].split()[1])
        i += 2
        moves = []
        max_moves = []
        while i < len(dump) and len(dump[i]) > 0:
            move = move_list[dump[i][0]]
            moves.append(move)
            if move.power > 0:
                max_move = copy(max_move_list[move.type])
                max_move.power = matchup_scoring.get_max_move_power(move)
            else:
                max_move = copy(status_max_move)
            max_move.category = move.category
            max_move.PP = move.PP
            max_moves.append(max_move)
            i += 1
        boss_pokemon[name] = Pokemon(name,ability,pokemon_types[name],pokemon_base_stats[name],moves,max_moves,level)
print('Read and processed boss Pokemon file.')

boss_matchup_LUT = {}
for key, attacker in rental_pokemon.items():
    matchups = {}
    for key, defender in boss_pokemon.items():
        matchups[defender.name] = matchup_scoring.evaluate_matchup(attacker, defender, rental_pokemon)
    boss_matchup_LUT[attacker.name] = matchups
    print('Finished computing matchups for '+str(attacker))
print('Computed boss matchup LUT.')

rental_matchup_LUT = {}
rental_pokemon_scores = {}
total_score = 0
for key, attacker in rental_pokemon.items():
    matchups = {}
    attacker_score = 0
    for key, defender in rental_pokemon.items():
        matchups[defender.name] = matchup_scoring.evaluate_matchup(attacker, defender, rental_pokemon)
        attacker_score += matchups[defender.name]
    rental_matchup_LUT[attacker.name] = matchups
    rental_pokemon_scores[attacker.name] = attacker_score
    total_score += attacker_score
    print('Finished computing matchups for '+str(attacker))

for key in rental_pokemon_scores:
    rental_pokemon_scores[key] /= (total_score/len(rental_pokemon))
print('Computed rental matchup LUT.')
    
    

with open('Pokemon_Data/Rental_Pokemon.pickle', 'wb') as file:
    pickle.dump(rental_pokemon, file)
with open('Pokemon_Data/Boss_Pokemon.pickle', 'wb') as file:
    pickle.dump(boss_pokemon, file)
with open('Pokemon_Data/Boss_Matchup_LUT.pickle', 'wb') as file:
    pickle.dump(boss_matchup_LUT, file)
with open('Pokemon_Data/Rental_Matchup_LUT.pickle', 'wb') as file:
    pickle.dump(rental_matchup_LUT, file)
with open('Pokemon_Data/Rental_Pokemon_Scores.pickle', 'wb') as file:
    pickle.dump(rental_pokemon_scores, file)
print('Finished packaging Pokemon!')

