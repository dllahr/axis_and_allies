import numpy
import logging

import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.unit as unit

logger = logging.getLogger(setup_logger.LOGGER_NAME)

BATTLE_TYPE_LAND = 0
BATTLE_TYPE_NAVAL = 1
BATTLE_TYPE_AMPHIBIOUS = 2


def run_combat_round(cur_attacker_units, cur_defender_units):
    attacker_units_that_hit,_ = calculate_hits(cur_attacker_units)
    
    defender_units_that_hit,_ = calculate_hits(cur_defender_units)

    return attacker_units_that_hit, defender_units_that_hit


def run_naval_bombardment(attack_units):
    naval_bombardment_units = [x for x in attack_units if x.name in unit.CAN_BOMBARD_NAMES]
    logger.debug("naval_bombardment_units:  {}".format(naval_bombardment_units))

    units_that_hit, _ = calculate_hits(naval_bombardment_units)

    return units_that_hit


def calculate_temp_attacks(attacker_units):
    artillery_units = [x for x in attacker_units if x.name == unit.ARTILLERY]
    num_artillery = len(artillery_units)

    num_paired_infantry = 0
    for i, cur_unit in enumerate(attacker_units):
        cur_unit.temp_attack = cur_unit.attack
        if cur_unit.name == unit.INFANTRY and num_paired_infantry < num_artillery:
            cur_unit.temp_attack = 2
            num_paired_infantry += 1

    return num_artillery, num_paired_infantry


def build_updated_defense_units(defense_units):
    new_defense_units = [x for x in defense_units if x.name != unit.ANTI_AIRCRAFT_ARTILLERY]

    for cur_unit in new_defense_units:
        cur_unit.temp_attack = cur_unit.defense

    return new_defense_units


def calculate_hits(units):
    did_hit_arr, dice_results = calculate_rolls_and_compare([x.temp_attack for x in units])

    units_that_hit = [x for i, x in enumerate(units) if did_hit_arr[i]]
    logger.debug("len(units_that_hit):  {}".format(len(units_that_hit)))

    return units_that_hit, dice_results


def calculate_rolls_and_compare(to_hit_list):
    dice_results = numpy.random.randint(1, 7, len(to_hit_list))
    logger.debug("dice_results:  {}".format(dice_results))

    did_hit_arr = dice_results <= numpy.array(to_hit_list)

    return did_hit_arr, dice_results


def build_unit_snapshot(units):
    r = [x.copy() for x in units]
    return r


def check_and_run_anti_aircraft_artillery(
        attacker_units, defender_units, calc_rolls_and_compare_fun=calculate_rolls_and_compare
    ):
    aaa_units = [x for x in defender_units if x.name == unit.ANTI_AIRCRAFT_ARTILLERY]

    attacker_air_units = [x for x in attacker_units if x.unit_type == unit.UNIT_TYPE_AIR]
    num_attack_air = len(attacker_air_units)
    logger.debug("num_attack_air:  {}".format(num_attack_air))

    num_aaa_hits = 0
    AAA_to_hit_list = []
    if len(aaa_units) > 0 and num_attack_air > 0:
        num_aaa_attacks = num_attack_air if num_attack_air < 3 else 3
        logger.debug("num_aaa_attacks:  {}".format(num_aaa_attacks))

        for cur_aaa_unit in aaa_units:
            AAA_to_hit_list += [cur_aaa_unit.defense]*num_aaa_attacks
        logger.debug("AAA_to_hit_list:  {}".format(AAA_to_hit_list))

        did_hit_arr, _ = calc_rolls_and_compare_fun(AAA_to_hit_list)
        logger.debug("did_hit_arr:  {}".format(did_hit_arr))

        initial_num_aaa_hits = numpy.sum(did_hit_arr*1)
        logger.debug("initial_num_aaa_hits:  {}".format(initial_num_aaa_hits))

        num_aaa_hits = initial_num_aaa_hits if initial_num_aaa_hits <= num_attack_air else num_attack_air

    logger.debug("num_aaa_hits:  {}".format(num_aaa_hits))

    return num_aaa_hits, AAA_to_hit_list


def remove_air_units_from_aaa_defense(attacker_units, num_aaa_hits):
    if num_aaa_hits > 0:
        air_units = [x for x in attacker_units if x.unit_type == unit.UNIT_TYPE_AIR]
        destroyed_air_unit_ids = set([x.id for x in air_units[:num_aaa_hits]])
    
        remaining_attacker_units = [x for x in attacker_units if not x.id in destroyed_air_unit_ids]
    else:
        remaining_attacker_units=attacker_units

    return remaining_attacker_units


