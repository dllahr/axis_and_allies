import logging

import os
import shutil

import numpy
import pandas
import plotly.express as pltxpr

import axis_and_allies.combat as combat
import axis_and_allies.unit as unit
import axis_and_allies.setup_logger as setup_logger

logger = logging.getLogger(setup_logger.LOGGER_NAME)


def load_units():
    with open("unit_data.json") as file:
        json_str = file.read().strip()
    my_unit_dict = unit.load_from_json(json_str)
    
    return my_unit_dict

def run_sim_01(unit_dict):
    attack_unit_names = ["fighter"]*4 + ["bomber"] + ["artillery"] + ["infantry"]*2 + ["tank"] + ["cruiser"]*2
    attack_units = build_units_from_names(attack_unit_names)
    
    defense_unit_names = ["fighter"]*2 + ["tank"] + ["artillery"] + ["infantry"]*2
    defense_units = build_units_from_names(defense_unit_names)

    title_prefix = "2023-10-08 invade Morocco"

    main(attack_units, defense_units, title_prefix, combat.BATTLE_TYPE_AMPHIBIOUS)

def run_sim_02(unit_dict):
    attack_unit_names = ["destroyer"] + ["fighter"]*2 + ["cruiser"]*2 + ["bomber"]*2 + ["aircraft carrier"]
    attack_units = build_units_from_names(attack_unit_names)
    
    defense_unit_names = ["fighter"]*2 + ["battleship"]*2 + ["aircraft carrier"]
    defense_units = build_units_from_names(defense_unit_names)

    title_prefix = "2023-10-08 seazone"

    main(attack_units, defense_units, title_prefix, combat.BATTLE_TYPE_NAVAL)

def run_sim_03(unit_dict):
    attack_unit_names = ["infantry"]*9 + ["artillery"]*2 + ["tank"]
    attack_units = build_units_from_names(attack_unit_names)
    
    defense_unit_names = ["infantry"]*3 + ["artillery"]*1 + ["tank"]
    defense_units = build_units_from_names(defense_unit_names)

    title_prefix = "2023-10-09 west russia 01"

    main(attack_units, defense_units, title_prefix, combat.BATTLE_TYPE_LAND, do_write_fig=True, plot_data_for_round=[-1])

def run_sim_04(unit_dict):
    attack_unit_names = ["infantry"]*3 + ["artillery"]*1 + ["tank"]*3 + ["fighter"]*2
    attack_units = build_units_from_names(attack_unit_names)
    
    defense_unit_names = ["infantry"]*3 + ["artillery"]*1 + ["tank"] + ["bomber"] + ["fighter"]
    defense_units = build_units_from_names(defense_unit_names)

    title_prefix = "2023-10-09 Ukraine 01"

    main(attack_units, defense_units, title_prefix, combat.BATTLE_TYPE_LAND, do_write_fig=True, plot_data_for_round=[1, -1])

def build_units_from_names(unit_names):
    units = [unit_dict[x].copy() for x in unit_names]
    return units

def fig_ops(fig, do_show_fig, do_write_fig, output_filepath):
    if do_show_fig:
        fig.show()
    if do_write_fig:
        fig.write_html(output_filepath, include_plotlyjs="cdn")

