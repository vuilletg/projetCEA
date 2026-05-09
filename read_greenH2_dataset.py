import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # NOUVELLE: Utilise pour Boxplot 
from dash import Dash, dcc, html, Input, Output, State
import os

df = None
Nsample = 100

def process_data(dataframe):
    cols = dataframe.columns

    p_dispo = [c for c in cols if c.startswith('T_')]
    c_dispo = [c for c in cols if c.startswith('CO_')]
    cr_dispo = [c for c in cols if c.startswith('CR_')]
    
    y_dispo = dataframe["Year"].unique()
    t_dispo = dataframe["Technology"].unique()

    return p_dispo, c_dispo, cr_dispo, y_dispo, t_dispo

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Visualisation des données Hydrogène", style={'textAlign': 'center'}),
    
    html.Div([
        html.Label("Nom du fichier CSV:"),
        dcc.Input(
            id='input-filename',
            type='text',
            value='ton_fichier.csv', 
            style={'width': '50%', 'margin': '10px'}
        ),
        html.Button('Charger et Appliquer', id='btn-apply', n_clicks=0, style={'marginLeft': '20px'})
    ], style={'backgroundColor': '#f9f9f9', 'padding': '10px'}),

    html.Div(id='graphs-container')
])

# CREATION BOXPLOT
def create_boxplot(y_col):
    if y_col is None or df is None:
        return go.Figure()
    
    clean_label = y_col.split('_')[-1]

    fig = px.box(
        df,
        x = "Technology",
        y = y_col,
        color = "Technology",
        facet_col = "Year",
        points = "outliers",
        title = f"Distribution de : {clean_label}",
        labels={
            "Technology": "Technologie",
            "Year": "Année",
            y_col: clean_label
        },
        template="plotly_white"
    )
    fig.update_layout(transition_duration=300,
                      margin = dict(l=40, r=40, t=80, b=40),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                      )
    return fig

@app.callback(
    Output('graphs-container', 'children'),
    Input('btn-apply', 'n_clicks'),
    State('input-filename', 'value'),
)
def update_all_data(n_clicks, filename):
    global df, param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo
    
    if n_clicks > 0:
        if os.path.exists(filename):
            temp_head = pd.read_csv(filename, nrows=0)
            dtype_map = {}
            for col in temp_head.columns:
                if col == 'Technology':
                    dtype_map[col] = 'category'
                elif col == 'Year':
                    dtype_map[col] = 'int16'
                else:
                    dtype_map[col] = 'float32' 
            df = pd.read_csv(filename, engine='pyarrow', dtype=dtype_map)
        else:
            return html.Div([html.H3(f"Erreur : Le fichier '{filename}' est introuvable.")])

    if df is None:
        return html.Div([html.H3("Entrez un nom de fichier et cliquez sur Appliquer")])
    
    param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo = process_data(df)
    Nyear = len(year_dispo)
    param_options = [{'label': p.split('_')[-1], 'value': p} for p in param_dispo]
    contexte_option = [{'label': c.split('_')[-1], 'value': c} for c in contexte_dispo]
    criteria_options = [{'label': cr.split('_')[-1], 'value': cr} for cr in criteria_dispo]
    
    return html.Div([
        html.Div([
            html.H2("Technique"),
            dcc.Dropdown(id='x-tech', options=param_options, value=param_dispo[0]),
            dcc.Dropdown(id='y-tech', options=param_options, value=param_dispo[1]),
            dcc.Dropdown(id='z-tech', options=param_options, value=param_dispo[2]),
            dcc.Slider(id='year-slider-tech', min=0, max=Nyear-1, value=0, marks={i: str(year_dispo[i]) for i in range(Nyear)}, step=None),
            dcc.Graph(id='tech_plot')
        ]),
        html.Div([
            html.H2("Contexte"),
            dcc.Dropdown(id='x-cont', options=contexte_option, value=contexte_dispo[0]),
            dcc.Dropdown(id='y-cont', options=contexte_option, value=contexte_dispo[1]),
            dcc.Slider(id='year-slider-cont', min=0, max=Nyear-1, value=0, marks={i: str(year_dispo[i]) for i in range(Nyear)}, step=None),
            dcc.Graph(id='cont_plot')
        ]),
        html.Div([
            html.H2("Critères"),

            # Ajouter RADIO BUTTON
            dcc.RadioItems(
                id='crit-plot-mode',
                options=[
                    {'label': ' Standard (Scatter)', 'value': 'std'},
                    {'label': ' Boxplot (Distribution)', 'value': 'box'}
                ],
                value='std',
                labelStyle={'display': 'inline-block', 'marginRight': '20px', 'fontWeight': 'bold'}
            ),
            #### FIN ####

            dcc.Dropdown(id='x-crit', options=criteria_options, value=criteria_dispo[0]),
            dcc.Dropdown(id='y-crit', options=criteria_options, value=criteria_dispo[1]),
            dcc.Graph(id='crit_plot')
        ])
    ])


def create_fig(x_col, y_col, z_col=None, year_idx=0):
    if x_col is None or y_col is None or df is None:
        return go.Figure()

    
    fig = go.Figure()
    Ntech = len(techno_dispo)
    points_per_tech_year = len(df) // (Ntech * len(year_dispo))
    try:
        data_x = df[x_col].values.reshape(Ntech, len(year_dispo), Nsample, points_per_tech_year // Nsample)
        data_y = df[y_col].values.reshape(Ntech, len(year_dispo), Nsample, points_per_tech_year // Nsample)
        
        for i, tech in enumerate(techno_dispo):
            z_vals = [0] * Nsample
            if z_col:
                data_z = df[z_col].values.reshape(Ntech, len(year_dispo), Nsample, points_per_tech_year // Nsample)
                z_vals = data_z[i, year_idx, :, 0]
                fig.add_trace(go.Scatter3d(
                    x=data_x[i, year_idx, :, 0],
                    y=data_y[i, year_idx, :, 0],
                    z=z_vals,
                    name=f"{tech}",
                    mode='markers',
                    marker=dict(size=4)
                ))
            else:
                points_x = data_x[i, year_idx, :, 1]
                points_y = data_y[i, year_idx, :, 1]
                fig.add_trace(go.Scatter(
                    x=points_x,
                    y=points_y,
                    name=f"{tech}",
                    mode='markers',
                    marker=dict(size=4)
                ))
    except Exception as e:
        print(f"Erreur de Reshape : {e}")
        return go.Figure()
        
    return fig

@app.callback(Output('tech_plot', 'figure'), [Input('x-tech', 'value'), Input('y-tech', 'value'), Input('z-tech', 'value'), Input('year-slider-tech', 'value')])
def update_t(x, y, z, yr): return create_fig(x, y, z, yr)

@app.callback(Output('cont_plot', 'figure'), [Input('x-cont', 'value'), Input('y-cont', 'value'), Input('year-slider-cont', 'value')])
def update_co(x, y, yr): return create_fig(x, y, year_idx=yr)

@app.callback(Output('crit_plot', 'figure'), [Input('x-crit', 'value'), Input('y-crit', 'value'),
                                              Input('crit-plot-mode', 'value') # Ajouter une nouvelle INPUT à partir "RADIO BUTTON"
                                              ])
#UPDATE
def update_cr(x, y, mode): 
    if mode == 'box':
        return create_boxplot(y)
    return create_fig(x, y)

if __name__ == '__main__':
    app.run(debug=True)