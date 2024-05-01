import logging

import numpy

import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.min_max.event_tree as evtre

logger = logging.getLogger(setup_logger.LOGGER_NAME)


def recurse_build_by_IPC_max_usage(IPC_cost_arr, total_IPC, current_entry, all_entry_set, min_IPC_cost):
    for i in range(IPC_cost_arr.shape[0]):
        new_entry = numpy.array(current_entry, dtype=numpy.uint16)
        new_entry[i] += 1

        new_entry_cost = sum(IPC_cost_arr * new_entry)

        if ((total_IPC - new_entry_cost) < min_IPC_cost):
            if  new_entry_cost <= total_IPC:
                all_entry_set.add(tuple(new_entry))
        else:
            recurse_build_by_IPC_max_usage(IPC_cost_arr, total_IPC, new_entry, all_entry_set, min_IPC_cost)


def recurse_build_by_IPC(IPC_cost_arr, total_IPC, current_entry, all_entry_set, min_IPC_cost):
    for i in range(IPC_cost_arr.shape[0]):
        new_entry = numpy.array(current_entry, dtype=numpy.uint16)
        new_entry[i] += 1

        new_entry_cost = sum(IPC_cost_arr * new_entry)

        if new_entry_cost <= total_IPC:
            all_entry_set.add(tuple(new_entry))
            recurse_build_by_IPC(IPC_cost_arr, total_IPC, new_entry, all_entry_set, min_IPC_cost)


def build_purchase_nodes(IPC_limit, unit_dict, my_event_tree):
    unit_name_list = sorted(unit_dict.keys())
    logger.debug("unit_name_list:  {}".format(unit_name_list))

    IPC_cost_arr = numpy.array([unit_dict[x].ipc for x in unit_name_list])
    logger.debug("IPC_cost_arr:  {}".format(IPC_cost_arr))

    init_entry = numpy.zeros(IPC_cost_arr.shape[0])
    all_entry_set = set()
    recurse_build_by_IPC(IPC_cost_arr, IPC_limit, init_entry, all_entry_set, min(IPC_cost_arr))

    ae_list = list(all_entry_set)
    logger.debug("len(ae_list):  {}".format(len(ae_list)))
    logger.debug("ae_list:\n{}".format(ae_list))

    all_entry_name_count_list = []
    for cur_entry in ae_list:
        cur_cost = sum(IPC_cost_arr * numpy.array(cur_entry))
        cur_dict = {unit_name_list[i]:unit_count for i,unit_count in enumerate(cur_entry)}
        all_entry_name_count_list.append((cur_dict, cur_cost))

    node_list = []
    for cur_entry, cur_cost in all_entry_name_count_list:
        cur_node = {
            "type":evtre.NT_purchase, 
            "IPC_limit":IPC_limit, 
            "purchase_unit_counts":cur_entry,
            "cost":cur_cost
        }
        cur_node.update(my_event_tree.build_basic_node())
        node_list.append(cur_node)

    return node_list