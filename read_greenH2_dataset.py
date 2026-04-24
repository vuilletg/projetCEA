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
        z=data_z[tech["id"], year_id, :, 17, 11, 0],
        name=tech["name"],
        mode='markers',
        marker=dict(color=tech["color"], size=3)
    ))
    
def creer_bouton(nom_colonne, axe_vise):
    nouveaux_points = []
    donnees_completes = get_data(nom_colonne)
    
    for i in range(Ntechno):
        if axe_vise == 2:
            points = donnees_completes[i, year_id, :, 17, 11, 0]
        else:
            points = donnees_completes[i, year_id, :, 0, 0, 0]
        nouveaux_points.append(points)

    nom_axe_plotly = ['xaxis', 'yaxis', 'zaxis'][axe_vise]
    lettre_axe = ['x', 'y', 'z'][axe_vise]

    return dict(
        label=nom_colonne,
        method="update",
        args=[
            {lettre_axe: nouveaux_points}, 
            {f"scene.{nom_axe_plotly}.title.text": nom_colonne} 
        ]
    )

menus_deroulants = []
for i, label in enumerate(["X", "Y", "Z"]):
    menus_deroulants.append(dict(
        buttons=[creer_bouton(col, i) for col in param_dispo],
        direction="down",
        showactive=True,
        x=0.1 + (i * 0.2),
        y=1.1
    ))

fig.update_layout(
    updatemenus=menus_deroulants,
    margin=dict(t=100),
    scene=dict(
        xaxis_title=param_dispo[0],
        yaxis_title=param_dispo[1],
        zaxis_title=param_dispo[2]
    )
)

plot(fig)
