"""Helper functions for scoring Pokemon against each other."""

# Matchup Scoring
#   Eric Donders
#   2020-11-27

import copy
from typing import List, Tuple, Iterable
from automaxlair.pokemon_classes import Pokemon, Move
from automaxlair.field import Field


def type_damage_multiplier_single(type1: str, type2: str) -> float:
    """Return a damage multiplier based on an attack type and target type."""

    types = (
        'normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting',
        'poison', 'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost',
        'dragon', 'dark', 'steel', 'fairy')
    return (
        (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 0, 1, 1, 0.5, 1),
        (1, 0.5, 0.5, 1, 2, 2, 1, 1, 1, 1, 1, 2, 0.5, 1, 0.5, 1, 2, 1),
        (1, 2, 0.5, 1, 0.5, 1, 1, 1, 2, 1, 1, 1, 2, 1, 0.5, 1, 1, 1),
        (1, 1, 2, 0.5, 0.5, 1, 1, 1, 0, 2, 1, 1, 1, 1, 0.5, 1, 1, 1),
        (1, 0.5, 2, 1, 0.5, 1, 1, 0.5, 2, 0.5, 1, 0.5, 2, 1, 0.5, 1, 0.5, 1),
        (1, 0.5, 0.5, 1, 2, 0.5, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 0.5, 1),
        (2, 1, 1, 1, 1, 2, 1, 0.5, 1, 0.5, 0.5, 0.5, 2, 0, 1, 2, 2, 0.5),
        (1, 1, 1, 1, 2, 1, 1, 0.5, 0.5, 1, 1, 1, 0.5, 0.5, 1, 1, 0, 2),
        (1, 2, 1, 2, 0.5, 1, 1, 2, 1, 0, 1, 0.5, 2, 1, 1, 1, 2, 1),
        (1, 1, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 0.5, 1),
        (1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 0.5, 1, 1, 1, 1, 0, 0.5, 1),
        (1, 0.5, 1, 1, 2, 1, 0.5, 0.5, 1, 0.5, 2, 1, 1, 0.5, 1, 2, 0.5, 0.5),
        (1, 2, 1, 1, 1, 2, 0.5, 1, 0.5, 2, 1, 2, 1, 1, 1, 1, 0.5, 1),
        (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 1, 1),
        (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 0.5, 0),
        (1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 2, 1, 1, 2, 1, 0.5, 1, 0.5),
        (1, 0.5, 0.5, 0.5, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0.5, 2),
        (1, 0.5, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 1, 1, 1, 2, 2, 0.5, 1)
    )[types.index(type1)][types.index(type2)]


def type_damage_multiplier(move_type: str, defender_types: List[str]) -> float:
    """Return a damage multiplier based on an attack type and target types."""
    factor = 1.0
    for defender_type in defender_types:
        factor *= type_damage_multiplier_single(move_type, defender_type)
    return factor


def weather_damage_multiplier(
    attacker: Pokemon, move: Move, defender: Pokemon, field: Field
) -> float:
    modifier = 1
    if field.is_weather_sunlight():
        if move.name_id == 'solar-beam':
            modifier *= 2
        elif move.name_id == 'thunder' or move.name_id == 'hurricane':
            modifier *= (0.5 / 0.7)
        elif move.name_id == 'weather-ball':
            move.type_id = 'fire'
            modifier *= 2

        if move.type_id == 'fire':
            modifier *= 1.5
        elif move.type_id == 'water':
            modifier *= 0.5
    elif field.is_weather_rain():
        if move.name_id == 'solar-beam':
            modifier *= 0.5
        elif move.name_id == 'thunder' or move.name_id == 'hurricane':
            modifier *= (1.0 / 0.7)
        elif move.name_id == 'weather-ball':
            move.type_id = 'water'
            modifier *= 2

        if move.type_id == 'water':
            modifier *= 1.5
        elif move.type_id == 'fire':
            modifier *= 0.5

    elif field.is_weather_hail():
        if move.name_id == 'solar-beam':
            modifier *= 0.5
        elif move.name_id == 'blizzard':
            modifier *= (1.0 / 0.7)
        elif move.name_id == 'weather-ball':
            move.type_id = 'ice'
            modifier *= 2
    elif field.is_weather_sandstorm():
        if move.name_id == 'solar-beam':
            modifier *= 0.5
        elif move.name_id == 'weather-ball':
            move.type_id = 'rock'
            modifier *= 2
    else:
        if move.name_id == 'weather-ball':
            move.type_id = 'normal'

    return modifier