def main(attack_units, defense_units, title_prefix, battle_type, N_sim=1000, max_plot_points=10000,
         plot_data_for_round=[-1], do_show_fig=True, do_write_fig=False
         ):
    output_path = os.path.join("output", title_prefix)
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.mkdir(output_path)

    logger.info("len(attack_units):  {}".format(len(attack_units)))
    sum_start_ipc_attack = sum([x.ipc for x in attack_units])
    logger.info("sum_start_ipc_attack:  {}".format(sum_start_ipc_attack))

    logger.info("len(defense_units):  {}".format(len(defense_units)))
    sum_start_ipc_defence = sum([x.ipc for x in defense_units])
    logger.info("sum_start_ipc_defense:  {}".format(sum_start_ipc_defence))

    all_results_list = []
    for i in range(N_sim):
        results_list = combat.run_combat(attack_units, defense_units, battle_type)
        all_results_list.append(results_list)

        _, result_attack_units, result_defense_units = results_list[-1]

        logger.debug("result_attack_units:  {}".format(result_attack_units))
        logger.debug("result_defense_units:  {}".format(result_defense_units))

        if i%100 == 0:
            logger.info("progress i:  {}".format(i))

    for cur_plot_round in plot_data_for_round:
        sum_remain_ipc_attack_list = []
        sum_remain_ipc_defense_list = []

        for results_list in all_results_list:
            _, result_attack_units, result_defense_units = results_list[cur_plot_round]

            remain_ipc_attack = [x.ipc for x in result_attack_units]
            remain_ipc_defense = [x.ipc for x in result_defense_units]
            sum_remain_ipc_attack = sum(remain_ipc_attack)
            sum_remain_ipc_defense = sum(remain_ipc_defense)
            logger.debug("sum_remain_ipc_attack:  {}".format(sum_remain_ipc_attack))
            logger.debug("sum_remain_ipc_defense:  {}".format(sum_remain_ipc_defense))

            sum_remain_ipc_attack_list.append(sum_remain_ipc_attack)
            sum_remain_ipc_defense_list.append(sum_remain_ipc_defense)

        sum_remain_ipc_attack_arr = numpy.array(sum_remain_ipc_attack_list)
        sum_remain_ipc_defense_arr = numpy.array(sum_remain_ipc_defense_list)
        diff_remain_ipc_arr = sum_remain_ipc_attack_arr - sum_remain_ipc_defense_arr

        sort_diff_remain_ipc_arr = numpy.array(diff_remain_ipc_arr)
        sort_diff_remain_ipc_arr.sort()

        plot_incr = 1
        if sort_diff_remain_ipc_arr.shape[0] > max_plot_points:
            plot_incr = int(numpy.round(sort_diff_remain_ipc_arr.shape[0] / max_plot_points))
        
        plot_sort_diff_remain_ipc_arr = sort_diff_remain_ipc_arr[::plot_incr]
        f = numpy.linspace(0., 1., num=plot_sort_diff_remain_ipc_arr.shape[0])
        title = "{} round {} ECDF of difference in remaining IPC attacker - defense".format(
            title_prefix, cur_plot_round)
        labels = {"x":"difference in remaining IPC", "y":"fraction of simulations"}
        fig = pltxpr.scatter(x=plot_sort_diff_remain_ipc_arr, y=f, title=title, labels=labels)
        output_filepath = os.path.join(output_path, "{}.html".format(title))
        fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

        title = "{} round {} Histogram of difference in remaining IPC attacker - defense".format(
            title_prefix, cur_plot_round)
        fig = pltxpr.histogram(x=plot_sort_diff_remain_ipc_arr, title=title, labels=labels)
        output_filepath = os.path.join(output_path, "{}.html".format(title))
        fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

        frac_winner_ipc = numpy.array(plot_sort_diff_remain_ipc_arr).astype(float)
        locs = plot_sort_diff_remain_ipc_arr > 0
        frac_winner_ipc[locs] = frac_winner_ipc[locs] / float(sum_start_ipc_attack)
        frac_winner_ipc[~locs] = frac_winner_ipc[~locs] / float(sum_start_ipc_defence)

        labels = {"x":"fractional difference in remaining IPC", "y":"fraction of simulations"}
        title = "{} round {} ECDF of difference in remaining fractional IPC attacker - defense".format(
            title_prefix, cur_plot_round)
        fig = pltxpr.scatter(x=frac_winner_ipc, y=f, title=title, labels=labels)
        output_filepath = os.path.join(output_path, "{}.html".format(title))
        fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

        title = "{} round {} Histogram of difference in remaining fractional IPC attacker - defense".format(
            title_prefix, cur_plot_round)
        fig = pltxpr.histogram(x=frac_winner_ipc, title=title, labels=labels)
        output_filepath = os.path.join(output_path, "{}.html".format(title))
        fig_ops(fig, do_show_fig, do_write_fig, output_filepath)


if __name__ == "__main__":
    setup_logger.setup(verbose=False)

    unit_dict = load_units()

    run_sim_04(unit_dict)