# Matchup Scoring
#   Eric Donders
#   2020-11-27

def type_damage_multiplier(type1, type2):
    """Return a damage multiplier based on an attack type and target type."""
    if type2 == '':
        return 1
    types = ('Normal','Fire','Water','Electric','Grass','Ice','Fighting','Poison','Ground','Flying','Psychic','Bug','Rock','Ghost','Dragon','Dark','Steel','Fairy')
    return ((1,1,1,1,1,1,1,1,1,1,1,1,0.5,0,1,1,0.5,1),
            (1,0.5,0.5,1,2,2,1,1,1,1,1,2,0.5,1,0.5,1,2,1),
            (1,2,0.5,1,0.5,1,1,1,2,1,1,1,2,1,0.5,1,1,1),
            (1,1,2,0.5,0.5,1,1,1,0,2,1,1,1,1,0.5,1,1,1),
            (1,0.5,2,1,0.5,1,1,0.5,2,0.5,1,0.5,2,1,0.5,1,0.5,1),
            (1,0.5,0.5,1,2,0.5,1,1,2,2,1,1,1,1,2,1,0.5,1),
            (2,1,1,1,1,2,1,0.5,1,0.5,0.5,0.5,2,0,1,2,2,0.5),
            (1,1,1,1,2,1,1,0.5,0.5,1,1,1,0.5,0.5,1,1,0,2),
            (1,2,1,2,0.5,1,1,2,1,0,1,0.5,2,1,1,1,2,1),
            (1,1,1,0.5,2,1,2,1,1,1,1,2,0.5,1,1,1,0.5,1),
            (1,1,1,1,1,1,2,2,1,1,0.5,1,1,1,1,0,0.5,1),
            (1,0.5,1,1,2,1,0.5,0.5,1,0.5,2,1,1,0.5,1,2,0.5,0.5),
            (1,2,1,1,1,2,0.5,1,0.5,2,1,2,1,1,1,1,0.5,1),
            (0,1,1,1,1,1,1,1,1,1,2,1,1,2,1,0.5,1,1),
            (1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,0.5,0),
            (1,1,1,1,1,1,0.5,1,1,1,2,1,1,2,1,0.5,1,0.5),
            (1,0.5,0.5,0.5,1,2,1,1,1,1,1,1,2,1,1,1,0.5,2),
            (1,0.5,1,1,1,1,2,0.5,1,1,1,1,1,1,2,2,0.5,1)
            )[types.index(type1.title())][types.index(type2.title())]


def ability_damage_multiplier(attacker, move_index, defender):
    """Return a damage multiplier stemming from abilities."""
    if attacker.ability in ('Mold Breaker', 'Turboblaze', 'Teravolt'):
        return 1

    move_type = attacker.moves[move_index].type
    if move_type == 'Ground' and defender.ability == 'Levitate':
        return 0
    elif move_type == 'Water' and defender.ability in ('Water Absorb', 'Storm Drain', 'Dry Skin'):
        return 0
    elif move_type == 'Fire':
        if defender.ability == 'Flash Fire':
            return 0
        elif defender.ability in ('Fluffy', 'Dry Skin'):
            return 2
        elif defender.ability in ('Thick Fat', 'Heatproof'):
            return 0.5
    elif move_type == 'Grass' and defender.ability == 'Sap Sipper':
        return 0
    elif move_type == 'Electric' and defender.ability in ('Lightning Rod', 'Motor Drive', 'Volt Absorb'):
        return 0
    elif move_type == 'Ice' and defender.ability == 'Thick Fat':
        return 0.5

    return 1
    


def calculate_damage(attacker, move_index, defender, output_format='Percentage'):
    """Return the damage (default %) of a move used by the attacker against the defender."""
    move = attacker.moves[move_index]
    modifier = 0.925 # Random between 0.85 and 1
    # Ignore # targets for now (partially dealt with in the boss' movesets
    # Ignore weather for now
    # Ignore crits
    if move.type in attacker.types: # Apply STAB
        if attacker.ability == 'Adaptability':
            modifier *= 2
        else:
            modifier *= 1.5
    modifier *= type_damage_multiplier(move.type, defender.types[0]) * type_damage_multiplier(move.type, defender.types[1])
    if move.category == 'Physical' and attacker.status == 'Burn':
        modifier *= 0.5
    modifier *= ability_damage_multiplier(attacker, move_index, defender)

    if move.category == 'Physical':
        if move.name != 'Body Press':
            numerator = attacker.stats[1]
        else:
            numerator = attacker.stats[2]
        denominator = defender.stats[2]
    else:
        numerator = attacker.stats[3]
        if move.name not in ('Psystrike', 'Psyshock'):
            denominator = defender.stats[4]
        else:
            denominator = defender.stats[2]

    return ((2/5*attacker.level+2)*move.power*numerator/denominator/50 + 2) * modifier / defender.stats[0]

def calculate_move_score(attacker, move_index, defender):
    """Return a numerical score of an attacker's move against a defender."""
    # For now, return a score based on damage alone. Later this function can be modified to give status moves some value
    return calculate_damage(attacker, move_index, defender)


def evaluate_matchup(attacker, defender):
    """Return a matchup score between an attacker and defender, with the attacker using optimal moves and the defender using average moves."""
    attacker_scores = []
    defender_scores = []
    #print('Matchup for '+attacker.name+' vs '+defender.name)
    for i in range(len(attacker.moves)):
        attacker_scores.append(calculate_damage(attacker, i, defender))
    for i in range(len(defender.moves)):
        defender_scores.append(calculate_damage(defender, i, attacker))
    try:
        return max(attacker_scores) / (sum(defender_scores)/len(defender_scores))
    except ZeroDivisionError:
        return 10


def select_best_move(attacker, defender):
    """Return the index of the move that the attacker should use against the defender."""
    best_score = -1
    best_index = 0
    for i in range(len(attacker.moves)):
        if attacker.PP[i] > 0:
            score = calculate_move_score(attacker, i, defender)
            if score > best_score:
                best_score = score
                best_index = i
    return best_index
    
    
    
        