def terrain_damage_multiplier(
    attacker: Pokemon, move: Move, defender: Pokemon, field: Field
) -> float:
    modifier = 1.0

    if 'flying' not in attacker.type_ids or (
        'levitate' != attacker.ability_name_id
    ):
        if field.is_terrain_electric():
            if move.name_id == 'terrain-pulse':
                move.type_id = 'electric'
                modifier *= 1.5

            if move.type_id == 'electric':
                modifier *= 1.3
        elif field.is_terrain_grassy():
            if move.name_id == 'terrain-pulse':
                move.type_id = 'grass'
                modifier *= 1.5

            if move.type_id == 'grass':
                modifier *= 1.3
        elif field.is_terrain_psychic():
            if move.name_id == 'terrain-pulse':
                move.type_id = 'psychic'
                modifier *= 1.5
            elif move.name_id == 'expanding-force':
                modifier *= 1.5

            if move.type_id == 'psychic':
                modifier *= 1.3

        elif field.is_terrain_misty():
            if move.name_id == 'terrain-pulse':
                move.type_id = 'fairy'
                modifier *= 1.5

            if move.type_id == 'dragon':
                modifier *= 0.5

    if 'flying' not in defender.type_ids or (
        'levitate' != defender.ability_name_id
    ):
        if field.is_terrain_electric():
            if move.name_id == 'rising-voltage':
                modifier *= 2

    return modifier


def ability_damage_multiplier(
    attacker: Pokemon, move_index: int, defender: Pokemon
) -> float:
    """Return a damage multiplier stemming from abilities."""

    move_type = attacker.moves[move_index].type_id
    move_name_id = (attacker.moves[move_index].name_id if not attacker.dynamax
                    else attacker.max_moves[move_index].name_id)

    return_val = 1.0

    # Account for abilities that affect the damage of certain move types.
    if attacker.ability_name_id not in (
        'mold-breaker', 'turboblaze', 'teravolt'
    ):
        if move_type == 'ground' and defender.ability_name_id == 'levitate':
            if move_name_id == 'thousand-arrows':
                return_val = 1.0
            else:
                return_val = 0.0
        elif move_type == 'water' and defender.ability_name_id in (
            'water-absorb', 'storm-drain', 'dry-skin'
        ):
            return_val = -1.0
        elif move_type == 'fire':
            if defender.ability_name_id == 'flash-fire':
                return_val = -1.0
            elif defender.ability_name_id in ('fluffy', 'dry-skin'):
                return_val = 2.0
            elif defender.ability_name_id in ('thick-fat', 'heatproof'):
                return_val = 0.5
        elif move_type == 'grass' and defender.ability_name_id == 'sap-sipper':
            return_val = -1.0
        elif move_type == 'electric' and defender.ability_name_id in (
            'lightning-rod', 'motor-drive', 'volt-absorb'
        ):
            return_val = -1.0
        elif move_type == 'ice' and defender.ability_name_id == 'thick-fat':
            return_val = 0.5
    elif attacker.ability_name_id == 'tinted-lens' and type_damage_multiplier(
        move_type, defender.type_ids
    ) < 1:
        return_val *= 2

    # Account for abilities that affect the damage of specific moves.
    if attacker.ability_name_id == 'iron-fist' and move_name_id in (
        'bullet-punch', 'comet-punch', 'dizzy-punch', 'double-iron-bash',
        'drain-punch', 'dynamic-punch', 'fire-punch', 'focus-punch',
        'hammer-arm', 'ice-hammer', 'ice-punch', 'mach-punch', 'mega-punch',
        'meteor-mash', 'plasma-fists', 'power-up-punch', 'shadow-punch',
        'sky-uppercut', 'surging-strikes', 'thunder-punch', 'wicked-blow'
    ):
        return_val *= 1.2
    elif attacker.ability_name_id == 'strong-jaw' and move_name_id in (
        'bite', 'crunch', 'fire-fang', 'fishious-rend', 'hyper-fang',
        'ice-fang', 'jaw-lock', 'poison-fang', 'psychic-fangs', 'thunder-fang'
    ):
        return_val *= 1.5
    if attacker.ability_name_id == (
        'adaptability' and move_type in attacker.type_ids
    ):
        return_val *= 4 / 3

    return return_val


