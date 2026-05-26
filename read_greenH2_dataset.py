import os
from turtle import mode
from dash import ALL, Dash, Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import alphashape
import numpy as np

df = None
Nsample = 0

def process_data(dataframe):
    cols = dataframe.columns
    p_dispo = [c for c in cols if c.startswith("TECHNICAL ")]
    c_dispo = [c for c in cols if c.startswith("CONTEXT ")]
    cr_dispo = [c for c in cols if c.startswith("CRITERIA")]
    usagegrid = []
    for c in c_dispo:
        tmp = dataframe[c].unique()
        usagegrid.append(len(tmp))
    y_dispo = dataframe["Year"].unique()
    t_dispo = dataframe["Technology"].unique()
    return p_dispo, c_dispo, cr_dispo, y_dispo, t_dispo, usagegrid

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

app.layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Visualisation des données",
                    className="text-center my-4 text-primary fw-bold",
                ),
                width=12,
            ),
            className="mx-0",
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            dbc.Button(
                                "Charger un fichier CSV",
                                id="btn-open-modal",
                                n_clicks=0,
                                color="primary",
                                className="shadow-sm",
                            ),
                        ]
                    ),
                    className="mb-4 bg-light border-0 shadow-sm rounded-0",
                ),
                width=12,
            ),
            className="mx-0",
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Configuration du fichier"),
                    close_button=True,
                ),
                dbc.ModalBody(
                    [
                        html.Label(
                            "Nom du fichier CSV :", className="fw-bold mb-2"
                        ),
                        dcc.Input(
                            id="input-filename",
                            type="text",
                            value="ton_fichier.csv",
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Charger et Appliquer",
                        id="btn-apply",
                        n_clicks=0,
                        color="success",
                    )
                ),
            ],
            id="modal-file",
            is_open=False,
        ),
        html.Div(id="graphs-container", className="px-1"),
    ],
    fluid=True,
    className="p-0",
    style={
        "maxWidth": "100%",
        "overflowX": "hidden",
    }
)

@app.callback(
    Output("modal-file", "is_open"),
    [Input("btn-open-modal", "n_clicks"), Input("btn-apply", "n_clicks")],
    [State("modal-file", "is_open")],
)
def toggle_modal(n_open, n_close, is_open):
    if n_open or n_close:
        return not is_open
    return is_open

