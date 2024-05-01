import unittest
import logging
import axis_and_allies.setup_logger as setup_logger

import numpy

import axis_and_allies.combat as combat
import axis_and_allies.unit as unit
import axis_and_allies.build_unit_dict as build_unit_dict


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


unit_dict = None


class TestCombat(unittest.TestCase):
    def test_calculate_hits(self):
        units = build_unit_dict.build_units(unit_dict)

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
        units = build_unit_dict.build_units(unit_dict)
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
        attacker_units = build_unit_dict.build_units(unit_dict)
        attacker_units.append(unit_dict["always_hit"].copy())
        attacker_units.append(unit_dict["always_miss"].copy())
        defender_units = build_unit_dict.build_units(unit_dict)
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
            naval_bombard_fun=lambda x: [], 
            combat_round_fun=lambda x,y: (attacker_units[-1:],[])
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

    def test_check_and_run_anti_aircraft_artillery(self):
        attacker_units = [unit_dict["fighter"].copy()]
        defender_units = [unit_dict["anti-aircraft artillery"]]

        num_aaa_hits, AAA_to_hit_list = combat.check_and_run_anti_aircraft_artillery(
            attacker_units, defender_units, 
            calc_rolls_and_compare_fun=lambda x: (numpy.array([False]), None)
        )
        logger.debug("always miss - num_aaa_hits:  {}".format(num_aaa_hits))
        self.assertEqual(0, num_aaa_hits)
        logger.debug("AAA_to_hit_list:  {}".format(AAA_to_hit_list))
        self.assertEqual(1, len(AAA_to_hit_list))
        self.assertTrue(all([x == defender_units[0].defense for x in AAA_to_hit_list]))

        num_aaa_hits, AAA_to_hit_list = combat.check_and_run_anti_aircraft_artillery(
            attacker_units, defender_units, 
            calc_rolls_and_compare_fun=lambda x: (numpy.array([True]), None)
        )
        logger.debug("always hit - num_aaa_hits:  {}".format(num_aaa_hits))
        self.assertEqual(1, num_aaa_hits)
        logger.debug("AAA_to_hit_list:  {}".format(AAA_to_hit_list))
        self.assertEqual(1, len(AAA_to_hit_list))
        self.assertTrue(all([x == defender_units[0].defense for x in AAA_to_hit_list]))

        attacker_units = [unit_dict["fighter"].copy()]
        defender_units = [unit_dict["anti-aircraft artillery"]]*2

        num_aaa_hits, AAA_to_hit_list = combat.check_and_run_anti_aircraft_artillery(
            attacker_units, defender_units, 
            calc_rolls_and_compare_fun=lambda x: (numpy.array([True, True]), None)
        )
        logger.debug("always hit multiple AAA but should only get 1 hit b/c only 1 aircraft - num_aaa_hits:  {}".format(
            num_aaa_hits))
        self.assertEqual(1, num_aaa_hits)
        logger.debug("AAA_to_hit_list:  {}".format(AAA_to_hit_list))
        self.assertEqual(2, len(AAA_to_hit_list))
        self.assertTrue(all([x == defender_units[0].defense for x in AAA_to_hit_list]))

        attacker_units = [unit_dict["fighter"].copy()]*4
        defender_units = [unit_dict["anti-aircraft artillery"]]

        num_aaa_hits, AAA_to_hit_list = combat.check_and_run_anti_aircraft_artillery(
            attacker_units, defender_units, 
            calc_rolls_and_compare_fun=lambda x: (numpy.array([True, True, True]), None)
        )
        logger.debug("always hit should only have 3 AAA_to_hit_list - num_aaa_hits:  {}".format(
            num_aaa_hits))
        self.assertEqual(3, num_aaa_hits)
        logger.debug("AAA_to_hit_list:  {}".format(AAA_to_hit_list))
        self.assertEqual(3, len(AAA_to_hit_list))
        self.assertTrue(all([x == defender_units[0].defense for x in AAA_to_hit_list]))

    def test_run_combat_aaa(self):
        t = unit_dict["fighter"]
        u = unit_dict["bomber"]
        v = unit_dict["anti-aircraft artillery"]

        attacker_units = [t.copy(), t.copy(), t.copy(), u.copy(), u.copy(), u.copy(), t.copy(), t.copy()]
        defender_units = [v.copy(), v.copy()]

        logger.debug("####################")
        logger.debug("run anti-aircraft artillery combat no checks FYI")
        r = combat.run_combat(
            attacker_units, defender_units, combat.BATTLE_TYPE_LAND
        )
        _, remain_attacker_units, remain_defender_units = r[-1]
        logger.debug("remain_attacker_units:  {}".format(remain_attacker_units))
        logger.debug("remain_defender_units:  {}".format(remain_defender_units))

    def test_build_updated_defense_units(self):
        defense_units = [
            unit_dict["fighter"].copy(), 
            unit_dict["anti-aircraft artillery"].copy(),
            unit_dict["infantry"].copy()
        ]
        for cur_unit in defense_units:
            cur_unit.temp_attack = -1
        logger.debug("defense_units:  {}".format(defense_units))

        updated_defense_units = combat.build_updated_defense_units(defense_units)
        logger.debug("updated_defense_units:  {}".format(updated_defense_units))

        self.assertEqual(2, len(updated_defense_units))
        self.assertTrue(all([x.temp_attack == x.defense for x in updated_defense_units]))
        self.assertFalse(any([x.name == unit.ANTI_AIRCRAFT_ARTILLERY for x in updated_defense_units]))

    def test_remove_air_units_from_aaa_defense(self):
        attack_units = [unit_dict["fighter"].copy(), unit_dict["tank"].copy()]
        r = combat.remove_air_units_from_aaa_defense(attack_units, 0)
        logger.debug("no hits - len(r):  {}".format(len(r)))
        self.assertEqual(2, len(r))
        self.assertEqual(set([x.id for x in attack_units]), set([x.id for x in r]))

        r = combat.remove_air_units_from_aaa_defense(attack_units, 2)
        logger.debug("2 hits but only 1 air unit - r:  {}".format(len(r)))
        self.assertEqual(1, len(r))
        self.assertEqual(attack_units[-1].id, r[0].id)

    def test_check_for_and_run_submarine_surprise_attack(self):
        attacker_units = [unit_dict["submarine"].copy()]
        defender_units = [unit_dict["cruiser"].copy()]
        r = combat.check_for_and_run_submarine_surprise_attack(
            attacker_units, defender_units, calc_rolls_and_compare_fun=lambda x: (numpy.array([True]), None)
        )
        logger.debug("submarine and no destroyer r:  {}".format(r))
        self.assertTrue(r[1])
        self.assertEqual(1, r[0])

        attacker_units = [unit_dict["submarine"].copy()]
        defender_units = [unit_dict["destroyer"].copy()]
        r = combat.check_for_and_run_submarine_surprise_attack(
            attacker_units, defender_units, calc_rolls_and_compare_fun=lambda x: (numpy.array([True]), None)
        )
        logger.debug("submarine and destroyer - no surprise attack and no hit r:  {}".format(r))
        self.assertFalse(r[1])
        self.assertEqual(0, r[0])

        attacker_units = [unit_dict["destroyer"].copy()]
        defender_units = [unit_dict["cruiser"].copy()]
        r = combat.check_for_and_run_submarine_surprise_attack(
            attacker_units, defender_units, calc_rolls_and_compare_fun=lambda x: (numpy.array([True]), None)
        )
        logger.debug("no submarine in attack so not hits:  {}".format(r))
        self.assertFalse(r[1])
        self.assertEqual(0, r[0])

        attacker_units = [unit_dict["submarine"].copy()]
        defender_units = [unit_dict["cruiser"].copy()]
        r = combat.check_for_and_run_submarine_surprise_attack(
            attacker_units, defender_units, calc_rolls_and_compare_fun=lambda x: (numpy.array([False]), None)
        )
        logger.debug("submarine in attack but function always misses so no hit:  {}".format(r))
        self.assertTrue(r[1])
        self.assertEqual(0, r[0])

    def test_remove_naval_units_from_sub_attack(self):
        defender_units = [unit_dict["fighter"].copy(), unit_dict["cruiser"].copy()]

        r = combat.remove_naval_units_from_sub_attack(defender_units, 0)
        logger.debug("no sub surprise hits len(r):  {}".format(len(r)))
        self.assertEqual(2, len(r))

        r = combat.remove_naval_units_from_sub_attack(defender_units, 2)
        logger.debug("2 sub surprise hits but only one naval unit - len(r):  {}".format(len(r)))
        self.assertEqual(1, len(r))

    def test_run_combat_sub_surprise(self):
        attacker_units = [unit_dict["submarine"].copy()]
        defender_units = [unit_dict["cruiser"].copy()]

        logger.debug("####################")
        logger.debug("run submarine surprise attack combat no checks FYI")
        r = combat.run_combat(
            attacker_units, defender_units, combat.BATTLE_TYPE_NAVAL
        )
        _, remain_attacker_units, remain_defender_units = r[-1]
        logger.debug("remain_attacker_units:  {}".format(remain_attacker_units))
        logger.debug("remain_defender_units:  {}".format(remain_defender_units))


if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unit_dict = build_unit_dict.load_units(do_add_test_units=True)

    unittest.main()
