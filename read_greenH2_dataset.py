import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import io

df = pd.read_csv("MCfulldata_ntechno3_N100_pandas_L3251210.csv")
nb_param_tech, nb_param_context, nb_criteria = 3, 3, 2
Nsample = 100
usage_grid = [31, 31, 5]
colors = ["blue", "red", "green", "cyan", "magenta", "yellow", "black", "orange", "purple"]

def process_data(dataframe, n_tech, n_cont, n_crit):
    endpoint_tech = 2 + n_tech
    p_dispo = dataframe.columns[2:endpoint_tech]
    endpoint_context = endpoint_tech + n_cont
    c_dispo = dataframe.columns[endpoint_tech:endpoint_context]
    endpoint_criteria = endpoint_context + n_crit
    cr_dispo = dataframe.columns[endpoint_context:endpoint_criteria]
    
    y_dispo = dataframe["Year"].unique()
    t_dispo = dataframe["Technology"].unique()
    return p_dispo, c_dispo, cr_dispo, y_dispo, t_dispo

param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo = process_data(df, nb_param_tech, nb_param_context, nb_criteria)

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Visualisation des données Hydrogène", style={'textAlign': 'center'}),
    
    html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Glisser-déposer ou ', html.A('Sélectionner un CSV')]),
            style={'width': '50%', 'height': '60px', 'lineHeight': '60px', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px auto'}
        ),
        html.Div([
            html.Label("Nb Tech: "), dcc.Input(id='in-tech', type='number', value=3, style={'width': '50px', 'marginRight': '10px'}),
            html.Label("Nb Context: "), dcc.Input(id='in-cont', type='number', value=3, style={'width': '50px', 'marginRight': '10px'}),
            html.Label("Nb Critères: "), dcc.Input(id='in-crit', type='number', value=2, style={'width': '50px'}),
            html.Button('Appliquer', id='btn-apply', n_clicks=0, style={'marginLeft': '20px'})
        ], style={'textAlign': 'center', 'marginBottom': '20px'})
    ], style={'backgroundColor': '#f9f9f9', 'padding': '10px'}),

    dcc.Store(id='stored-data'),

    html.Div(id='graphs-container')
])

@app.callback(
    Output('graphs-container', 'children'),
    Input('btn-apply', 'n_clicks'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('in-tech', 'value'),
    State('in-cont', 'value'),
    State('in-crit', 'value')
)
def update_all_data(n_clicks, contents, filename, n_t, n_co, n_cr):
    global df, param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo
    
    if contents is not None:
        import base64
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    
    param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo = process_data(df, n_t, n_co, n_cr)
    Nyear = len(year_dispo)

    return html.Div([
        html.Div([
            html.H2("Technique"),
            dcc.Dropdown(id='x-tech', options=param_dispo, value=param_dispo[0]),
            dcc.Dropdown(id='y-tech', options=param_dispo, value=param_dispo[1]),
            dcc.Dropdown(id='z-tech', options=param_dispo, value=param_dispo[2]),
            dcc.Slider(id='year-slider', min=0, max=Nyear-1, value=0, marks={i: str(year_dispo[i]) for i in range(Nyear)}, step=None),
            dcc.Graph(id='tech_plot')
        ]),
        html.Div([
            html.H2("Contexte"),
            dcc.Dropdown(id='x-cont', options=contexte_dispo, value=contexte_dispo[0]),
            dcc.Dropdown(id='y-cont', options=contexte_dispo, value=contexte_dispo[1]),
            dcc.Graph(id='cont_plot')
        ]),
        html.Div([
            html.H2("Critères"),
            dcc.Dropdown(id='x-crit', options=criteria_dispo, value=criteria_dispo[0]),
            dcc.Dropdown(id='y-crit', options=criteria_dispo, value=criteria_dispo[1]),
            dcc.Graph(id='crit_plot')
        ])
    ])

def create_fig(x_col, y_col, z_col=None, year_idx=0):
    fig = go.Figure()
    Ntech = len(techno_dispo)
    # Reshape dynamique basé sur les données actuelles
    data_x = df[x_col].values.reshape(Ntech, len(year_dispo), Nsample, *usage_grid)
    data_y = df[y_col].values.reshape(Ntech, len(year_dispo), Nsample, *usage_grid)
    
    for i, tech in enumerate(techno_dispo):
        z_vals = [0] * Nsample # Default si pas de Z
        if z_col:
            data_z = df[z_col].values.reshape(Ntech, len(year_dispo), Nsample, *usage_grid)
            z_vals = data_z[i, year_idx, :, 17, 11, 0]

        fig.add_trace(go.Scatter3d(
            x=data_x[i, year_idx, :, 0, 0, 0],
            y=data_y[i, year_idx, :, 0, 0, 0],
            z=z_vals,
            name=f"{tech}",
            mode='markers',
            marker=dict(size=4)
        ))
    return fig

@app.callback(Output('tech_plot', 'figure'), [Input('x-tech', 'value'), Input('y-tech', 'value'), Input('z-tech', 'value'), Input('year-slider', 'value')])
def update_t(x, y, z, yr): return create_fig(x, y, z, yr)

@app.callback(Output('cont_plot', 'figure'), [Input('x-cont', 'value'), Input('y-cont', 'value')])
def update_co(x, y): return create_fig(x, y)

@app.callback(Output('crit_plot', 'figure'), [Input('x-crit', 'value'), Input('y-crit', 'value')])
def update_cr(x, y): return create_fig(x, y)

if __name__ == '__main__':
    app.run(debug=True)