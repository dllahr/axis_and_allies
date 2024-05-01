import unittest
import logging
import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.game_state as game_state

import axis_and_allies.min_max.event_tree as evtre



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

class TestEventTree(unittest.TestCase):
    def test___init__(self):
        my_evtree = evtre.EventTree()
        logger.debug("my_evtree:  {}".format(my_evtree))

    def test_build_basic_node(self):
        my_evtree = evtre.EventTree()
        r = my_evtree.build_basic_node()
        logger.debug("r:  {}".format(r))

        self.assertIn("children", r)
        self.assertEqual(0, len(r["children"]))
        self.assertIn("id", r)
        self.assertIn("game_state", r)
        self.assertIs(game_state.GameState, type(r["game_state"]))


if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unittest.main()
