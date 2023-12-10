import numpy
import gymnasium as gym

import logging
import axis_and_allies.setup_logger as setup_logger

import axis_and_allies.run_simulation as run_simulation
import axis_and_allies.combat as combat


logger = logging.getLogger(setup_logger.LOGGER_NAME)

# indexes into action space
ACTION_FRACTION_SPEND = 0
ACTION_RATIO_ART = 1  # ratio of artillery to infantry in purchase etc.
ACTION_RATIO_TANK = 2
ACTION_RATIO_FIGHTER = 3
ACTION_RATIO_BOMBER = 4

UNIT_NAMES_REFERENCE = ["infantry", "artillery", "tank", "fighter", "bomber"]


class Opponent:
    def __init__(self, model=None, env=None, unit_counts=None) -> None:
        self.model = model
        self.env = env
        self.unit_counts = unit_counts


class SuperSimpleEnv(gym.Env):
    """
    Custom Environment that follows gym interface.
    This is a super simple environment for purchasing units in Axis and Allies that will then immediately
    be used in a battle
    """

    # Because of google colab, we cannot implement the GUI ('human' render mode)
    metadata = {"render_modes": ["console"]}

    DEFAULT_ACTION = [1.] + [0.]*4

    def __init__(self, IPC_limit, ipc_cost_arr, unit_dict, render_mode="console", log_ratio_limit=5, ipc_frac_limits=(0., 1.)):
        super(SuperSimpleEnv, self).__init__()
        self.render_mode = render_mode

        self.IPC_limit = IPC_limit
        self.ipc_cost_arr = ipc_cost_arr
        self.unit_dict = unit_dict

        log_ratio_limit = float(log_ratio_limit)
        self.log_ratio_limit = log_ratio_limit

        self.unit_counts = None
        self.current_action = numpy.array(SuperSimpleEnv.DEFAULT_ACTION)

        self.result = 0.

        self.all_results = []
        self.all_actions = []
        self.all_opponent_actions = []

        self.model = None
        
        # the action indexes are described above specifically but overall
        # it is the fraction of total IPC to spend, and then the log2(ratio) of the units to purchase with respect to the 
        # number of infantry to purchase
        # these values will then be converted into conrete integer numbers of units to be purchased subject to the IPC
        # constraint
        self.action_space = gym.spaces.Box(
            low=numpy.array([ipc_frac_limits[0]] + [-log_ratio_limit]*4),
            high=numpy.array([ipc_frac_limits[1]] + [log_ratio_limit]*4)
        )

        # The observation will be the fraction of IPC remaining after the battle
        # where positive indicates a win, negative indicates a loss
        self.observation_space = gym.spaces.Box(
            low=0, high=45, shape=(1,), dtype=numpy.int32
        )

    def build_default_obseration(self):
        return numpy.array([self.IPC_limit]).astype(numpy.float32), {}  # empty info dict

    def reset(self, seed=None, options=None):
        """
        Important: the observation must be a numpy array
        :return: (np.array)
        """
        super().reset(seed=seed, options=options)
        
        self.current_action = numpy.array(SuperSimpleEnv.DEFAULT_ACTION, dtype=numpy.float32)

        return self.build_default_obseration()

    def step(self, action):
        self.current_action = action
        self.all_actions.append(action)

        self.unit_counts = convert_action_to_integers(action, self.IPC_limit, self.ipc_cost_arr)
        unit_names = convert_unit_count_to_unit_name_list(self.unit_counts)

        opponent_action = self.model.predict(self.build_default_obseration()[0])[0]
        # print("opponent_action:  {}".format(opponent_action))
        self.all_opponent_actions.append(opponent_action)

        opponent_unit_counts = convert_action_to_integers(opponent_action, self.IPC_limit, self.ipc_cost_arr)
        opponent_unit_names = convert_unit_count_to_unit_name_list(opponent_unit_counts)
        
        self.combat_result = run_simulation.run_single_from_names(
            self.unit_dict, unit_names, opponent_unit_names, combat.BATTLE_TYPE_LAND
        )

        sum_start_ipc_attack = run_simulation.calculate_sum_ipc(
            run_simulation.build_units_from_names(self.unit_dict, unit_names)
        )
        sum_start_ipc_defense = run_simulation.calculate_sum_ipc(
            run_simulation.build_units_from_names(self.unit_dict, opponent_unit_names)
        )
        self.result_metrics = run_simulation.calculate_metrics_from_combat_result(
            self.combat_result[-1], sum_start_ipc_attack, sum_start_ipc_defense
        )
        # -1 indicates result from last round of combat

        # Optionally we can pass additional info, we are not using that for now
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
            self.build_default_obseration()[0], # this normally returns the agent position we don't have
            # an equivalent b/c this is "one and done"
            self.result, # reward
            True, # terminated
            False, # truncated
            info,
        )


    def render(self):
        if self.render_mode == "console":
            logger.info("self:  {}".format(self))

            logger.info("self.current_action:  {}".format(self.current_action))
            IPC_spend = numpy.round(self.current_action[ACTION_FRACTION_SPEND] * self.IPC_limit)
            logger.info("IPC_spend:  {}".format(IPC_spend))

            unit_counts = convert_action_to_integers(self.current_action, self.IPC_limit, self.ipc_cost_arr)
            logger.info("unit_counts:  {}".format(unit_counts))

    def close(self):
        pass

    def __str__(self):
        r = """IPC_limit:  {}
log_ratio_limit:  {}
action_space:  {}
observation_space:  {}
current_action:  {}
""".format(self.IPC_limit, self.log_ratio_limit, self.action_space, self.observation_space, self.current_action)
        return r
    
    def __repr__(self):
        return self.__str__()


