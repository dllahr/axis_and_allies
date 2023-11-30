import numpy
import pandas

import plotly.express as pltxpr

import logging

import axis_and_allies.combat as combat
import axis_and_allies.run_simulation as run_simulation
import axis_and_allies.setup_logger as setup_logger

logger = logging.getLogger(setup_logger.LOGGER_NAME)


def run_strategic_bombing(attack_bombers):
    cur_attacker_bombers = sorted(attack_bombers, key=lambda x: x.ipc)
    combat.calculate_temp_attacks(cur_attacker_bombers)

    air_defense_to_hit_list = [1]*len(cur_attacker_bombers)
    did_air_defense_hit_arr,_ = combat.calculate_rolls_and_compare(air_defense_to_hit_list)

    num_air_defense_hits = numpy.sum(did_air_defense_hit_arr*1)

    cur_attacker_bombers = cur_attacker_bombers[num_air_defense_hits:]

    bomber_damage = numpy.random.randint(1, 7, len(cur_attacker_bombers))

    return cur_attacker_bombers, bomber_damage

def simulate_strategic_bombing(unit_dict, max_bomber_damage=20):
    N_bombers = numpy.power(2, range(4), dtype=int)
    N_sim = 1000

    bomber_unit = unit_dict["bomber"]

    data_dict = {"N_bomber_start":[], "N_bomber_after":[], "bomber_damage":[]}
    for cur_n_bomber in N_bombers:
        logger.info("cur_n_bomber:  {}".format(cur_n_bomber))

        attack_bombers = [bomber_unit.copy() for i in range(cur_n_bomber)]

        for i in range(N_sim):
            cur_attack_bombers, bomber_damage = run_strategic_bombing(attack_bombers)
            data_dict["N_bomber_start"].append(cur_n_bomber)
            data_dict["N_bomber_after"].append(len(cur_attack_bombers))
            data_dict["bomber_damage"].append(numpy.sum(bomber_damage))

    data_df = pandas.DataFrame(data_dict)
    data_df["N_bombers_lost"] = data_df.N_bomber_start - data_df.N_bomber_after
    data_df["bomber_IPC_lost"] = bomber_unit.ipc * data_df.N_bombers_lost

    data_df["net_IPC"] = data_df.bomber_damage - data_df.bomber_IPC_lost

    data_df["clipped_bomber_damage"] = data_df.bomber_damage
    locs = data_df.clipped_bomber_damage > max_bomber_damage
    data_df.loc[locs, "clipped_bomber_damage"] = max_bomber_damage

    data_df["clipped_net_IPC"] = data_df.clipped_bomber_damage - data_df.bomber_IPC_lost

    data_df["pct_rnk_net_IPC"] = numpy.nan
    data_df["pct_rnk_clipped_net_IPC"] = numpy.nan
    for cur_n_bomber in N_bombers:
        locs = data_df.N_bomber_start == cur_n_bomber
        data_df.loc[locs, "pct_rnk_net_IPC"] = data_df.loc[locs, "net_IPC"].rank(pct=True, method="first")
        data_df.loc[locs, "pct_rnk_clipped_net_IPC"] = data_df.loc[locs, "clipped_net_IPC"].rank(pct=True, method="first")

    data_df["N_bomber_start_str"] = data_df.N_bomber_start.astype(str)

    logger.info("data_df:\n{}".format(data_df))

    fig = pltxpr.scatter(data_df, x="net_IPC", y="pct_rnk_net_IPC", color="N_bomber_start_str")
    fig.show()

    fig = pltxpr.scatter(data_df, x="clipped_net_IPC", y="pct_rnk_clipped_net_IPC", color="N_bomber_start_str")
    fig.show()
    

if __name__ == "__main__":
    setup_logger.setup(verbose=False)

    unit_dict = run_simulation.load_units()

    simulate_strategic_bombing(unit_dict)