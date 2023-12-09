import logging

import os
import shutil
import collections

import numpy
import pandas
import plotly.express as pltxpr

import axis_and_allies.combat as combat
import axis_and_allies.unit as unit
import axis_and_allies.setup_logger as setup_logger

logger = logging.getLogger(setup_logger.LOGGER_NAME)


CombatResultMetric = collections.namedtuple("CombatResultMetric", 
    ["attack_ipc", "defense_ipc", "diff_ipc", "fraction_ipc_winner"]
)

def load_units(input_file="unit_data.json"):
    with open(input_file) as file:
        json_str = file.read().strip()
    my_unit_dict = unit.load_from_json(json_str)
    
    return my_unit_dict


def run_single_from_names(unit_dict, attack_unit_names, defense_unit_names, battle_type):
    # import pdb; pdb.set_trace()
    attack_units = build_units_from_names(unit_dict, attack_unit_names)
    defense_units = build_units_from_names(unit_dict, defense_unit_names)

    combat_result = combat.run_combat(attack_units, defense_units, battle_type)

    return combat_result


def run_sim_land_game(unit_dict):
    attack_unit_names = ["infantry"]*25 + ["artillery"]*4 + ["tank"]*0 + ["fighter"]*7 + ["bomber"]*0 #+ ["cruiser"]*1 + ["battleship"]

    defense_unit_names = ["infantry"]*9 + ["artillery"]*6 + ["anti-aircraft artillery"]*0 + ["tank"]*1 + ["fighter"]*4 #+ ["bomber"]*3
    
    run_sim_land(unit_dict, attack_unit_names, defense_unit_names)
    

def run_sim_land(unit_dict, attack_unit_names, defense_unit_names, N_sim=1000, title_prefix=""):
    attack_units = build_units_from_names(unit_dict, attack_unit_names)
    defense_units = build_units_from_names(unit_dict, defense_unit_names)
    main(
        attack_units, defense_units, title_prefix, combat.BATTLE_TYPE_LAND, do_write_fig=False, plot_data_for_round=[-1],
        N_sim=N_sim
    )


def run_sim_naval(unit_dict):
    title_prefix = "nevermind"

    attack_unit_names = (
        ["submarine"]*1 + ["destroyer"]*0 + ["fighter"]*7 #+ ["aircraft carrier"]*2 + ["cruiser"] + ["battleship"]*1 + ["bomber"]*1
        
    )
    attack_units = build_units_from_names(unit_dict, attack_unit_names)
    
    defense_unit_names = (
        ["submarine"]*1 + ["destroyer"]*1 + ["fighter"]*4 + ["aircraft carrier"]*2 + ["cruiser"]*2 + ["battleship"]*1  #
    )

    defense_units = build_units_from_names(unit_dict, defense_unit_names)

    main(
        attack_units, defense_units, title_prefix, combat.BATTLE_TYPE_NAVAL, do_write_fig=False, plot_data_for_round=[-1],
        # N_sim=1
    )

def build_units_from_names(unit_dict, unit_names):
    units = [unit_dict[x].copy() for x in unit_names]
    return units

def calculate_sum_ipc(unit_list):
    ipc_list = [x.ipc for x in unit_list]
    return sum(ipc_list)

