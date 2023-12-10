import time

import numpy
import pandas

import stable_baselines3
import gymnasium as gym

import axis_and_allies.run_simulation as run_simulation
import axis_and_allies.reinforcement_learning.super_simple_env as super_simple_env

output_template = "env_data_r{}x{}.txt"
output_eval_template = "evaluate_model_r{}x{}.txt"

IPC_limit = 30
ipc_cost_arr = numpy.array([3,4,6,10,12])

unit_dict = run_simulation.load_units("../unit_data.json")

def evaluate_model(N=200):
    default_obs = env.build_default_obseration()[0]

    action_list = [model.predict(default_obs)[0] for i in range(N)]
    result_list = [env.step(action)[1] for action in action_list]

    eval_df = pandas.DataFrame({"action":[x[0] for x in action_list], "result":result_list})
    return eval_df


env = super_simple_env.SuperSimpleEnv(IPC_limit, ipc_cost_arr, unit_dict)
print(env)

model = stable_baselines3.PPO(stable_baselines3.ppo.MlpPolicy, env, verbose=0, n_steps=4096*8) # , n_steps=2
env.model = model

print("predictions from untrained model")
untrained_eval_df = evaluate_model()
untrained_eval_df["model_state"] = "untrained"

print("start learning!")

start_time = time.time()
model.learn(total_timesteps=1)
end_time = time.time()
duration = end_time - start_time
duration_min = duration / 60.
print("duraton:  {}  duration_min:  {}".format(duration, duration_min))

a = numpy.vstack(env.all_actions)
# a.shape
a_df = pandas.DataFrame(a, columns=["action_{}".format(i) for i in range(a.shape[1])])
# a_df
b_df = pandas.DataFrame(
    numpy.vstack(env.all_opponent_actions),
    columns=["opp_action_{}".format(i) for i in range(len(env.all_opponent_actions[0]))]
)
# b_df
data_df = pandas.concat([a_df, b_df], axis=1)
data_df["result"] = env.all_results
data_df.index.name = "training_cycle"
print(data_df)

output_file = output_template.format(data_df.shape[0], data_df.shape[1])
print(output_file)
data_df.to_csv(output_file, sep="\t")

print("generate predictions trained model")
trained_eval_df = evaluate_model()
trained_eval_df["model_state"] = "trained"

eval_df = pandas.concat([untrained_eval_df, trained_eval_df], axis=0)
output_file = output_eval_template.format(eval_df.shape[0], eval_df.shape[1])
eval_df.to_csv(output_file, sep="\t")