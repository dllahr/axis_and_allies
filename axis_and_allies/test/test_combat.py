import unittest
import logging
import axis_and_allies.setup_logger as setup_logger

import numpy

import axis_and_allies.combat as combat
import axis_and_allies.unit as unit


logger = logging.getLogger(setup_logger.LOGGER_NAME)

# Some notes on testing conventions (more in cuppers convention doc):
#    (1) Use "self.assert..." over "assert"
#        - self.assert* methods: https://docs.python.org/2.7/library/unittest.html#assert-methods
#       - This will ensure that if one assertion fails inside a test method,
#         exectution won't halt and the rest of the test method will be executed
#         and other assertions are also verified in the same run.  
#     (2) For testing exceptions use:
#        with self.assertRaises(some_exception) as context:
#            [call method that should raise some_exception]
#        self.assertEqual(str(context.exception), "expected exception message")
#
#        self.assertAlmostEquals(...) for comparing floats

test_unit_json = """
{
    "always_hit":{
        "ipc":1001,
        "attack":7,
        "defense":7,
        "unit_type":"land",
        "max_hit_points":1,
        "move":1
    },
    "always_miss":{
        "ipc":1003,
        "attack":0,
        "defense":0,
        "unit_type":"land",
        "max_hit_points":1,
        "move":1
    }
}
""".strip()

unit_dict = None

def load_units():
    with open("../unit_data.json") as file:
        json_str = file.read().strip()
    my_unit_dict = unit.load_from_json(json_str)

    my_unit_dict.update(
        unit.load_from_json(test_unit_json)
    )
    
    t = my_unit_dict["always_miss"].copy()
    t.unit_type = unit.UNIT_TYPE_NAVAL
    t.name = "always_miss_naval"
    my_unit_dict[t.name] = t

    u = my_unit_dict["always_hit"].copy()
    u.unit_type = unit.UNIT_TYPE_NAVAL
    u.name = "always_hit_naval"
    my_unit_dict[u.name] = u
    
    return my_unit_dict

def build_units():
    units = [unit_dict[name].copy() for name in sorted(unit_dict.keys())]
    return units

