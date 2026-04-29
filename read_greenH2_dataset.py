from asyncio.windows_events import NULL

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

df = pd.read_csv("MCfulldata_ntechno3_N100_pandas_L3251210.csv")

nb_param_tech = 3
nb_param_context = 3
nb_criteria = 2
Nsample = 100
usage_grid = [31, 31, 5]
endpoint_tech = 2 + nb_param_tech
param_dispo = df.columns[2:endpoint_tech]
startpoint_context = endpoint_tech
endpoint_context = startpoint_context + nb_param_context
contexte_dispo = df.columns[startpoint_context:endpoint_context]
startpoint_criteria = endpoint_context
endpoint_criteria = startpoint_criteria + nb_criteria
criteria_dispo = df.columns[startpoint_criteria:endpoint_criteria]

year_dispo = df["Year"].unique()
Nyear = len(year_dispo)
techno_dispo = df["Technology"].unique()
Ntechno = len(techno_dispo)
colors = ["blue", "red", "green", "cyan", "magenta", "yellow", "black", "orange", "purple"]


def get_data(column_name):
    return df[column_name].values.reshape(Ntechno, Nyear, Nsample, usage_grid[0], usage_grid[1], usage_grid[2])


app = Dash(__name__)

app.layout = html.Div([
    html.H1("visualisation des données Hydrogene", style={'textAlign': 'center', 'fontFamily': 'sans-serif'}),
    html.Div([
        html.H2("Technique"),
        html.Div([
            html.Div([
                html.Label("Axe X"),
                dcc.Dropdown(id='x-tech-axis-dropdown', options=param_dispo, value=param_dispo[0]),
            ], className="dropdown-container"),

            html.Div([
                html.Label("Axe Y"),
                dcc.Dropdown(id='y-tech-axis-dropdown', options=param_dispo, value=param_dispo[1]),
            ], className="dropdown-container"),

            html.Div([
                html.Label("Axe Z"),
                dcc.Dropdown(id='z-tech-axis-dropdown', options=param_dispo, value=param_dispo[2]),
            ], className="dropdown-container"),
            html.Div([
                html.Label("Année"),
                dcc.Slider(
                    id='year-slider',
                    min=0,
                    max=Nyear - 1,
                    value=0,
                    marks={i: year_dispo[i] for i in range(Nyear)},
                    step=None
                ),
            ], className="slider-container"),
        ], className="control-panel"),

        dcc.Graph(id='tech_plot', className="graph-container")
    ]),
    html.Div([
        html.H2("contexte"),
        html.Div([
            html.Div([
                html.Label("Axe X"),
                dcc.Dropdown(id='x-cont-axis-dropdown', options=contexte_dispo, value=contexte_dispo[0]),
            ], className="dropdown-container"),

            html.Div([
                html.Label("Axe Y"),
                dcc.Dropdown(id='y-cont-axis-dropdown', options=contexte_dispo, value=contexte_dispo[1]),
            ], className="dropdown-container"),
        ], className="control-panel"),

        dcc.Graph(id='cont_plot', className="graph-container")
    ]),
    html.Div([
        html.H2("critere"),
        html.Div([
            html.Div([
                html.Label("Axe X"),
                dcc.Dropdown(id='x-crit-axis-dropdown', options=criteria_dispo, value=criteria_dispo[0]),
            ], className="dropdown-container"),

            html.Div([
                html.Label("Axe Y"),
                dcc.Dropdown(id='y-crit-axis-dropdown', options=criteria_dispo, value=criteria_dispo[1]),
            ], className="dropdown-container"),
        ], className="control-panel"),

        dcc.Graph(id='crit_plot', className="graph-container")
    ])
])

def update_graph(x_col, y_col, z_col= NULL, year_value =NULL):
    data_x = get_data(x_col)
    data_y = get_data(y_col)
    data_z = get_data(z_col)
    year_id = year_value
    fig = go.Figure()

    for i, tech in enumerate(techno_dispo):
        fig.add_trace(go.Scatter3d(
            x=data_x[i, year_id, :, 0, 0, 0],
            y=data_y[i, year_id, :, 0, 0, 0],
            z=data_z[i, year_id, :, 17, 11, 0],
            name=f"{tech}_{year_dispo[year_id]}",
            mode='markers',
            marker=dict(color=colors[i % len(colors)], size=4, opacity=0.8)
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title=x_col,
            yaxis_title=y_col,
            zaxis_title=z_col,
            bgcolor="#ffffff"
        ),
        margin=dict(l=0, r=0, b=0, t=50),
        hovermode='closest'
    )

    return fig


@app.callback(
    Output('tech_plot', 'figure'),
    Input('x-tech-axis-dropdown', 'value'),
    Input('y-tech-axis-dropdown', 'value'),
    Input('z-tech-axis-dropdown', 'value'),
    Input('year-slider', 'value')
)
def update_tech_plot(x_col, y_col, z_col, year_value): return update_graph(x_col, y_col, z_col, year_value)
@app.callback(
    Output('cont_plot', 'figure'),
    Input('x-cont-axis-dropdown', 'value'),
    Input('y-cont-axis-dropdown', 'value')
)
def update_tech_plot(x_col, y_col): return update_graph(x_col, y_col)
@app.callback(
    Output('crit_plot', 'figure'),
    Input('x-crit-axis-dropdown', 'value'),
    Input('y-crit-axis-dropdown', 'value')
)
def update_tech_plot(x_col, y_col): return update_graph(x_col, y_col)

if __name__ == '__main__':
    app.run(debug=True)
