# Package_Pokemon
#   Eric Donders
#   2020-11-27
#   Read information on Pokemon and construct sets of rental and boss Pokemon used in Dynamax Adventures

from Pokemon_Data.Pokemon import Pokemon
from Pokemon_Data.Move import Move
from Pokemon_Data import matchup_scoring
import csv, pickle

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
        move_list[Name] = Move(Name, Type, Category, Power, Accuracy, PP, TM, Effect, Probability)

pokemon_base_stats = {}
with open('Pokemon_Data/All_Pokemon_stats.txt', newline='\n') as tsvfile:
    spamreader = csv.reader(tsvfile, delimiter='\t', quotechar='"')
    for row in spamreader:
        Name = row[2]
        stats = (int(row[3]), int(row[4]), int(row[5]), int(row[6]), int(row[7]), int(row[8]))
        pokemon_base_stats[Name] = stats

pokemon_types = {}
with open('Pokemon_Data/Pokemon_types.csv', newline='\n') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        Name = row[0]
        types = (row[1], row[2])
        pokemon_types[Name] = types

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
        while i < len(dump) and len(dump[i]) > 0:
            moves.append(move_list[dump[i][0]])
            i += 1
        rental_pokemon[name] = Pokemon(name,ability,pokemon_types[name],pokemon_base_stats[name],moves,level)

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
        while i < len(dump) and len(dump[i]) > 0:
            moves.append(move_list[dump[i][0]])
            i += 1
        boss_pokemon[name] = Pokemon(name,ability,pokemon_types[name],pokemon_base_stats[name],moves,level)


boss_matchup_LUT = {}
for key, attacker in rental_pokemon.items():
    matchups = {}
    for key, defender in boss_pokemon.items():
        matchups[defender.name] = matchup_scoring.evaluate_matchup(attacker, defender)
    boss_matchup_LUT[attacker.name] = matchups

rental_matchup_LUT = {}
rental_pokemon_scores = {}
total_score = 0
for key, attacker in rental_pokemon.items():
    matchups = {}
    attacker_score = 0
    for key, defender in rental_pokemon.items():
        matchups[defender.name] = matchup_scoring.evaluate_matchup(attacker, defender)
        attacker_score += matchups[defender.name]
    rental_matchup_LUT[attacker.name] = matchups
    rental_pokemon_scores[attacker.name] = attacker_score
    total_score += attacker_score

for key in rental_pokemon_scores:
    rental_pokemon_scores[key] /= (total_score/len(rental_pokemon))
    

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

