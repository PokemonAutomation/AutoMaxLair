# Matchup Scoring
#   Eric Donders
#   2020-11-27
import copy
from typing import TypeVar, Dict, List
Pokemon = TypeVar('Pokemon')
Move = TypeVar('Move')

def type_damage_multiplier(type1: str, type2: str) -> int:
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


def ability_damage_multiplier(attacker: Pokemon, move_index: int, defender: Pokemon) -> float:
    """Return a damage multiplier stemming from abilities."""
    if attacker.ability in ('Mold Breaker', 'Turboblaze', 'Teravolt'):
        return 1

    move_type = attacker.moves[move_index].type
    if move_type == 'Ground' and defender.ability == 'Levitate':
        if attacker.moves[move_index].name == 'Thousand Arrows':
            return 1
        else:
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


def get_max_move_power(move: Move) -> int:
    if move.type.title() == 'Fighting' or move.type.title() == 'Poison':
        if move.base_power < 10:
            return 0
        elif move.base_power <= 40:
            return 70
        elif move.base_power <= 50:
            return 75
        elif move.base_power <= 60:
            return 80
        elif move.base_power <= 70:
            return 85
        elif move.base_power <= 100:
            return 90
        elif move.base_power <= 140:
            return 95
        else:
            return 100
    else:
        if move.base_power < 10:
            return 0
        elif move.base_power <= 40:
            return 90
        elif move.base_power <= 50:
            return 100
        elif move.base_power <= 60:
            return 110
        elif move.base_power <= 70:
            return 120
        elif move.base_power <= 100:
            return 130
        elif move.base_power <= 140:
            return 140
        else:
            return 150
    


def calculate_damage(attacker: Pokemon, move_index: int, defender: Pokemon, multiple_targets: bool=False) -> float:
    """Return the damage (default %) of a move used by the attacker against the defender."""
    if attacker.dynamax:
        move = attacker.max_moves[move_index]
    else:
        move = attacker.moves[move_index]
        
    modifier = 0.925 # Random between 0.85 and 1
    modifier *= move.accuracy
    if multiple_targets and move.is_spread:
        modifier *= 0.75
    # Ignore weather for now
    # Ignore crits
    if move.type in attacker.types: # Apply STAB
        if attacker.ability == 'Adaptability':
            modifier *= 2
        else:
            modifier *= 1.5
    # Apply type effectiveness
    for i in range(len(defender.types)):
        if move.name != 'Thousand Arrows' or defender.types[i].title() != 'Flying':
            modifier *= type_damage_multiplier(move.type, defender.types[i])
    # Apply status effects
    if move.category == 'Physical' and attacker.status == 'Burn':
        modifier *= 0.5
    # Apply modifiers from abilities
    modifier *= ability_damage_multiplier(attacker, move_index, defender)
    # Apply attacker and defender stats
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

def calculate_average_damage(attackers: List[Pokemon], defenders: List[Pokemon], multiple_targets: bool=False) -> float:
    """Return the average damage output of a range of attackers against a single defender."""
    if len(attackers) == 0 or len(defenders) == 0:
        return 0
    else:
        total_damage = 0
        count = 0
        for key in attackers:
            attacker = attackers[key]
            for key2 in defenders:
                defender = defenders[key2]
                subtotal_damage = 0
                subcount = 0
                for i in range(len(attacker.moves)):
                    subtotal_damage += calculate_damage(attacker, i, defender, multiple_targets)
                    subcount += 1
                total_damage += subtotal_damage / subcount
                count += 1
            
        return total_damage / count

def calculate_move_score(attacker: Pokemon, move_index: int, defender: Pokemon, teammates: Dict[str, Pokemon]={}) -> float:
    """Return a numerical score of an attacker's move against a defender."""
    dealt_damage = 0
    # Calculate contribution of the move itself (assume Dynamaxed boss)
    dealt_damage += calculate_damage(attacker, move_index, defender, False) / 2

    # Estimate contributions by teammates (assume Dynamaxed boss)
    temp_teammates = copy.deepcopy(teammates)
    temp_teammates.pop(attacker.name, None) # Don't count the attacker twice
    temp_teammates.pop(defender.name, None)
    fudge_factor = 1.5 # Average damage of teammates is likely undercounted as some status moves are helpful and the AI chooses better than random moves
    dealt_damage += 3 * calculate_average_damage(temp_teammates, {defender.name:defender}) / 2 * fudge_factor

    # Estimate contributions from status moves
    #   TODO: implement status moves besides Wide Guard
    
    # Estimate damage received
    received_damage = 0
    for i in range(len(defender.moves)):
        if defender.moves[i].is_spread:
            if attacker.moves[move_index].name != 'Wide Guard' or attacker.dynamax:
                received_damage += calculate_damage(defender, i, attacker, multiple_targets=True)
                received_damage += 3* calculate_average_damage({defender.name:defender}, teammates, multiple_targets=True)
            else:
                #print('Wide guard stops '+defender.moves[i].name) # DEBUG
                pass
        else:
            received_damage += 0.25 * calculate_damage(defender, i, attacker, multiple_targets=True) / (2 if attacker.dynamax else 1)
            received_damage += 0.75 * calculate_average_damage({defender.name:defender}, teammates, multiple_targets=False)
    average_received_damage = received_damage / len(defender.moves)
                

    # Return the score
    #move = attacker.max_moves[move_index] if attacker.dynamax else attacker.moves[move_index]
    #print('Score for '+attacker.name+' using '+move.name+': '+str(score))
    return dealt_damage / average_received_damage


def evaluate_matchup(attacker: Pokemon, boss: Pokemon, teammates: Dict[str, Pokemon]={}) -> float:
    """Return a matchup score between an attacker and defender, with the attacker using optimal moves and the defender using average moves."""
    if attacker.name == 'Ditto':
        attacker = boss
    base_version = copy.copy(attacker)
    base_version.dynamax = False
    dmax_version = copy.copy(attacker)
    dmax_version.dynamax = False
    score = max(calculate_move_score(base_version, select_best_move(base_version, boss, teammates), boss, teammates),
                (calculate_move_score(base_version, select_best_move(base_version, boss, teammates), boss, teammates)+calculate_move_score(dmax_version, select_best_move(dmax_version, boss, teammates), boss, teammates))/2)
    return score


def select_best_move(attacker: Pokemon, defender: Pokemon, teammates: Dict[str, Pokemon]={}) -> int:
    """Return the index of the move that the attacker should use against the defender."""
    best_score = -100
    best_index = 0
    for i in range(len(attacker.moves)):
        if attacker.PP[i] > 0:
            score = calculate_move_score(attacker, i, defender, teammates=teammates)
            if score > best_score or i == 0:
                best_score = score
                best_index = i
    return best_index

def print_matchup_summary(attacker: Pokemon, defender: Pokemon, teammates: Dict[str, Pokemon]={}) -> None:
    output = 'Matchup between '+attacker.name+' and '+defender.name+': %0.2f' % evaluate_matchup(attacker, defender, teammates)
    print(output)
    for i in range(len(attacker.moves)):
        move_list = attacker.max_moves if attacker.dynamax else attacker.moves
        output = 'Score for '+move_list[i].name+' (Effective BP %i, accuracy %0.2f): ' % (move_list[i].power, move_list[i].accuracy)
        output += '%0.2f' % calculate_move_score(attacker, i, defender, teammates)
        print(output)
    
    
    
        