def calculate_damage(
    attacker: Pokemon, move_index: int, defender: Pokemon, field: Field,
    multiple_targets: bool = False
) -> float:
    """Return the damage (default %) of a move used by the attacker against the
    defender.
    """

    move = (
        attacker.max_moves[move_index] if attacker.dynamax
        else attacker.moves[move_index]
    )

    modifier = 0.925  # Random between 0.85 and 1
    modifier *= move.accuracy
    if multiple_targets and move.is_spread:
        modifier *= 0.75
    # Ignore crits

    # It needs to be before STAB
    modifier *= weather_damage_multiplier(attacker, move, defender, field)

    modifier *= terrain_damage_multiplier(attacker, move, defender, field)

    # It needs to be before STAB
    if move.type_id == 'normal':
        if attacker.ability_name_id == 'refrigerate':
            move.type_id = 'ice'
            modifier *= 1.2
        elif attacker.ability_name_id == 'aerilate':
            move.type_id = 'flying'
            modifier *= 1.2
        elif attacker.ability_name_id == 'galvanize':
            move.type_id = 'electric'
            modifier *= 1.2
        elif attacker.ability_name_id == 'pixilate':
            move.type_id = 'fairy'
            modifier *= 1.2
    else:
        if attacker.ability_name_id == 'normalize':
            move.type_id = 'normal'
            modifier *= 1.2

    if move.type_id in attacker.type_ids:  # Apply STAB
        # Note that Adaptability is handled elsewhere.
        modifier *= 1.5
    # Apply type effectiveness
    if move.name_id != 'thousand-arrows' or 'flying' not in defender.type_ids:
        modifier *= type_damage_multiplier(move.type_id, defender.type_ids)
    # Apply status effects
    if move.category == 'physical' and attacker.status == 'burn':
        modifier *= 0.5
    # Apply modifiers from abilities
    modifier *= ability_damage_multiplier(attacker, move_index, defender)
    # Apply boosts from auras
    if move.type_id == 'fairy' and (
        attacker.ability_name_id == 'fairy-aura'
        or defender.ability_name_id == 'fairy-aura'
    ):
        modifier *= 1.33
    if move.type_id == 'dark' and (
        attacker.ability_name_id == 'dark-aura'
        or defender.ability_name_id == 'dark-aura'
    ):
        modifier *= 1.33

    # Apply attacker and defender stats
    if move.category == 'physical':
        if move.name_id == 'body-press':
            numerator = attacker.stats[2]
        elif move.name_id == 'foul-play':
            numerator = defender.stats[1]
        else:
            numerator = attacker.stats[1]
        denominator = defender.stats[2]
    else:
        numerator = attacker.stats[3]
        if move.name_id not in ('psystrike', 'psyshock'):
            denominator = defender.stats[4]
            if field.is_weather_sandstorm() and 'rock' in defender.type_ids:
                denominator *= 1.5
        else:
            denominator = defender.stats[2]

    return ((
        (2 / 5 * attacker.level + 2) * move.power * numerator / denominator
        / 50 + 2) * modifier / defender.stats[0])


