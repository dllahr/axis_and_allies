import unittest
import logging
import axis_and_allies.setup_logger as setup_logger

import numpy
import pprint

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



class TestUnit(unittest.TestCase):
    def test_load_from_json(self):
        json_str = """
            {
                "infantry":{
                    "ipc":3,
                    "attack":1,
                    "defense":2,
                    "unit_type":"land",
                    "max_hit_points":1,
                    "move":1
                },
                "artillery":{
                    "ipc":4,
                    "attack":2,
                    "defense":2,
                    "unit_type":"land",
                    "max_hit_points":1,
                    "move":1
                }
            }"""
        unit_dict = unit.load_from_json(json_str)
        pprint.pprint(unit_dict)
        self.assertEqual(2, len(unit_dict))
        self.assertIn("artillery", unit_dict)
        self.assertIn("infantry", unit_dict)

    def test_load_from_json_file(self):
        with open("../unit_data.json") as file:
            json_str = file.read().strip()
        unit_dict = unit.load_from_json(json_str)
        pprint.pprint(unit_dict)
        self.assertIn("artillery", unit_dict)
        self.assertIn("infantry", unit_dict)



if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unittest.main()
