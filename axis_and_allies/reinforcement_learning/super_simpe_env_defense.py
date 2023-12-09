import numpy

import axis_and_allies.reinforcement_learning.super_simple_env as super_simple_env

import axis_and_allies.run_simulation as run_simulation
import axis_and_allies.combat as combat


class SuperSimpleEnvDefense(super_simple_env.SuperSimpleEnv):
    def __init__(self, IPC_limit, ipc_cost_arr, render_mode="console", log_ratio_limit=5, unit_dict=None,
                 ipc_frac_limits=(0., 1.)
    ):
        super().__init__(IPC_limit, ipc_cost_arr, render_mode, log_ratio_limit, ipc_frac_limits=ipc_frac_limits)

        self.opponent_unit_counts = None
        self.unit_dict = unit_dict

        self.combat_result = None
        self.result_metrics = None
    
    def step(self, action):
        # print("taking a step defense")
        # import pdb; pdb.set_trace()
        self.current_action = action
        self.all_actions.append(action)

        self.unit_counts = super_simple_env.convert_action_integers(action, self.IPC_limit, self.ipc_cost_arr)

        defense_unit_names = super_simple_env.convert_unit_count_to_unit_name_list(self.unit_counts)
        attack_unit_names = super_simple_env.convert_unit_count_to_unit_name_list(self.opponent_unit_counts)

        self.combat_result = run_simulation.run_single_from_names(
            self.unit_dict, attack_unit_names, defense_unit_names, combat.BATTLE_TYPE_LAND
        )

        sum_start_ipc_attack = run_simulation.calculate_sum_ipc(
            run_simulation.build_units_from_names(self.unit_dict, attack_unit_names)
        )
        sum_start_ipc_defense = run_simulation.calculate_sum_ipc(
            run_simulation.build_units_from_names(self.unit_dict, defense_unit_names)
        )
        self.result_metrics = run_simulation.calculate_metrics_from_combat_result(
            self.combat_result[-1], sum_start_ipc_attack, sum_start_ipc_defense
        )
        # -1 indicates ultimate result / from last round of combat

        #     # Optionally we can pass additional info, we are not using that for now
        info = {}

        self.result = self.result_metrics.fraction_ipc_winner # reward
        # print("defense self.result:  {}".format(self.result))

        self.all_results.append(self.result)

        # if numpy.isnan(self.result):
        #     print("result is nan")
        #     print("result_metrics:  {}".format(self.result_metrics))

        progress = len(self.all_results)
        if  progress % 100 == 0:
            print("progress:  {}".format(progress))
            
        return (
            numpy.array([self.result]).astype(numpy.float32), # this normally returns the agent position we don't have
            # an equivalent b/c this is "one and done"
            self.result, # reward
            True, # terminated
            False, # truncated
            info,
        )

