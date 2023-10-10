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


def update_temp_attack_for_defense(defense_units):
    for cur_unit in defense_units:
        cur_unit.temp_attack = cur_unit.defense


def calculate_hits(units):
    dice_results = numpy.random.randint(1, 7, len(units))
    logger.debug("dice_results:  {}".format(dice_results))

    units_that_hit = [x for i, x in enumerate(units) if dice_results[i] <= x.temp_attack]
    logger.debug("len(units_that_hit):  {}".format(len(units_that_hit)))

    return units_that_hit, dice_results


def build_unit_snapshot(units):
    r = [x.copy() for x in units]
    return r


def run_combat(attacker_units, defender_units, battle_type, 
               naval_bombard_fun=run_naval_bombardment, combat_round_fun=run_combat_round):
    # regular land battle
    if BATTLE_TYPE_AMPHIBIOUS == battle_type:
        bombardment_units_that_hit = naval_bombard_fun(attacker_units)
        cur_attacker_units = [x for x in attacker_units if x.unit_type != unit.UNIT_TYPE_NAVAL]
    else:
        bombardment_units_that_hit = None
        cur_attacker_units = list(attacker_units)
        
    cur_attacker_units = sorted(cur_attacker_units, key=lambda x: x.ipc)
    
    cur_defender_units = sorted(defender_units, key=lambda x: x.ipc)
    update_temp_attack_for_defense(cur_defender_units)

    combat_round = 0
    results_list = [(combat_round, build_unit_snapshot(cur_attacker_units), build_unit_snapshot(cur_defender_units))]
    while len(cur_attacker_units) > 0 and len(cur_defender_units) > 0:
        logger.debug("###########################")
        logger.debug("combat_round:  {}".format(combat_round))
        calculate_temp_attacks(cur_attacker_units)

        logger.debug("cur_attacker_units:  {}".format(cur_attacker_units))
        logger.debug("cur_defender_units:  {}".format(cur_defender_units))

        attacker_units_that_hit, defender_units_that_hit = combat_round_fun(cur_attacker_units, cur_defender_units)
        num_attack_hits = len(attacker_units_that_hit)
        if BATTLE_TYPE_AMPHIBIOUS == battle_type and combat_round == 0:
            num_attack_hits += len(bombardment_units_that_hit)
        logger.debug("num_attack_hits:  {}".format(num_attack_hits))

        num_defense_hits = len(defender_units_that_hit)
        logger.debug("num_defense_hits:  {}".format(num_defense_hits))

        cur_attacker_units = cur_attacker_units[num_defense_hits:]
        cur_defender_units = cur_defender_units[num_attack_hits:]

        combat_round += 1

        results_list.append((combat_round, build_unit_snapshot(cur_attacker_units), build_unit_snapshot(cur_defender_units)))

    return results_list