def create_boxplot(y_col, mode, selected_year, slider_values=None):
    if y_col is None or df is None:
        return go.Figure()

    mask = df["Year"].astype(str) == str(selected_year)

    if slider_values and len(slider_values) == len(contexte_dispo):
        for i, col_name in enumerate(contexte_dispo):
            unique_vals = df[col_name].unique()
            chosen_val = unique_vals[slider_values[i]]
            mask = mask & (df[col_name] == chosen_val)

    df_filtered = df[mask]

    if df_filtered.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Aucune donnée disponible pour ce contexte",
            template="plotly_white",
        )
        return fig

    clean_label = " ".join(y_col.split(" ")[1:])
    if mode == "2":
        fig = px.violin(
            df_filtered,
            x="Technology",
            y=y_col,
            color="Technology",
            points="all",
            title=f"Distribution de : {clean_label} ({selected_year})",
            labels={  
                "Technology": "Technologie",
                "Year": "Année",
                y_col: clean_label,
            },
            template="plotly_white",
        )
    else:
        fig = px.box(
            df_filtered,
            x="Technology",
            y=y_col,
            color="Technology",
            points="all",
            title=f"Distribution de : {clean_label} ({selected_year})",
            labels={
                "Technology": "Technologie",
                "Year": "Année",
                y_col: clean_label,
            },
            template="plotly_white",
        )
    fig.update_layout(
        transition_duration=300,
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    return fig

@app.callback(
    Output("graphs-container", "children"),
    Input("btn-apply", "n_clicks"),
    State("input-filename", "value"),
)
def update_all_data(n_clicks, filename):
    global df, param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo, usagegrid

    if n_clicks > 0:
        if os.path.exists(filename):
            temp_head = pd.read_csv(filename, nrows=0)
            dtype_map = {}
            for col in temp_head.columns:
                if col == "Technology":
                    dtype_map[col] = "category"
                elif col == "Year":
                    dtype_map[col] = "int16"
                else:
                    dtype_map[col] = "float32"
            df = pd.read_csv(filename, engine="pyarrow", dtype=dtype_map)
        else:
            return html.Div(
                [
                    html.H3(
                        f"Erreur : Le fichier '{filename}' est introuvable."
                    )
                ], className="text-center alert alert-danger"
            )

    if df is None:
        return html.Div(
            [html.H3("Cliquez sur 'Charger un fichier' pour commencer")], className="text-center alert alert-primary"
        )

    param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo, usagegrid = (
        process_data(df)
    )
    Nyear = len(year_dispo)
    param_options = [
        {"label": " ".join(p.split(" ")[1:]), "value": p} for p in param_dispo
    ]
    criteria_options = [
        {"label": " ".join(cr.split(" ")[1:]), "value": cr}
        for cr in criteria_dispo
    ]

    return html.Div(
        [
            dbc.Row(
                [
                    # --- PREMIÈRE COLONNE : CONTEXTE ---
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Contexte",
                                    className="bg-primary text-white fw-bold fs-5",
                                ),
                                dbc.CardBody(
                                    [
                                        html.Label(
                                            "Année :", className="fw-bold mb-1"
                                        ),
                                        dcc.Slider(
                                            id="year-slider-cont",
                                            min=0,
                                            max=Nyear - 1,
                                            value=0,
                                            marks={
                                                i: str(year_dispo[i])
                                                for i in range(Nyear)
                                            },
                                            step=None,
                                            className="mb-4",
                                        ),
                                        html.Div(
                                            id="dynamic-sliders-container",
                                            children=[
                                                html.Div(
                                                    [
                                                        html.Label(
                                                            f"{' '.join(contexte_dispo[i].split(' ')[1:])} :",
                                                            className="fw-bold mt-2",
                                                        ),
                                                        dcc.Slider(
                                                            id={
                                                                "type": "context-slider",
                                                                "index": str(
                                                                    df[
                                                                        contexte_dispo[
                                                                            i
                                                                        ]
                                                                    ].unique()
                                                                ),
                                                            },
                                                            min=0,
                                                            max=usagegrid[i] - 1,
                                                            value=0,
                                                            step=1,
                                                            marks={
                                                                j: str(val)
                                                                for j, val in enumerate(
                                                                    df[
                                                                        contexte_dispo[
                                                                            i
                                                                        ]
                                                                    ].unique()
                                                                )
                                                            },
                                                        ),
                                                    ]
                                                )
                                                for i in range(len(contexte_dispo))
                                            ],
                                        ),
                                    ]
                                ),
                            ],
                            className="shadow-sm h-100", # h-100 pour occuper toute la hauteur disponible
                        ),
                        md=4, # Largeur de la colonne Contexte (4/12)
                        className="mb-4",
                    ),
                    
                    # --- DEUXIÈME COLONNE : TECHNIQUE & CRITÈRES (Superposés) ---
                    dbc.Col(
                        [
                            # Bloc Technique
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        "Technique",
                                        className="bg-success text-white fw-bold fs-5",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="tech-plot-mode-container"),
                                            html.Label(
                                                "Axe X :", className="fw-bold mb-1"
                                            ),
                                            dcc.Dropdown(
                                                id="x-tech",
                                                options=param_options,
                                                value=param_dispo[0],
                                                className="mb-2",
                                            ),
                                            html.Label(
                                                "Axe Y :", className="fw-bold mb-1"
                                            ),
                                            dcc.Dropdown(
                                                id="y-tech",
                                                options=param_options,
                                                value=param_dispo[1],
                                                className="mb-2",
                                            ),
                                            html.Label(
                                                "Axe Z :", className="fw-bold mb-1"
                                            ),
                                            dcc.Dropdown(
                                                id="z-tech",
                                                options=param_options,
                                                value=(param_dispo[2] if len(param_dispo) > 2 else None),
                                                className="mb-3",
                                            ),
                                            dcc.Graph(id="tech_plot"),
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4", # Marge en bas pour séparer du bloc suivant
                            ),
                            
                            # Bloc Critères
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        "Critères",
                                        className="bg-info text-white fw-bold fs-5",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="crit-plot-mode-container"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Axe X :",
                                                                className="fw-bold mb-1",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="x-crit",
                                                                options=criteria_options,
                                                                value=criteria_dispo[0],
                                                            ),
                                                        ],
                                                        md=4, # Adapté en md=4 car l'espace horizontal est plus restreint
                                                        id="x-crit-container",
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Axe Y :",
                                                                className="fw-bold mb-1",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="y-crit",
                                                                options=criteria_options,
                                                                value=criteria_dispo[1],
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Axe Z :",
                                                                className="fw-bold mb-1",
                                                            ),
                                                            dcc.Dropdown(
                                                                id="z-crit",
                                                                options=criteria_options,
                                                                value=(criteria_dispo[2] if len(criteria_dispo) > 2 else None),
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dcc.Graph(id="crit_plot"),
                                        ]
                                    ),
                                ],
                                className="shadow-sm",
                            ),
                        ],
                        md=8, # Largeur de la colonne de droite (8/12)
                        className="mb-4",
                    ),
                ]
            ),
        ]
    )

