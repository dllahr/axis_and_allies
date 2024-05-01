import unittest
import logging

import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.unit as unit
import axis_and_allies.region as region


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



class TestRegion(unittest.TestCase):
    def test___init__(self):
        r = region.Region(id=2, region_type=region.REGION_TYPE_LAND, ipc_production=3)
        logger.debug("r:  {}".format(r))

    def test_copy(self):
        c = region.Region(name="my_test_region", id=2, ipc_production=3)
        logger.debug("c:  {}".format(c))
        r = c.copy()
        logger.debug("r:  {}".format(r))
        self.assertEqual(c.id, r.id)
        self.assertEqual(c.name, r.name)
        self.assertEqual(c.ipc_production, r.ipc_production)

    def test_load_from_txt(self):
        r_dict, rs_dict = region.load_from_txt("../region_data.txt")

        logger.debug("r_dict[100]:\n{}".format(r_dict[100]))

        r = r_dict[100]
        self.assertIsNotNone(r.id)
        self.assertIsNotNone(r.name)
        self.assertIsNotNone(r.region_type)
        self.assertIsNotNone(r.ipc_production)

        self.assertLess(0, len(r.adjacent_regions))
        adjacent_region_ids = set(r.get_adjacent_region_ids())
        expected_adjacent_region_ids = set([int(x) for x in "101,102,108,104,109".split(",")])
        self.assertEqual(expected_adjacent_region_ids, adjacent_region_ids)

        self.assertEqual(set(r_dict.keys()), set(rs_dict.keys()))

    def test_region_status__init__(self):
        r = region.RegionStatus()
        logger.debug("r:  {}".format(r))

    def test_region_status_copy(self):
        my_region = region.Region(id=2, name="Silesia")
        my_units = [unit.Unit(name="a"), unit.Unit(name="b")]
        r = region.RegionStatus(region=my_region, has_industry=True, unit_list=my_units)
        logger.debug("r:  {}".format(r))

if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unittest.main()
