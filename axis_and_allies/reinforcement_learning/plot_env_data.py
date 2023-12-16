import sys

import numpy
import pandas

import plotly.express as pltxpr

# input_file = sys.argv[1]
input_eval_file = sys.argv[1]

eval_df = pandas.read_csv(input_eval_file, sep="\t", index_col=0)
plot_cols = eval_df.columns.to_list()
plot_cols.remove("model_state")
for col in plot_cols:
    new_col = "pct_rnk_"+col
    eval_df[new_col] = numpy.nan
    for model_state in eval_df.model_state.unique():
        locs = eval_df.model_state == model_state
        eval_df.loc[locs, new_col] = eval_df.loc[locs, col].rank(pct=True, method="first")
print(eval_df)


for col in plot_cols:
    title = "{} box plot comparing trained untrained".format(col)
    fig = pltxpr.box(eval_df, x="model_state", y=col, points="all", title=title)
    fig.show()
    fig.write_html("results/v0.02/{}.html".format(title), include_plotlyjs="cdn")

    title = "{} ECDF comparing trained untrained".format(col)
    fig = pltxpr.scatter(eval_df, x=col, y="pct_rnk_{}".format(col), color="model_state", title=title)
    fig.show()
    fig.write_html("results/v0.02/{}.html".format(title), include_plotlyjs="cdn")