class TestCombat(unittest.TestCase):
    def test_calculate_hits(self):
        units = build_units()

        for i in range(100):
            units_that_hit, dice_results = combat.calculate_hits(units)
            
            if i%10 == 0:
                logger.debug("len(units_that_hit):  {}".format(units_that_hit))
                logger.debug("dice_results:  {}".format(dice_results))

            self.assertTrue(all(dice_results >= 1))
            self.assertTrue(all(dice_results <= 6))

            compare = dice_results <= numpy.array([x.attack for x in units])
            if i%10 == 0:
                logger.debug("compare:  {}".format(compare))
            self.assertEqual(len(units_that_hit), sum(compare))

    def test_calculate_temp_attacks(self):
        units = build_units()
        units.append(unit_dict[unit.INFANTRY].copy())
        
        infantry_units = [x for x in units if x.name == unit.INFANTRY]
        logger.debug("before calculate_temp_attacks infantry_units:  {}".format(infantry_units))

        r = combat.calculate_temp_attacks(units)
        logger.debug("r:  {}".format(r))
        self.assertEqual(1, r[0])
        self.assertEqual(1, r[1])
        logger.debug("after calculate_temp_attacks infantry_units:  {}".format(infantry_units))

        self.assertEqual(2, infantry_units[0].temp_attack)
        self.assertEqual(infantry_units[1].attack, infantry_units[1].temp_attack)

    def test_run_combat_round(self):
        attacker_units = build_units()
        attacker_units.append(unit_dict["always_hit"].copy())
        attacker_units.append(unit_dict["always_miss"].copy())
        defender_units = build_units()
        defender_units.append(unit_dict["always_hit"].copy())
        defender_units.append(unit_dict["always_miss"].copy())

        attack_hits_list = []
        defense_hits_list = []
        for i in range(100):
            attacker_units_that_hit, defender_units_that_hit = combat.run_combat_round(attacker_units, defender_units)
            attack_hits_list.append(attacker_units_that_hit)
            defense_hits_list.append(defender_units_that_hit)

            attacker_hit_names = set([x.name for x in attacker_units_that_hit])
            self.assertIn("always_hit", attacker_hit_names)
            self.assertNotIn("always_miss", attacker_hit_names)

            defender_hit_names = set([x.name for x in defender_units_that_hit])
            self.assertIn("always_hit", defender_hit_names)
            self.assertNotIn("always_miss", defender_hit_names)

        num_attack_hits_list = [len(x) for x in attack_hits_list]
        logger.debug("num_attack_hits_list:  {}".format(num_attack_hits_list))
        num_defense_hits_list = [len(x) for x in defense_hits_list]
        logger.debug("num_defense_hits_list:  {}".format(num_defense_hits_list))

    def test_run_combat_land(self):
        t = unit_dict["infantry"]
        u = unit_dict["artillery"]
        v = unit_dict["tank"]

        attacker_units = [t.copy(), v.copy(), u.copy(), t.copy()]
        defender_units = [u.copy(), t.copy(), t.copy(), v.copy()]

        r = combat.run_combat(attacker_units, defender_units, combat.BATTLE_TYPE_LAND)
        _, remain_attacker_units, remain_defender_units = r[-1]
        logger.debug("remain_attacker_units:  {}".format(remain_attacker_units))
        logger.debug("remain_defender_units:  {}".format(remain_defender_units))

        self.assertTrue(len(remain_attacker_units) == 0 or len(remain_defender_units) == 0)

    def test_run_combat_amphibious(self):
        t = unit_dict["infantry"]
        u = unit_dict["artillery"]
        v = unit_dict["tank"]

        attacker_units = [t.copy(), u.copy(), unit_dict["cruiser"].copy()]
        defender_units = [t.copy(), t.copy()]

        logger.debug("####################")
        logger.debug("naval bombardment misses, land attack always hits, defense always misses")
        r = combat.run_combat(
            attacker_units, defender_units, combat.BATTLE_TYPE_AMPHIBIOUS,
            naval_bombard_fun=lambda x: [], combat_round_fun=lambda x,y: ([1],[])
        )
        _, remain_attacker_units, remain_defender_units = r[-1]
        logger.debug("remain_attacker_units:  {}".format(remain_attacker_units))
        logger.debug("remain_defender_units:  {}".format(remain_defender_units))
        self.assertEqual(2, len(remain_attacker_units))
        remain_attacker_units_ids = set([x.id for x in remain_attacker_units])
        self.assertIn(attacker_units[0].id, remain_attacker_units_ids)
        self.assertIn(attacker_units[1].id, remain_attacker_units_ids)
        self.assertEqual(0, len(remain_defender_units))

        logger.debug("####################")
        logger.debug("naval bombardment hits, land attack always misses, defense always hits")
        r = combat.run_combat(
            attacker_units, defender_units, combat.BATTLE_TYPE_AMPHIBIOUS,
            naval_bombard_fun=lambda x: [1], combat_round_fun=lambda x,y: ([],[1])
        )
        _, remain_attacker_units, remain_defender_units = r[-1]
        logger.debug("remain_attacker_units:  {}".format(remain_attacker_units))
        logger.debug("remain_defender_units:  {}".format(remain_defender_units))
        self.assertEqual(0, len(remain_attacker_units))
        self.assertEqual(1, len(remain_defender_units))
        remain_defender_units_ids = set([x.id for x in remain_defender_units])
        self.assertIn(remain_defender_units[0].id, remain_defender_units_ids)

        logger.debug("####################")
        logger.debug("functional / random")
        r = combat.run_combat(
            attacker_units, defender_units, combat.BATTLE_TYPE_AMPHIBIOUS
        )
        _, remain_attacker_units, remain_defender_units = r[-1]
        logger.debug("remain_attacker_units:  {}".format(remain_attacker_units))
        logger.debug("remain_defender_units:  {}".format(remain_defender_units))
        self.assertTrue(len(remain_attacker_units) == 0 or len(remain_defender_units) == 0)

    def test_run_naval_bombardment(self):
        t = unit_dict["always_hit_naval"].copy()
        t.name = "battleship"
        u = unit_dict["always_miss_naval"].copy()
        u.name = "cruiser"
        units = [
            unit_dict["cruiser"].copy(), unit_dict["battleship"].copy(), unit_dict["always_hit"].copy(), t, u
        ]

        for i in range(100):
            units_that_hit = combat.run_naval_bombardment(units)

            if i%10 == 0:
                logger.debug("units_that_hit:  {}".format(units_that_hit))

            self.assertIn(t, units_that_hit)
            self.assertNotIn(u, units_that_hit)

if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unit_dict = load_units()

    unittest.main()