def calculate_average_damage(
    attackers: Iterable[Pokemon], defenders: Iterable[Pokemon],
    field: Field, multiple_targets: bool = False
) -> float:
    """Return the average damage output of a range of attackers against a
    single defender.
    """

    attackers = list(attackers)
    defenders = list(defenders)

    if len(attackers) == 0 or len(defenders) == 0:
        return 0
    else:
        total_damage = 0.0
        count = 0
        for attacker in attackers:
            for defender in defenders:
                subtotal_damage = 0.0
                subcount = 0
                for i in range(len(attacker.moves)):
                    subtotal_damage += calculate_damage(
                        attacker, i, defender, field, multiple_targets)
                    subcount += 1
                total_damage += subtotal_damage / subcount
                count += 1

        return total_damage / count


def calculate_move_score(
    attacker: Pokemon, move_index: int, defender: Pokemon,
    teammates: Iterable[Pokemon], field: Field
) -> float:
    """Return a numerical score of an attacker's move against a defender."""

    teammates = list(teammates)

    # Calculate contribution of the move itself (assume Dynamaxed boss)
    dealt_damage = calculate_damage(
        attacker, move_index, defender, field, False) / 2

    # Estimate contributions by teammates (assume Dynamaxed boss).
    # Don't count the attacker or defender as teammates.
    try:
        teammates.remove(attacker)
    except ValueError:
        pass
    try:
        teammates.remove(defender)
    except ValueError:
        pass
    # The average damage of teammates is likely undercounted as some status
    # moves are helpful and the AI chooses better than random moves.
    fudge_factor = 1.5
    dealt_damage += 3 * calculate_average_damage(
        teammates, [defender], field) / 2 * fudge_factor

    # Estimate contributions from status moves.
    #   TODO: implement status moves besides Wide Guard.

    # Estimate damage received.
    received_damage = 0.0
    received_regular_damage = 0.0
    received_max_move_damage = 0.0
    max_move_probability = 0.3  # Estimate!
    original_dynamax_state = defender.dynamax
    # Calculate damage from regular moves.
    defender.dynamax = False
    num_moves = len(defender.moves)
    for i in range(num_moves):
        if defender.moves[i].is_spread and not defender.dynamax:
            if (
                attacker.moves[move_index].name_id != 'wide-guard'
                or attacker.dynamax
            ):
                received_regular_damage += calculate_damage(
                    defender, i, attacker, field, multiple_targets=True
                ) / num_moves
                received_regular_damage += 3 * calculate_average_damage(
                    [defender], teammates, field,
                    multiple_targets=True
                ) / num_moves
            else:
                # print('Wide guard stops '+defender.moves[i].name) # DEBUG
                pass
        else:
            received_regular_damage += (
                0.25 * calculate_damage(defender, i, attacker, field)
                / (2 if attacker.dynamax else 1)
            ) / num_moves
            received_regular_damage += (
                0.75 * calculate_average_damage([defender], teammates, field)
            ) / num_moves
    # Calculate damage from Max Moves.
    # Note that bosses never seem to use Max Guard. It is assumed that the move
    # index is selected first, followed by the choice of whether or not to use
    # the max version.
    defender.dynamax = True
    num_max_moves = min(4, len(defender.max_moves))
    for i in range(num_max_moves):
        received_max_move_damage += (
            0.25 * calculate_damage(defender, i, attacker, field)
            / (2 if attacker.dynamax else 1)
        ) / num_max_moves
        received_max_move_damage += (
            0.75 * calculate_average_damage([defender], teammates, field)
        ) / num_max_moves
    # Return the defender to its original dynamax state.
    defender.dynamax = original_dynamax_state

    # Calculate the incoming damage as a weighted average of regular and max
    # moves.
    received_damage = (
        received_regular_damage * (1 - max_move_probability)
        + received_max_move_damage * max_move_probability
    )

    # Return the score
    try:
        return dealt_damage / received_damage
    except ZeroDivisionError:
        # just in case received damage is zero, the score is indefinite
        # I'm setting it to 1.0 just for convenience
        return 1.0


