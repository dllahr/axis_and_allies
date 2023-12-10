import sys

import numpy
import pandas

import plotly.express as pltxpr

input_file = sys.argv[1]
input_eval_file = sys.argv[2]

eval_df = pandas.read_csv(input_eval_file, sep="\t", index_col=0)
for col in ["action", "result"]:
    new_col = "pct_rnk_"+col
    eval_df[new_col] = numpy.nan
    for model_state in eval_df.model_state.unique():
        locs = eval_df.model_state == model_state
        eval_df.loc[locs, new_col] = eval_df.loc[locs, col].rank(pct=True, method="first")
print(eval_df)

data_df = pandas.read_csv(input_file, sep="\t")

data_df["pct_rnk_result"] = data_df["result"].rank(pct=True, method="first")

block_incr = data_df.shape[0] / 10.
data_df["training_cycle_block"] = [int(x/block_incr) for x in data_df.training_cycle]
print(data_df)

# fig = pltxpr.scatter(
#     data_df, x="result", y="pct_rnk_result",
#     title="ECDF results N={}".format(data_df.shape[0])
# )
# fig.show()

# fig = pltxpr.scatter(
#     data_df, x="training_cycle", y="result",
#     # opacity=0.2,
#     title="result vs training_cycle"
# )
# fig.show()

# fig = pltxpr.box(
#     data_df, x="training_cycle_block", y="result", points="all",
#     title="result vs training_cycle_block"
# )
# fig.show()

# fig = pltxpr.scatter(
#     data_df, x="training_cycle", y="action_0",
#     title="action_0 vs training_cycle"
# )
# fig.show()

# fig = pltxpr.box(
#     data_df, x="training_cycle_block", y="action_0", points="all",
#     title="action_0 vs training_cycle_block"
# )
# fig.show()

# fig = pltxpr.scatter(
#     data_df, x="training_cycle", y="opp_action_0",
#     title="opp_action_0 vs training_cycle"
# )
# fig.show()

# fig = pltxpr.box(
#     data_df, x="training_cycle_block", y="opp_action_0", points="all",
#     title="opp_action_0 vs training_cycle_block"
# )
# fig.show()

fig = pltxpr.box(eval_df, x="model_state", y="action", points="all")
fig.show()

fig = pltxpr.box(eval_df, x="model_state", y="result", points="all")
fig.show()

fig = pltxpr.scatter(eval_df, x="action", y="pct_rnk_action", color="model_state")
fig.show()

fig = pltxpr.scatter(eval_df, x="result", y="pct_rnk_result", color="model_state")
fig.show()