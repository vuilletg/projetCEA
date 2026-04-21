import pandas as pd
import plotly.graph_objects as go
from plotly.offline import plot

df = pd.read_csv("MCfulldata_ntechno3_N100_pandas_L3251210.csv")

Ntechno = 3
Nyear = 3
Nsample = 100
usage_grid = [31, 31, 5]
param_dispo = df.columns[2:]
year_dispo = df["Year"].unique()
techno_dispo = df["Technology"].unique()

name_x = param_dispo[0]
name_y = param_dispo[1]
name_z = param_dispo[2]
col = ["blue", "red", "green", "cyan", "magenta", "yellow", "black", "orange", "purple"]
print (param_dispo)
year_id = 0 

tech_configs = [
    {"name": tech +"_" + str(year_dispo[year_id]), "id": i, "color": col[i]} for i, tech in enumerate(techno_dispo)
]

def get_data(column_name):
    return df[column_name].values.reshape(Ntechno, Nyear, Nsample, usage_grid[0], usage_grid[1], usage_grid[2])

data_x = get_data(name_x)
data_y = get_data(name_y)
data_z = get_data(name_z)

fig = go.Figure()

for tech in tech_configs:
    fig.add_trace(go.Scatter3d(
        x=data_x[tech["id"], year_id, :, 0, 0, 0],
        y=data_y[tech["id"], year_id, :, 0, 0, 0],
        z=data_z[tech["id"], year_id, :, 17,11,0],
        name=tech["name"],
        mode='markers',
        marker=dict(color=tech["color"], size=3)
    ))

fig.update_layout(
    height=1000, 
    width=1000,
    scene=dict(
        xaxis_title=name_x,
        yaxis_title=name_y,
        zaxis_title=name_z
    )
)
plot(fig, auto_open=True)
