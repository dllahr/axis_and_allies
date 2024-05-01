import logging

# import numpy

import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.min_max.event_tree as evtre
import axis_and_allies.min_max.build_purchase_nodes as build_purchase_nodes
import axis_and_allies.min_max.build_combat_move_nodes as build_combat_move_nodes
import axis_and_allies.min_max.build_combat_nodes as build_combat_nodes

logger = logging.getLogger(setup_logger.LOGGER_NAME)




def build_indiv_player_turn_event_tree(IPC_limit, N_combat_outcome, total_probability_combat_outcome_limit):
    my_event_tree = evtre.EventTree()

    purchase_node_list = build_purchase_nodes.build_purchase_nodes(IPC_limit, my_event_tree)

    my_event_tree.root["children"] = purchase_node_list

    combat_move_node_list = build_combat_move_nodes.build_combat_move_nodes()

    for combat_move_node in combat_move_node_list:
        combat_node_list = build_combat_nodes.build_combat_nodes(N_combat_outcome, total_probability_combat_outcome_limit)
        combat_move_node["children"] = combat_node_list

    