def calculate_unit_ratios_and_cost_array(log_ratio_arr, ipc_cost_arr):
    unit_ratios = numpy.power(2., log_ratio_arr)
    logger.debug("unit_ratios:  {}".format(unit_ratios))

    cost_arr = numpy.array(
        [ipc_cost_arr[0]] + list(
            unit_ratios * ipc_cost_arr[1:]
        )
    )

    return unit_ratios, cost_arr


def check_cost_and_adjust_units(initial_unit_count, ipc_cost_arr, IPC_spend):
    unit_count = numpy.array(initial_unit_count)
    check_cost = numpy.sum(unit_count * ipc_cost_arr)
    logger.debug("initial check_cost:  {}".format(check_cost))

    while check_cost > IPC_spend:
        excess_cost = check_cost - IPC_spend
        logger.debug("excess_cost:  {}".format(excess_cost))

        unit_vs_excess_cost = ipc_cost_arr - excess_cost
        unit_vs_excess_cost[unit_count == 0] = numpy.nan
        logger.debug("unit_vs_excess_cost:  {}".format(unit_vs_excess_cost))

        unit_to_remove_index = numpy.nanargmin(numpy.absolute(unit_vs_excess_cost))
        logger.debug("unit_to_remove_index:  {}".format(unit_to_remove_index))

        unit_count[unit_to_remove_index] -= 1
        logger.debug("updated unit_count:  {}".format(unit_count))

        check_cost = numpy.sum(unit_count * ipc_cost_arr)
        logger.debug("check_cost:  {}".format(check_cost))

    return unit_count.astype(int)


def convert_action_to_integers(action, IPC_limit, ipc_cost_arr):
    # fraction_IPC_spend = 1.0 - action[ACTION_FRACTION_SPEND]
    # IPC_spend = numpy.round(IPC_limit * fraction_IPC_spend) + 0.1
    IPC_spend = numpy.round(IPC_limit * action[ACTION_FRACTION_SPEND]) + 0.1
    # add this small offset to make subsequent rounding / dividing math work

    unit_ratios, cost_arr = calculate_unit_ratios_and_cost_array(action[1:], ipc_cost_arr)

    sum_cost = numpy.sum(cost_arr)
    logger.debug("sum_cost:  {}".format(sum_cost))

    buy_ratio = IPC_spend / sum_cost
    logger.debug("buy_ratio:  {}".format(buy_ratio))

    buy_count = int(numpy.round(buy_ratio))
    buy_count = buy_count if buy_count >= 1 else 1
    logger.debug("buy_count:  {}".format(buy_count))

    raw_unit_count = numpy.array(
        [buy_count] + list((unit_ratios * buy_count))
    )
    logger.debug("raw_unit_count:  {}".format(raw_unit_count))

    initial_unit_count = numpy.round(raw_unit_count).astype(int)
    logger.debug("initial_unit_count:  {}".format(initial_unit_count))

    unit_count = check_cost_and_adjust_units(initial_unit_count, ipc_cost_arr, IPC_spend)

    return unit_count


def convert_unit_count_to_unit_name_list(unit_count):
    unit_name_list = []

    for i, unit_name in enumerate(UNIT_NAMES_REFERENCE):
        unit_name_list += [unit_name]*unit_count[i]

    return unit_name_list