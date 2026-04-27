import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

df = pd.read_csv("MCfulldata_ntechno3_N100_pandas_L3251210.csv")

Nsample = 100
usage_grid = [31, 31, 5]
param_dispo = df.columns[2:]
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
        html.Div([
            html.Label("Axe X"),
            dcc.Dropdown(id='x-axis-dropdown', options=param_dispo, value=param_dispo[0]),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Axe Y"),
            dcc.Dropdown(id='y-axis-dropdown', options=param_dispo, value=param_dispo[1]),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("Axe Z"),
            dcc.Dropdown(id='z-axis-dropdown', options=param_dispo, value=param_dispo[2]),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        html.Div([
            html.Label("année"),
            dcc.Slider(id='year-slider',min=0, max=len(year_dispo) - 1,value=0,),
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'backgroundColor': '#f9f9f9', 'padding': '20px', 'borderRadius': '10px'}),

    dcc.Graph(id='plot', style={'height': '80vh'})
])

@app.callback(
    Output('plot', 'figure'),
    Input('x-axis-dropdown', 'value'),
    Input('y-axis-dropdown', 'value'),
    Input('z-axis-dropdown', 'value'),
    Input('year-slider', 'value')
)
def update_graph(x_col, y_col, z_col, year_value):
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

if __name__ == '__main__':
    app.run(debug=True)