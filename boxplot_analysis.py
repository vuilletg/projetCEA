import pandas as pd
import plotly.express as px
import dash
from dash import Dash, dcc, html, Input, Output

# 1. Chargement des données
df = pd.read_csv("MCfulldata_ntechno3_N100_pandas_L3251210.csv", sep=None, engine='python')
df.columns = df.columns.str.strip()

# Dictionnaire des métriques
metrics_options = [
    {'label': 'Consommation électrique (kWh/kgH2)', 'value': 'Specific electric energy consumption (kWh/kgH2)'},
    {'label': 'Durée de vie (kh)', 'value': 'Lifetime (kh)'},
    {'label': 'Pression (barg)', 'value': 'Pressure (barg)'},
    {'label': 'Heures de fonctionnement (h/an)', 'value': 'Hours per year (h/year)'},
    {'label': "Coût de l'électricité (€/MWh)", 'value': 'Electricity cost (€/MWh)'},
    {'label': 'Coût de la chaleur (% coût élec)', 'value': 'Heat cost (% elec cost)'},
    {'label': "Coût de l'hydrogène (€/kgH2)", 'value': 'Hydrogen cost (€/kgH2)'},
    {'label': 'Empreinte Carbone (CO2eq/kgH2)', 'value': 'Carbon footprint (CO2eq/kgH2)'}
]

# 2. Initialisation de l'application Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Analyse Multicritère Hydrogène - Projet CEA", 
            style={'textAlign': 'center', 'fontFamily': 'Arial, sans-serif', 'padding': '20px'}),

    html.Div([
        html.Label("Sélectionnez l'indicateur à analyser :", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id ='metric-dropdown',
            options = metrics_options,
            value='Specific electric energy consumption (kWh/kgH2)', # Valeur défaut
            clearable=False,
            style={'width': '100%'}
        )
        ], style={'width': '50%', 'margin': '0 auto', 'padding': '20px'}),

    html.Div([
        dcc.Loading(
            id="loading-1",
            type="default",
            children=dcc.Graph(id='main-boxplot')
        )
    ], style={'padding': '20px'})
])

# 3. Callback 
@app.callback(
    Output('main-boxplot', 'figure'),
    Input('metric-dropdown', 'value')
)

def update_graph(selected_metric):
    label = next(item['label'] for item in metrics_options if item['value'] == selected_metric)

    fig = px.box(
        df,
        x = "Technology",
        y = selected_metric,
        color = "Technology",
        facet_col = "Year",
        points = "outliers",
        title = f"Distribution des données : {label}",
        labels={
            "Technology": "Technologie",
            "Year": "Année",
            selected_metric: label
        },
        template="plotly_white"
    )
    fig.update_layout(transition_duration=300,
                      margin = dict(l=40, r=40, t=80, b=40),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                      )
    return fig


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)