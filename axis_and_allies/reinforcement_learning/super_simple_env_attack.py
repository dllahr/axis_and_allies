import numpy

import axis_and_allies.reinforcement_learning.super_simple_env as super_simple_env

import axis_and_allies.run_simulation as run_simulation
import axis_and_allies.combat as combat


class SuperSimpleEnvAttack(super_simple_env.SuperSimpleEnv):
    def __init__(self, IPC_limit, ipc_cost_arr, render_mode="console", log_ratio_limit=5,
                 defense_model=None, defense_env=None, ipc_frac_limits=(0., 1.)
                 ):
        super().__init__(IPC_limit, ipc_cost_arr, render_mode, log_ratio_limit, ipc_frac_limits=ipc_frac_limits)

        self.defense_model = defense_model
        self.defense_env = defense_env

    def step(self, action):
        # print("taking a step attack")
        # import pdb; pdb.set_trace()

        self.current_action = action
        self.all_actions.append(action)

        self.unit_counts = super_simple_env.convert_action_integers(action, self.IPC_limit, self.ipc_cost_arr)

        self.defense_env.opponent_unit_counts = self.unit_counts

        self.defense_model.learn(total_timesteps=1)

        # Optionally we can pass additional info, we are not using that for now
        info = {}

        self.result = self.defense_env.result_metrics.fraction_ipc_winner # reward

        self.all_results.append(self.result)

        return (
            numpy.array([self.result]).astype(numpy.float32),  # does this need to conform to obseration space?
            self.result, # reward
            True, # terminated
            False, # truncated
            info,
        )