def calculate_metrics_from_combat_result(combat_result, sum_start_ipc_attack, sum_start_ipc_defense):
    # import pdb; pdb.set_trace()
    _, result_attack_units, result_defense_units = combat_result

    # remain_ipc_attack = [x.ipc for x in result_attack_units]
    # remain_ipc_defense = [x.ipc for x in result_defense_units]

    sum_remain_ipc_attack = calculate_sum_ipc(result_attack_units)
    sum_remain_ipc_defense = calculate_sum_ipc(result_defense_units)
    
    logger.debug("sum_remain_ipc_attack:  {}".format(sum_remain_ipc_attack))
    logger.debug("sum_remain_ipc_defense:  {}".format(sum_remain_ipc_defense))

    diff_ipc = sum_remain_ipc_attack - sum_remain_ipc_defense

    frac_winner_ipc = numpy.nan
    if diff_ipc > 0:
        frac_winner_ipc = diff_ipc / sum_start_ipc_attack
    elif diff_ipc < 0:
        frac_winner_ipc = diff_ipc / sum_start_ipc_defense
    else:
        frac_winner_ipc = 0.
    
    return CombatResultMetric(
        attack_ipc=sum_remain_ipc_attack, defense_ipc=sum_remain_ipc_defense,
        diff_ipc=diff_ipc, fraction_ipc_winner=frac_winner_ipc
    )

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
    sum_start_ipc_attack = calculate_sum_ipc(attack_units)
    logger.info("sum_start_ipc_attack:  {}".format(sum_start_ipc_attack))

    logger.info("len(defense_units):  {}".format(len(defense_units)))
    sum_start_ipc_defence = calculate_sum_ipc(defense_units)
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

    diff_remain_ipc_arr_list = []
    for cur_plot_round in plot_data_for_round:
        combat_result_metric_list = [
            calculate_metrics_from_combat_result(
                x[cur_plot_round], sum_start_ipc_attack, sum_start_ipc_defence
            ) for x in all_results_list
        ]

        sort_diff_remain_ipc_arr = sorted(combat_result_metric_list, key=lambda x: x.diff_ipc)

        if do_show_fig or do_write_fig:
            plot_incr = 1
            if len(sort_diff_remain_ipc_arr) > max_plot_points:
                plot_incr = int(numpy.round(sort_diff_remain_ipc_arr.shape[0] / max_plot_points))
            
            plot_sort_diff_remain_ipc_arr = [
                x.diff_ipc for x in sort_diff_remain_ipc_arr[::plot_incr]
            ]
            f = numpy.linspace(0., 1., num=len(plot_sort_diff_remain_ipc_arr))
            title = "{} round {} ECDF of difference in remaining IPC attacker - defense".format(
                title_prefix, cur_plot_round)
            labels = {"x":"difference in remaining IPC", "y":"fraction of simulations"}
            fig = pltxpr.scatter(x=plot_sort_diff_remain_ipc_arr, y=f, title=title, labels=labels)
            output_filepath = os.path.join(output_path, "{}.html".format(title))
            fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

            # title = "{} round {} Histogram of difference in remaining IPC attacker - defense".format(
            #     title_prefix, cur_plot_round)
            # fig = pltxpr.histogram(x=plot_sort_diff_remain_ipc_arr, title=title, labels=labels)
            # output_filepath = os.path.join(output_path, "{}.html".format(title))
            # fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

            # labels = {"x":"fractional difference in remaining IPC", "y":"fraction of simulations"}
            # title = "{} round {} ECDF of difference in remaining fractional IPC attacker - defense".format(
            #     title_prefix, cur_plot_round)
            # fig = pltxpr.scatter(x=frac_winner_ipc, y=f, title=title, labels=labels)
            # output_filepath = os.path.join(output_path, "{}.html".format(title))
            # fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

            # title = "{} round {} Histogram of difference in remaining fractional IPC attacker - defense".format(
            #     title_prefix, cur_plot_round)
            # fig = pltxpr.histogram(x=frac_winner_ipc, title=title, labels=labels)
            # output_filepath = os.path.join(output_path, "{}.html".format(title))
            # fig_ops(fig, do_show_fig, do_write_fig, output_filepath)

    return diff_remain_ipc_arr_list

