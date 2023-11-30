import pandas
import numpy

import sklearn.neural_network as neural_network


input_file = "sim_data_r273x19.txt"


data_df = pandas.read_csv(input_file, sep="\t", index_col=0)

data_df["z_IPC"] = (data_df.IPC - data_df.IPC.mean()) / data_df.IPC.std()

print(data_df)
print(data_df.columns)

X_cols = [x for x in data_df.columns if x.endswith("_defense")]
X_cols.extend(["z_IPC"])
print(X_cols)