def create_fig(x_col, y_col, z_col=None, mode = 1, year_idx=0, *args):
    if x_col is None or y_col is None or df is None:
        return go.Figure()
    x_label = " ".join(x_col.split(" ")[1:])
    y_label = " ".join(y_col.split(" ")[1:])
    product_usagegrid = 1
    for val in usagegrid:
        product_usagegrid *= val
    fig = go.Figure()
    Ntech = len(techno_dispo)
    Nsample_per_combination = len(df) // (
        Ntech * len(year_dispo) * product_usagegrid
    )
    try:
        data_x = df[x_col].values.reshape(
            Ntech, len(year_dispo), Nsample_per_combination, *usagegrid
        )
        data_y = df[y_col].values.reshape(
            Ntech, len(year_dispo), Nsample_per_combination, *usagegrid
        )
        for i, tech in enumerate(techno_dispo):
            z_vals = [0] * Nsample_per_combination
            if z_col:
                data_z = df[z_col].values.reshape(
                    Ntech, len(year_dispo), Nsample_per_combination, *usagegrid
                )
                z_label = " ".join(z_col.split(" ")[1:])
                fig.update_layout(
                    scene=dict(
                        xaxis_title=x_label,
                        yaxis_title=y_label,
                        zaxis_title=z_label,
                    )
                )
                z_vals = data_z[i, year_idx, :, *args]
                if mode == "2":
                    fig.add_trace(
                        go.Mesh3d(
                            x=data_x[i, year_idx, :, *args],
                            y=data_y[i, year_idx, :, *args],
                            z=z_vals,
                            name=f"{tech}",
                            opacity=0.5,
                            alphahull=4,
                            flatshading=False
                        )
                    )
                else:
                    fig.add_trace(
                        go.Scatter3d(
                            x=data_x[i, year_idx, :, *args],
                            y=data_y[i, year_idx, :, *args],
                            z=z_vals,
                            name=f"{tech}",
                            mode="markers",
                            marker=dict(size=4),
                        )
                    )
            else:
                fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)
                points_x = data_x[i, year_idx, :, *args]
                points_y = data_y[i, year_idx, :, *args]
                if mode == "3":
                    default_colors = px.colors.qualitative.Plotly
                    color_hex = default_colors[i % len(default_colors)]
                    rgb_color = px.colors.hex_to_rgb(color_hex)
                    r, g, b = rgb_color
                    custom_colorscale = [
                        [0.0, f"rgba({r}, {g}, {b}, 0.0)"],
                        [0.2, f"rgba({r}, {g}, {b}, 0.3)"],
                        [0.6, f"rgba({r}, {g}, {b}, 0.7)"], 
                        [1.0, f"rgba({r}, {g}, {b}, 1)"]   
                    ]
                    fig.add_trace(
                        go.Histogram2dContour(
                            x=points_x,
                            y=points_y,
                            name=f"{tech}",
                            contours=dict(
                                coloring='heatmap',
                                showlines=False
                            ),
                            line=dict(width=0.1),
                            ncontours=40,
                            colorscale=custom_colorscale,
                            showscale=False,
                            showlegend=True
                        )
                    )
                elif mode == "2":
                    points = np.column_stack((points_x, points_y))
                    hull = alphashape.alphashape(points, 0)
                    hull_x, hull_y = hull.exterior.xy
                    fig.add_trace(
                        go.Scatter(
                            x=list(hull_x),
                            y=list(hull_y),
                            name=f"{tech}",
                            mode="none",
                            fill="toself"
                        )
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=points_x,
                            y=points_y,
                            name=f"{tech}",
                            mode="markers",
                            marker=dict(size=4),
                        )
                    )
    except Exception as e:
        print(f"Erreur de Reshape : {e}")
        return go.Figure()
    return fig