def collect_data_for_modeling(unit_dict):
    N_sim_per_config = 3
    N_config_per_IPC = lambda IPC: 1
    IPC_min = 10
    IPC_max = 100

    # for land battles
    possible_units = [x for x in unit_dict.values() if x.unit_type == unit.UNIT_TYPE_AIR or x.unit_type == unit.UNIT_TYPE_LAND]
    possible_units = sorted(possible_units, key=lambda x: (x.unit_type, x.ipc))

    all_results = []
    for IPC in range(IPC_min, IPC_max+1):
        N_config = N_config_per_IPC(IPC)

        for i in range(N_config):
            attack_units, attack_units_counts, attack_IPC = build_random_force(IPC, possible_units)
            defense_units, defense_units_counts, defense_IPC = build_random_force(IPC, possible_units)

            diff_remain_IPC_arr = main(
                attack_units, defense_units, "NA", combat.BATTLE_TYPE_AMPHIBIOUS, do_write_fig=False, 
                plot_data_for_round=[-1], do_show_fig=False, N_sim=N_sim_per_config
            )[0]

            all_results.append(
                (IPC, attack_units_counts, defense_units_counts, attack_IPC, defense_IPC, diff_remain_IPC_arr)
            )

    data_dict = {"IPC":[], "attack_IPC":[], "defense_IPC":[], "diff_remain_IPC":[]}
    data_dict.update({x.name+"_attack":[] for x in possible_units})
    data_dict.update({x.name+"_defense":[] for x in possible_units})

    for IPC, attack_units_counts, defense_units_counts, attack_IPC, defense_IPC, diff_remain_IPC_arr in all_results:
        N_diff_remain_IPC_arr = len(diff_remain_IPC_arr)
        assert N_diff_remain_IPC_arr == N_sim_per_config

        data_dict["IPC"].extend([IPC]*N_diff_remain_IPC_arr)
        data_dict["attack_IPC"].extend([attack_IPC]*N_diff_remain_IPC_arr)
        data_dict["defense_IPC"].extend([defense_IPC]*N_diff_remain_IPC_arr)

        for i, cur_unit in enumerate(possible_units):
            data_dict[cur_unit.name+"_attack"].extend([attack_units_counts[i]]*N_diff_remain_IPC_arr)
            data_dict[cur_unit.name+"_defense"].extend([defense_units_counts[i]]*N_diff_remain_IPC_arr)
        
        data_dict["diff_remain_IPC"].extend(diff_remain_IPC_arr)
    
    data_df = pandas.DataFrame(data_dict)
    data_df["attack_frac_spend"] = data_df.attack_IPC / data_df.IPC
    data_df["defense_frac_spend"] = data_df.defense_IPC / data_df.IPC
    locs = data_df.diff_remain_IPC >= 0
    data_df["frac_diff_remain_IPC"] = float("nan")
    data_df.loc[locs, "frac_diff_remain_IPC"] = data_df.diff_remain_IPC / data_df.attack_IPC
    data_df.loc[~locs, "frac_diff_remain_IPC"] = data_df.diff_remain_IPC / data_df.defense_IPC

    print(data_df.head())
    output_file = "sim_data_r{}x{}.txt".format(data_df.shape[0], data_df.shape[1])
    data_df.to_csv(output_file, sep="\t")


def build_random_force(IPC_limit, possible_units):
    cur_IPC = 0
    random_force_counts = numpy.zeros(len(possible_units), dtype=numpy.uint)
    random_force = []
    while cur_IPC <= IPC_limit:
        cur_index = numpy.random.randint(0, len(possible_units))
        random_force_counts[cur_index] += 1

        cur_unit = possible_units[cur_index]
        cur_IPC += cur_unit.ipc
        random_force.append(cur_unit.copy())
    
    if cur_IPC > IPC_limit:
        random_force = random_force[:-1]
        random_force_counts[cur_index] -= 1

    sum_random_force_ipc = sum([x.ipc for x in random_force])
    logger.debug("sum_random_force_ipc:  {}".format(sum_random_force_ipc))

    assert sum_random_force_ipc <= IPC_limit, (sum_random_force_ipc, IPC_limit)

    return random_force, random_force_counts, sum_random_force_ipc


if __name__ == "__main__":
    setup_logger.setup(verbose=False)

    unit_dict = load_units()

    run_sim_naval(unit_dict)
    # run_sim_land_game(unit_dict)

    # collect_data_for_modeling(unit_dict)