def check_for_and_run_submarine_surprise_attack(
        cur_attacker_units, cur_defender_units, calc_rolls_and_compare_fun=calculate_rolls_and_compare
    ):
    attack_subs = [x for x in cur_attacker_units if unit.SUBMARINE == x.name]
    defender_destroyers = [x for x in cur_defender_units if unit.DESTROYER == x.name]

    if len(attack_subs) > 0 and len(defender_destroyers) == 0:
        logger.debug("submarine surprise attack len(attack_subs):  {}  len(defender_destroyers):  {}".format(
            len(attack_subs), len(defender_destroyers)
        ))
        to_hit_list = [x.temp_attack for x in attack_subs]
        did_hit_arr,_ = calc_rolls_and_compare_fun(to_hit_list)

        num_sub_surprise_hits = numpy.sum(did_hit_arr*1)

        did_surprise_attack_happen = True

    else:
        logger.debug("no submarine surprise attack len(attack_subs):  {}  len(defender_destroyers):  {}".format(
            len(attack_subs), len(defender_destroyers)
        ))
        num_sub_surprise_hits = 0
        did_surprise_attack_happen = False

    return num_sub_surprise_hits, did_surprise_attack_happen


def remove_naval_units_from_sub_attack(cur_defender_units, num_sub_hits):
    if num_sub_hits > 0:
        naval_units = [x for x in cur_defender_units if x.unit_type == unit.UNIT_TYPE_NAVAL]
        destroyed_naval_unit_ids = set([x.id for x in naval_units[:num_sub_hits]])

        remaining_defender_units = [x for x in cur_defender_units if not x.id in destroyed_naval_unit_ids]
    else:
        remaining_defender_units = cur_defender_units
    
    return remaining_defender_units


def run_naval_bombardment_if_needed(battle_type, cur_attacker_units,
                                    naval_bombard_fun=run_naval_bombardment):
    if BATTLE_TYPE_AMPHIBIOUS == battle_type:
        bombardment_units_that_hit = naval_bombard_fun(cur_attacker_units)
        logger.debug("BATTLE_TYPE_AMPHIBIOUS - bombardment_units_that_hit:  {}".format(bombardment_units_that_hit))

        cur_attacker_units = [x for x in cur_attacker_units if x.unit_type != unit.UNIT_TYPE_NAVAL]
    else:
        bombardment_units_that_hit = []

    return cur_attacker_units, len(bombardment_units_that_hit)
    

def run_aaa_defense(cur_attacker_units, cur_defender_units):
    num_aaa_hits,_ = check_and_run_anti_aircraft_artillery(cur_attacker_units, cur_defender_units)

    cur_attacker_units = remove_air_units_from_aaa_defense(cur_attacker_units, num_aaa_hits)

    return cur_attacker_units


def run_combat(attacker_units, defender_units, battle_type, 
               naval_bombard_fun=run_naval_bombardment, combat_round_fun=run_combat_round):

    cur_attacker_units = sorted(attacker_units, key=lambda x: x.ipc)
    calculate_temp_attacks(cur_attacker_units)
    cur_defender_units = sorted(defender_units, key=lambda x: x.ipc)

    cur_attacker_units, num_bombardment_hits = run_naval_bombardment_if_needed(battle_type, cur_attacker_units, naval_bombard_fun)
    
    cur_attacker_units = run_aaa_defense(cur_attacker_units, cur_defender_units)

    cur_defender_units = build_updated_defense_units(cur_defender_units)

    combat_round = 0
    results_list = [(combat_round, build_unit_snapshot(cur_attacker_units), build_unit_snapshot(cur_defender_units))]
    while len(cur_attacker_units) > 0 and len(cur_defender_units) > 0:
        logger.debug("###########################")
        logger.debug("combat_round:  {}".format(combat_round))
        calculate_temp_attacks(cur_attacker_units)

        did_surprise_attack_happen = False
        if BATTLE_TYPE_NAVAL == battle_type:
            num_sub_surprise_hits, did_surprise_attack_happen = check_for_and_run_submarine_surprise_attack(
                cur_attacker_units, cur_defender_units
            )
            # units removed by submarine surprise hits get removed immediately no defense attack
            if did_surprise_attack_happen:
                cur_defender_units = remove_naval_units_from_sub_attack(cur_defender_units, num_sub_surprise_hits)

        logger.debug("cur_attacker_units:  {}".format(cur_attacker_units))
        logger.debug("cur_defender_units:  {}".format(cur_defender_units))

        attacker_units_that_hit, defender_units_that_hit = combat_round_fun(cur_attacker_units, cur_defender_units)
        num_general_attack_hits = len([x for x in attacker_units_that_hit if x.name != unit.SUBMARINE])
        num_sub_hits = len([x for x in attacker_units_that_hit if x.name == unit.SUBMARINE])
        logger.debug("num_sub_hits:  {}".format(num_sub_hits))

        if combat_round == 0:
            num_general_attack_hits += num_bombardment_hits
        logger.debug("num_general_attack_hits:  {}".format(num_general_attack_hits))

        num_defense_hits = len(defender_units_that_hit)
        logger.debug("num_defense_hits:  {}".format(num_defense_hits))

        cur_attacker_units = cur_attacker_units[num_defense_hits:]

        if not did_surprise_attack_happen:
            cur_defender_units = remove_naval_units_from_sub_attack(cur_defender_units, num_sub_hits)

        cur_defender_units = cur_defender_units[num_general_attack_hits:]

        combat_round += 1

        results_list.append((combat_round, build_unit_snapshot(cur_attacker_units), build_unit_snapshot(cur_defender_units)))

    return results_list