@app.callback(
    Output("tech-plot-mode-container", "children"),[
    Input("x-tech", "value"),
    Input("y-tech", "value"),
    Input("z-tech", "value"),
]
)
def update_tech_plot_mode_container(x, y, z):
    axes_count = sum(1 for axis in [x, y, z] if axis is not None)
    return html.Div(
        [
        html.Label(
            "Mode d'affichage :",
            className="fw-bold mb-2 me-3",
        ),
        dbc.RadioItems(
            id="tech-plot-mode",
            options=[
                {"label": " Boxplot", "value": "1"},
                {"label": " Violin", "value": "2"}
            ] if axes_count == 1 else [
                {"label": " points 2d", "value": "1"},
                {"label": " surface 2d", "value": "2"},
                {"label": " densitée 2d", "value": "3"}
            ] if axes_count == 2 else[
                {"label": " points 3d", "value": "1"},
                {"label": " surface 3d", "value": "2"}
            ],
            value="1",
            inline=True,
            className="mb-3",
        ),
        ]
    )


@app.callback(
    Output("crit-plot-mode-container", "children"),
    [
        Input("x-crit", "value"),
        Input("y-crit", "value"),
        Input("z-crit", "value"),
    ],
)
def update_crit_plot_mode_container(x, y, z):
    axes_count = sum(1 for axis in [x, y, z] if axis is not None)
    return html.Div([
     html.Label(
            "Mode d'affichage :",
            className="fw-bold mb-2 me-3",
        ),
        dbc.RadioItems(
            id="crit-plot-mode",
            options=[
                {"label": " boxplot", "value": "1"},
                {"label": " Violin", "value": "2"}
            ] if axes_count == 1 else [
                {"label": " points 2d", "value": "1"},
                {"label": " surface 2d ", "value": "2"},
                {"label": " densitée 2d", "value": "3"}
            ] if axes_count == 2 else[
                {"label": " points 3d", "value": "1"},
                {"label": " surface 3d ", "value": "2"}
            ],
            value="1",
            inline=True,
            className="mb-3",
        ),
    ]
    )

@app.callback(
    Output("tech_plot", "figure"),
    [
        Input("x-tech", "value"),
        Input("y-tech", "value"),
        Input("z-tech", "value"),
        Input("tech-plot-mode", "value"),
        Input("year-slider-cont", "value"),
    ],
)
def update_t(x, y, z, mode, yr):
    slice = (0,) * len(usagegrid)
    if df is None:
        return go.Figure()
    active_axes = [axis for axis in [x, y, z] if axis is not None]
    axes_count = len(active_axes)
    if axes_count == 1:
        return create_boxplot(active_axes[0],mode, year_dispo[yr], slice)
    elif axes_count == 2:
        return create_fig(active_axes[0], active_axes[1], None, mode, yr, *slice)
    else:
        return create_fig(active_axes[0], active_axes[1], active_axes[2], mode, yr, *slice)

@app.callback(
    Output("crit_plot", "figure"),
    [
        Input("x-crit", "value"),
        Input("y-crit", "value"),
        Input("z-crit", "value"),
        Input("crit-plot-mode", "value"),
        Input("year-slider-cont", "value"),
        Input({"type": "context-slider", "index": ALL}, "value"),
    ],
)
def update_cr(x, y, z, mode, yr, slider_values):
    if df is None:
        return go.Figure()
    selected_year = year_dispo[yr]
    
    active_axes = [axis for axis in [x, y, z] if axis is not None]
    axes_count = len(active_axes)
    if axes_count == 1:
        return create_boxplot(active_axes[0], mode, selected_year, slider_values)
    elif axes_count == 2:
        return create_fig(active_axes[0], active_axes[1], None, mode, yr, *slider_values)
    else:
        return create_fig(active_axes[0], active_axes[1], active_axes[2], mode, yr, *slider_values)

if __name__ == "__main__":
    app.run(debug=True)