import unittest
import logging

import numpy

import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.build_unit_dict as build_unit_dict
import axis_and_allies.min_max.event_tree as evtre

import axis_and_allies.min_max.build_purchase_nodes as bpn

unit_dict = None


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

class TestBuildPurchaseNodes(unittest.TestCase):

    def test_recurse_build_by_IPC_max_usage(self):
        total_IPC = 10

        my_unit_dict = {}
        for x in ["infantry", "artillery", "tank"]:
            my_unit_dict[x] = unit_dict[x].copy()

        unit_name_list = sorted(my_unit_dict.keys())
        logger.debug("unit_name_list:  {}".format(unit_name_list))

        IPC_cost_arr = numpy.array([my_unit_dict[x].ipc for x in unit_name_list])
        logger.debug("IPC_cost_arr:  {}".format(IPC_cost_arr))

        init_entry = numpy.zeros(IPC_cost_arr.shape[0])
        all_entry_set = set()
        bpn.recurse_build_by_IPC_max_usage(IPC_cost_arr, total_IPC, init_entry, all_entry_set, min(IPC_cost_arr))
        ae_list = sorted(all_entry_set)
        logger.debug("len(ae_list):  {}".format(len(ae_list)))
        logger.debug("ae_list:\n{}".format(ae_list))

        total_ipc_cost_arr = numpy.array([sum(numpy.array(x)*IPC_cost_arr) for x in ae_list])
        logger.debug("total_ipc_cost_arr:  {}".format(total_ipc_cost_arr))
        self.assertTrue(all(total_ipc_cost_arr <= total_IPC))

        remain_ipc_arr = total_IPC - total_ipc_cost_arr
        logger.debug("remain_ipc_arr:  {}".format(remain_ipc_arr))
        self.assertTrue(all(remain_ipc_arr < min(IPC_cost_arr)))

    def test_recurse_build_by_IPC(self):
        total_IPC = 10

        logger.debug("***************** simplest example")
        my_unit_dict = {}
        for x in ["infantry"]:
            my_unit_dict[x] = unit_dict[x].copy()

        unit_name_list = sorted(my_unit_dict.keys())
        logger.debug("unit_name_list:  {}".format(unit_name_list))

        IPC_cost_arr = numpy.array([my_unit_dict[x].ipc for x in unit_name_list])
        logger.debug("IPC_cost_arr:  {}".format(IPC_cost_arr))

        init_entry = numpy.zeros(IPC_cost_arr.shape[0])
        all_entry_set = set()
        bpn.recurse_build_by_IPC(IPC_cost_arr, total_IPC, init_entry, all_entry_set, min(IPC_cost_arr))
        ae_list = sorted(all_entry_set)
        logger.debug("len(ae_list):  {}".format(len(ae_list)))
        logger.debug("ae_list:\n{}".format(ae_list))

        total_ipc_cost_arr = numpy.array([sum(numpy.array(x)*IPC_cost_arr) for x in ae_list])
        logger.debug("total_ipc_cost_arr:  {}".format(total_ipc_cost_arr))
        self.assertTrue(all(total_ipc_cost_arr <= total_IPC))

        remain_ipc_arr = total_IPC - total_ipc_cost_arr
        logger.debug("remain_ipc_arr:  {}".format(remain_ipc_arr))
        self.assertEqual([(i,) for i in range(1,4)], ae_list)

        logger.debug("***************** more complicated")
        my_unit_dict = {}
        for x in ["infantry", "artillery", "tank"]:
            my_unit_dict[x] = unit_dict[x].copy()

        unit_name_list = sorted(my_unit_dict.keys())
        logger.debug("unit_name_list:  {}".format(unit_name_list))

        IPC_cost_arr = numpy.array([my_unit_dict[x].ipc for x in unit_name_list])
        logger.debug("IPC_cost_arr:  {}".format(IPC_cost_arr))

        init_entry = numpy.zeros(IPC_cost_arr.shape[0])
        all_entry_set = set()
        bpn.recurse_build_by_IPC(IPC_cost_arr, total_IPC, init_entry, all_entry_set, min(IPC_cost_arr))
        ae_list = sorted(all_entry_set)
        logger.debug("len(ae_list):  {}".format(len(ae_list)))
        logger.debug("ae_list:\n{}".format(ae_list))

        total_ipc_cost_arr = numpy.array([sum(numpy.array(x)*IPC_cost_arr) for x in ae_list])
        logger.debug("total_ipc_cost_arr:  {}".format(total_ipc_cost_arr))
        self.assertTrue(all(total_ipc_cost_arr <= total_IPC))

        remain_ipc_arr = total_IPC - total_ipc_cost_arr
        logger.debug("remain_ipc_arr:  {}".format(remain_ipc_arr))

    def test_build_purchase_nodes(self):
        total_IPC = 10

        logger.debug("***************** simplest example")
        my_unit_dict = {}
        for x in ["infantry"]:
            my_unit_dict[x] = unit_dict[x].copy()

        r = bpn.build_purchase_nodes(total_IPC, my_unit_dict, evtre.EventTree())

        logger.debug("len(r):  {}".format(r))
        self.assertEqual(3, len(r))

        for i, x in enumerate(r):
            logger.debug("i:  {}  node:  {}".format(i, x))

        logger.debug("***************** more complicated")
        my_unit_dict = {}
        for x in ["infantry", "artillery", "tank"]:
            my_unit_dict[x] = unit_dict[x].copy()

        r = bpn.build_purchase_nodes(total_IPC, my_unit_dict, evtre.EventTree())

        logger.debug("len(r):  {}".format(r))
        self.assertEqual(10, len(r))

        for i, x in enumerate(r):
            logger.debug("i:  {}  node:  {}".format(i, x))


if __name__ == "__main__":
    setup_logger.setup(verbose=True)

    unit_dict = build_unit_dict.load_units("../../unit_data.json", do_add_test_units=True)

    unittest.main()