def evaluate_matchup(
    attacker: Pokemon, boss: Pokemon, teammates: Iterable[Pokemon] = [],
    num_lives: int = 1
) -> float:
    """Return a matchup score between an attacker and defender, with the
    attacker using optimal moves and the defender using average moves.
    """

    # Transform Ditto (Dynamax Adventure Ditto has Imposter).
    if attacker.name_id == 'ditto':
        attacker = transform_ditto(attacker, boss)
    elif boss.name_id == 'ditto':
        boss = transform_ditto(boss, attacker)

    # Calculate scores for base and Dynamaxed versions of the attacker.
    base_version = copy.copy(attacker)
    base_version.dynamax = False
    dmax_version = copy.copy(attacker)
    dmax_version.dynamax = True
    base_version_score = select_best_move(
        base_version, boss, Field(), teammates)[2]
    dmax_version_score = select_best_move(
        dmax_version, boss, Field(), teammates)[2]
    score = max(
        base_version_score, (base_version_score + dmax_version_score) / 2)

    # Adjust the score depending on the Pokemon's HP. If there are multiple
    # lives left, fainting is less important.
    assert 1 <= num_lives <= 4, 'num_lives should be between 1 and 4.'
    HP_correction = ((5 - num_lives) * attacker.HP + num_lives - 1) / 4

    return score * HP_correction


def evaluate_average_matchup(
    attacker: Pokemon, bosses: Iterable[Pokemon],
    teammates: Iterable[Pokemon] = [], num_lives: int = 1
) -> float:
    """Return an average matchup score between an attacker and multiple
    defenders. Wrapper for the evaluate_matchup function which scores a single
    matchup.
    """

    total_score = 0
    for boss in bosses:
        total_score += evaluate_matchup(attacker, boss, teammates, num_lives)

    return 1 if len(bosses) == 0 else total_score / len(bosses)


def select_best_move(
    attacker: Pokemon, defender: Pokemon, field: Field,
    teammates: Iterable[Pokemon] = []
) -> Tuple[int, str, float]:
    """Return the index of the move that the attacker should use against the
    defender.
    """

    best_score = -100.0
    best_index = 0
    best_move_name_id = ''
    for i in range(len(attacker.moves)):
        if attacker.PP[i] > 0:
            score = calculate_move_score(
                attacker, i, defender, teammates, field)
            if score > best_score:
                best_index = i
                best_move_name_id = attacker.moves[i].name_id
                best_score = score
    return best_index, best_move_name_id, best_score


def print_matchup_summary(
    attacker: Pokemon, defender: Pokemon, field: Field,
    teammates: Iterable[Pokemon] = []
) -> None:
    output = (
        f'Matchup between {attacker.name_id} and {defender.name_id}: '
        f'{evaluate_matchup(attacker, defender, teammates):.2f}')
    print(output)
    move_list = attacker.max_moves if attacker.dynamax else attacker.moves
    for i in range(len(attacker.moves)):
        move = move_list[i]
        output = (
            f'Score for {move.name_id} (Effective BP {move.power}, accuracy '
            f'{move.accuracy}, type multiplier '
            f'{type_damage_multiplier(move.type_id, defender.type_ids)}): '
            f'{calculate_move_score(attacker, i, defender, teammates, field)}'
        )
        print(output)


def transform_ditto(ditto: Pokemon, template: Pokemon) -> Pokemon:
    """Get a copy of a Ditto transformed into a template Pokemon."""
    ditto_transformed = copy.copy(template)
    ditto_transformed.name_id = ditto.name_id
    ditto_transformed.names = ditto.names

    HP = ditto.base_stats[0]
    ditto_transformed.base_stats = (
        HP, template.base_stats[1], template.base_stats[2],
        template.base_stats[3], template.base_stats[4], template.base_stats[5])
    ditto_transformed.recalculate_stats()

    if len(ditto_transformed.moves) > 4:
        ditto_transformed.moves = ditto_transformed.moves[:4]
        ditto_transformed.max_moves = ditto_transformed.max_moves[:4]
    ditto_transformed.PP = [5, 5, 5, 5]

    return ditto_transformed


def get_weighted_score(
    rental_score: float, rental_weight: int, boss_score: float,
    boss_weight: int
):
    """Compute a weighted score for a Rental Pokemon."""
    return (
        (rental_score ** rental_weight) * (boss_score ** boss_weight)
    ) ** (1 / (rental_weight + boss_weight))
