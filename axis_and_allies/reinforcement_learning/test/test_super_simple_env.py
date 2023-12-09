import unittest
import logging
import axis_and_allies.setup_logger as setup_logger

import numpy

import axis_and_allies.reinforcement_learning.super_simple_env as ssenv


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



class TestSuperSimpleEnv(unittest.TestCase):
    def test___init__(self):
        r = ssenv.SuperSimpleEnv(IPC_limit=10, ipc_cost_arr=numpy.array([3,4,6]))
        logger.debug("r:  {}".format(r))
        logger.debug("r.action_space.shape:  {}".format(r.action_space.shape))

    def test_reset(self):
        c = ssenv.SuperSimpleEnv(IPC_limit=10)
        logger.debug("c.action_space.shape:  {}".format(c.action_space.shape))

        r = c.reset()
        logger.debug("r[0]:  {}".format(r[0]))
        logger.debug("r[1]:  {}".format(r[1]))

        self.assertEqual(c.action_space.shape[0], r[0].shape[0])

    def test_calculate_cost_array(self):
        log_ratio_arr = numpy.array([2., -3., 5.])
        logger.debug("log_ratio_arr:  {}".format(log_ratio_arr))

        ipc_cost_arr = numpy.array([1., 7., 11., 13.])
        logger.debug("ipc_cost_arr:  {}".format(ipc_cost_arr))

        r_ratios, r_costs = ssenv.calculate_unit_ratios_and_cost_array(log_ratio_arr, ipc_cost_arr)
        logger.debug("r:  {}".format(r_costs))

        self.assertEqual(ipc_cost_arr[0], r_costs[0])
        self.assertEqual(28, r_costs[1])
        self.assertEqual(11/8, r_costs[2])
        self.assertEqual(32*13, r_costs[3])


    def test_convert_action_integers(self):
        action = numpy.array([1., 0., 0.])
        ipc_cost = numpy.array([3, 4, 6])

        logger.debug("happy path - buy one each")
        r = ssenv.convert_action_integers(action, 13, ipc_cost)
        logger.debug("happy path - buy one of each - r:  {}".format(r))
        self.assertTrue(all(r == 1))

        logger.debug("######################")
        logger.debug("require adjusting units")
        action = numpy.array([1., 0.5, 0.])
        r = ssenv.convert_action_integers(action, 29, ipc_cost)
        logger.debug("require adjusting units - r:  {}".format(r))
        self.assertEqual(1, r[0])
        self.assertEqual(3, r[1])
        self.assertEqual(2, r[2])

        logger.debug("######################")
        logger.debug("maximize excess")
        action = numpy.array([1., 0., 0.])
        r = ssenv.convert_action_integers(action, 58, ipc_cost)

        logger.debug("######################")
        logger.debug("IPC limit low")
        action = numpy.array([1., 0., 0., 0., 0.])
        ipc_cost = numpy.array([3, 4, 6, 10, 12])
        r = ssenv.convert_action_integers(action, 10, ipc_cost)
        logger.debug("IPC limit low - r:  {}".format(r))

    def test_render(self):
        r = ssenv.SuperSimpleEnv(IPC_limit=10, ipc_cost_arr=numpy.array([3,4,6,10,12]))
        r.render()
        
if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unittest.main()
