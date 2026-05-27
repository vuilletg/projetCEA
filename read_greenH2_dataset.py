import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import ALL, Dash, Input, Output, State, dcc, html, no_update, Patch

# =============================================================================
# VARIABLES GLOBALES & CACHE
# =============================================================================
df = None
Nsample = 0
param_dispo = []      
contexte_dispo = []   
criteria_dispo = []   
year_dispo = []       
techno_dispo = []     
usagegrid = []        

# Cache pour éviter de refaire le reshape à chaque appel de create_fig
data_cache = {}

def process_data(dataframe):
    cols = dataframe.columns
    p_dispo = [c for c in cols if c.startswith("TECHNICAL ")]
    c_dispo = [c for c in cols if c.startswith("CONTEXT ")]
    cr_dispo = [c for c in cols if c.startswith("CRITERIA")]
    
    # Optimisation : List comprehension plus rapide
    usagegrid_local = [len(dataframe[c].unique()) for c in c_dispo]
    y_dispo = dataframe["Year"].unique()
    t_dispo = dataframe["Technology"].unique()
    
    return p_dispo, c_dispo, cr_dispo, y_dispo, t_dispo, usagegrid_local

# =============================================================================
# INITIALISATION DE L'APPLICATION DASH
# =============================================================================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H1("Visualisation des données", className="text-center my-4 text-primary fw-bold"), width=12)),
        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
            dbc.Button("Charger un fichier CSV", id="btn-open-modal", n_clicks=0, color="primary", className="shadow-sm"),
        ]), className="mb-4 bg-light border-0 shadow-sm rounded-0"), width=12)),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Configuration du fichier"), close_button=True),
            dbc.ModalBody([
                html.Label("Nom du fichier CSV :", className="fw-bold mb-2"),
                dcc.Input(id="input-filename", type="text", value="ton_fichier.csv"),
            ]),
            dbc.ModalFooter(dbc.Button("Charger et Appliquer", id="btn-apply", n_clicks=0, color="success")),
        ], id="modal-file", is_open=False),
        
        html.Div(id="graphs-container", className="px-1"),
    ],
    fluid=True, className="p-0", style={"maxWidth": "100%", "overflowX": "hidden"}
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

# =============================================================================
# FONCTIONS DE GÉNÉRATION DES GRAPHIQUES OPTIMISÉES
# =============================================================================

def create_boxplot(y_col, mode, selected_year, slider_values=None):
    if y_col is None or df is None:
        return go.Figure()

    # Filtre ultra-rapide via index ou booléens combinés
    mask = df["Year"] == int(selected_year)

    if slider_values and len(slider_values) == len(contexte_dispo):
        # Utilisation de query dynamique ou masques numpy combinés (plus rapide que des boucles pandas)
        for i, col_name in enumerate(contexte_dispo):
            unique_vals = df[col_name].unique()
            mask &= (df[col_name] == unique_vals[slider_values[i]])

    # Utiliser le format numpy/pyarrow sous-jacent via loc
    df_filtered = df.loc[mask, ["Technology", y_col]]

    if df_filtered.empty:
        fig = go.Figure()
        fig.update_layout(title="Aucune donnée disponible", template="plotly_white")
        return fig

    clean_label = y_col.split(" ", 1)[-1]
    
    # Éviter px.violin/box complet si on veut du speed, mais px reste correct si le dataframe est petit après filtre
    if mode == "2":
        fig = px.violin(df_filtered, x="Technology", y=y_col, color="Technology", points="all", template="plotly_white")
    else:
        fig = px.box(df_filtered, x="Technology", y=y_col, color="Technology", points="all", template="plotly_white")
        
    fig.update_layout(
        title=f"Distribution de : {clean_label} ({selected_year})",
        xaxis_title="Technologie", yaxis_title=clean_label,
        transition_duration=0, # Désactivé pour gagner en réactivité
        margin=dict(l=40, r=40, t=80, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_fig(x_col, y_col, z_col=None, mode=1, year_idx=0, *args):
    """
    Génère les graphiques complexes (2D/3D, contours, surfaces, nuages de points)
    en utilisant un découpage matriciel (Reshape) mis en cache pour isoler les dimensions.
    """
    if x_col is None or y_col is None or df is None:
        return go.Figure()
        
    x_label = x_col.split(" ", 1)[-1]
    y_label = y_col.split(" ", 1)[-1]
    
    fig = go.Figure()
    Ntech = len(techno_dispo)
    
    # Récupération ou création du cache pour le Reshape (ultra-rapide)
    global data_cache
    if x_col not in data_cache:
        product_usagegrid = np.prod(usagegrid)
        Nsample_per_combination = len(df) // (Ntech * len(year_dispo) * product_usagegrid)
        shape = (Ntech, len(year_dispo), Nsample_per_combination, *usagegrid)
        data_cache[x_col] = df[x_col].values.reshape(shape)
        data_cache[y_col] = df[y_col].values.reshape(shape)
        if z_col:
            data_cache[z_col] = df[z_col].values.reshape(shape)

    data_x = data_cache[x_col]
    data_y = data_cache[y_col]
    
    for i, tech in enumerate(techno_dispo):
        # Slice Numpy direct
        idx = (i, year_idx, slice(None)) + args
        points_x = data_x[idx]
        points_y = data_y[idx]
        
        # --- CAS DU TRACÉ 3D ---
        if z_col:
            data_z = data_cache[z_col]
            z_vals = data_z[idx]
            z_label = z_col.split(" ", 1)[-1]
            fig.update_layout(scene=dict(xaxis_title=x_label, yaxis_title=y_label, zaxis_title=z_label))
            
            if mode == "2":  # Mesh 3D (Surface) -> FONCTIONNALITÉ RESTAURÉE
                fig.add_trace(go.Mesh3d(
                    x=points_x, y=points_y, z=z_vals,
                    name=tech, opacity=0.5, alphahull=4, flatshading=False
                ))
            else:  # Scatter 3D (Points)
                fig.add_trace(go.Scatter3d(
                    x=points_x, y=points_y, z=z_vals,
                    name=tech, mode="markers", marker=dict(size=4)
                ))
        
        # --- CAS DU TRACÉ 2D ---
        else:
            fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)
            
            if mode == "3":  # Histogramme de densité 2D (Contours) -> FONCTIONNALITÉ RESTAURÉE
                default_colors = px.colors.qualitative.Plotly
                color_hex = default_colors[i % len(default_colors)]
                r, g, b = px.colors.hex_to_rgb(color_hex)
                
                # Ton échelle de couleurs personnalisée avec opacité adaptative (Alpha)
                custom_colorscale = [
                    [0.0, f"rgba({r}, {g}, {b}, 0.0)"],
                    [0.1, f"rgba({r}, {g}, {b}, 0.1)"],
                    [0.2, f"rgba({r}, {g}, {b}, 0.3)"],
                    [0.6, f"rgba({r}, {g}, {b}, 0.7)"], 
                    [1.0, f"rgba({r}, {g}, {b}, 1)"]   
                ]
                fig.add_trace(go.Histogram2dContour(
                    x=points_x, y=points_y, name=tech,
                    contours=dict(coloring='heatmap', showlines=False),
                    line=dict(width=0.1), ncontours=40, colorscale=custom_colorscale,
                    showscale=False, showlegend=True
                ))
                
            elif mode == "2":  # Enveloppe géométrique (Alpha Shape / Hull 2D)
                try:
                    import alphashape
                    points = np.column_stack((points_x, points_y))
                    hull = alphashape.alphashape(points, 0)
                    hull_x, hull_y = hull.exterior.xy
                    fig.add_trace(go.Scatter(
                        x=list(hull_x), y=list(hull_y), name=tech, mode="none", fill="toself"
                    ))
                except Exception:
                    # Fallback si alphashape crash ou n'est pas installé
                    fig.add_trace(go.Scattergl(
                        x=points_x, y=points_y, name=tech, mode="markers", marker=dict(size=4)
                    ))
                    
            else:  # Scatter 2D classique (Points via WebGL pour la performance)
                fig.add_trace(go.Scattergl(
                    x=points_x, y=points_y, name=tech, mode="markers", marker=dict(size=4)
                ))
                
    fig.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=50, b=40))
    return fig

# =============================================================================
# CALLBACKS DE MISE À JOUR
# =============================================================================

@app.callback(
    Output("graphs-container", "children"),
    Input("btn-apply", "n_clicks"),
    State("input-filename", "value"),
)
def update_all_data(n_clicks, filename):
    global df, param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo, usagegrid, data_cache

    if n_clicks > 0:
        if os.path.exists(filename):
            data_cache.clear() # Reset du cache à la lecture d'un nouveau fichier
            temp_head = pd.read_csv(filename, nrows=0)
            dtype_map = {col: "category" if col == "Technology" else ("int16" if col == "Year" else "float32") for col in temp_head.columns}
            df = pd.read_csv(filename, engine="pyarrow", dtype=dtype_map)
        else:
            return html.Div([html.H3(f"Erreur : '{filename}' introuvable.")], className="text-center alert alert-danger")

    if df is None:
        return html.Div([html.H3("Cliquez sur 'Charger un fichier' pour commencer")], className="text-center alert alert-primary")

    param_dispo, contexte_dispo, criteria_dispo, year_dispo, techno_dispo, usagegrid = process_data(df)
    Nyear = len(year_dispo)
    
    param_options = [{"label": p.split(" ", 1)[-1], "value": p} for p in param_dispo]
    criteria_options = [{"label": cr.split(" ", 1)[-1], "value": cr} for cr in criteria_dispo]
    contexte_options = [{"label": c.split(" ", 1)[-1], "value": c} for c in contexte_dispo]

    return html.Div([
        dbc.Row([
            # GAUCHE : CONTEXTE
            dbc.Col(dbc.Card([
                dbc.CardHeader("Contexte", className="bg-primary text-white fw-bold fs-5"),
                dbc.CardBody([
                    html.Label("Année :", className="fw-bold mb-1"),
                    dcc.Slider(id="year-slider-cont", min=0, max=Nyear - 1, value=0, marks={i: str(year_dispo[i]) for i in range(Nyear)}, step=None, className="mb-4"),
                    html.Hr(),
                    html.H5("Configuration Graphique Contexte", className="text-secondary mt-2"),
                    dbc.Row([
                        dbc.Col([html.Label("Axe X :", className="small fw-bold"), dcc.Dropdown(id="x-context-drop", options=contexte_options, value=contexte_dispo[0] if contexte_dispo else None, clearable=False)], md=6),
                        dbc.Col([html.Label("Axe Y :", className="small fw-bold"), dcc.Dropdown(id="y-context-drop", options=contexte_options, value=contexte_dispo[1] if len(contexte_dispo)>1 else None, clearable=False)], md=6),
                        dbc.Col([html.Label("Critère :", className="small fw-bold"), dcc.Dropdown(id="criteria-drop", options=criteria_options, value=criteria_dispo[0] if criteria_dispo else None, clearable=False)], md=6)
                    ], className="mb-2"),
                    
                    dcc.Graph(id="context_clickable_plot", className="mb-3"),
                    html.Hr(),
                    html.Label("Filtres Manuels (Sliders) :", className="fw-bold text-muted mb-2"),
                    
                    html.Div(id="sliders-container", children=[
                        html.Div(id={"type": "context-slider-wrapper", "index": col}, children=[
                            html.Label(f"{col.split(' ', 1)[-1]} :", className="fw-bold mt-2"),
                            dcc.Slider(id={"type": "context-slider", "index": col}, min=0, max=usagegrid[i] - 1, value=0, step=1, marks={j: str(val) for j, val in enumerate(df[col].unique())}),
                        ]) for i, col in enumerate(contexte_dispo)
                    ]),
                ]),
            ], className="shadow-sm h-100"), md=6, className="mb-4"),
            
            # DROITE : TECHNIQUE & CRITÈRES
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Technique", className="bg-success text-white fw-bold fs-5"),
                    dbc.CardBody([
                        html.Div(id="tech-plot-mode-container"),
                        html.Label("Axe X :", className="fw-bold mb-1"), dcc.Dropdown(id="x-tech", options=param_options, value=param_dispo[0], className="mb-2"),
                        html.Label("Axe Y :", className="fw-bold mb-1"), dcc.Dropdown(id="y-tech", options=param_options, value=param_dispo[1], className="mb-2"),
                        html.Label("Axe Z :", className="fw-bold mb-1"), dcc.Dropdown(id="z-tech", options=param_options, value=(param_dispo[2] if len(param_dispo) > 2 else None), className="mb-3"),
                        dcc.Graph(id="tech_plot"),
                    ])
                ], className="shadow-sm mb-4"),
                
                dbc.Card([
                    dbc.CardHeader("Critères", className="bg-info text-white fw-bold fs-5"),
                    dbc.CardBody([
                        html.Div(id="crit-plot-mode-container"),
                        dbc.Row([
                            dbc.Col([html.Label("Axe X :", className="fw-bold mb-1"), dcc.Dropdown(id="x-crit", options=criteria_options, value=criteria_dispo[0])], md=4),
                            dbc.Col([html.Label("Axe Y :", className="fw-bold mb-1"), dcc.Dropdown(id="y-crit", options=criteria_options, value=criteria_dispo[1])], md=4),
                            dbc.Col([html.Label("Axe Z :", className="fw-bold mb-1"), dcc.Dropdown(id="z-crit", options=criteria_options, value=(criteria_dispo[2] if len(criteria_dispo) > 2 else None))], md=4),
                        ], className="mb-3"),
                        dcc.Graph(id="crit_plot"),
                    ])
                ], className="shadow-sm"),
            ], md=6, className="mb-4"),
        ])
    ])


@app.callback(
    Output("context_clickable_plot", "figure"),
    [
        Input("x-context-drop", "value"),
        Input("y-context-drop", "value"),
        Input("criteria-drop", "value"),
        Input("year-slider-cont", "value"),
        Input({"type": "context-slider", "index": ALL}, "id"),
        Input({"type": "context-slider", "index": ALL}, "value")
    ]
)
def update_context_plot(x_ctx, y_ctx, crit_ctx, yr_idx, slider_ids, slider_values):
    if df is None or not x_ctx or not y_ctx or not crit_ctx:
        return go.Figure()
    
    selected_year = year_dispo[yr_idx]
    
    # Éviter .astype(str) dans les boucles ! On compare des entiers directement.
    df_filtered = df[df["Year"] == int(selected_year)]
    
    mapping_sliders = {sid["index"]: sval for sid, sval in zip(slider_ids, slider_values)}
    
    # Groupement vectorisé avec Pandas au lieu d'une boucle imbriquée sur chaque case !
    # C'est ÇA qui tuait tes performances.
    filter_cols = [c for c in contexte_dispo if c != x_ctx and c != y_ctx and c in mapping_sliders]
    for col in filter_cols:
        unique_vals = list(df[col].unique())
        df_filtered = df_filtered[df_filtered[col] == unique_vals[mapping_sliders[col]]]
        
    x_label = x_ctx.split(" ", 1)[-1]
    y_label = y_ctx.split(" ", 1)[-1]
    crit_label = crit_ctx.split(" ", 1)[-1]
    
    # Agrégation groupée ultra-rapide
    grouped = df_filtered.groupby([y_ctx, x_ctx, "Technology"])[crit_ctx].mean().reset_index()
    if grouped.empty:
        return go.Figure()

    # Trouver le vainqueur de manière vectorisée
    idx_max = grouped.groupby([y_ctx, x_ctx])[crit_ctx].idxmax()
    winners = grouped.loc[idx_max]

    x_bins = sorted(df[x_ctx].unique())
    y_bins = sorted(df[y_ctx].unique())
    tech_to_idx = {tech: i for i, tech in enumerate(techno_dispo)}
    
    z_matrix = np.full((len(y_bins), len(x_bins)), np.nan)
    customdata_matrix = [[None for _ in x_bins] for _ in y_bins]
    hover_matrix = [["Aucune donnée" for _ in x_bins] for _ in y_bins]

    # Remplissage des matrices optimisé
    x_to_pos = {val: i for i, val in enumerate(x_bins)}
    y_to_pos = {val: i for i, val in enumerate(y_bins)}

    for _, row in winners.iterrows():
        i = y_to_pos[row[y_ctx]]
        j = x_to_pos[row[x_ctx]]
        z_matrix[i, j] = tech_to_idx[row["Technology"]]
        customdata_matrix[i][j] = [row[x_ctx], row[y_ctx]]
        hover_matrix[i][j] = f"<b>Dominant</b>: {row['Technology']}<br><b>Valeur</b>: {row[crit_ctx]:.2f}"

    plotly_colors = px.colors.qualitative.Plotly
    custom_colorscale = []
    N_tech = len(techno_dispo)
    for tech, idx in tech_to_idx.items():
        base_color = plotly_colors[idx % len(plotly_colors)]
        custom_colorscale.extend([[idx / N_tech, base_color], [(idx + 1) / N_tech, base_color]])

    fig = go.Figure(data=go.Heatmap(
        x=x_bins, y=y_bins, z=z_matrix, customdata=customdata_matrix,
        text=hover_matrix, hoverinfo="text", colorscale=custom_colorscale,
        showscale=False, xgap=2, ygap=2, zmin=0, zmax=N_tech
    ))
    
    fig.update_layout(
        title=f"Matrice de Contexte ({selected_year})",
        xaxis=dict(title=x_label, type='category'),
        yaxis=dict(title=y_label, type='category'),
        clickmode='event+select', template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


@app.callback(
    [Output({"type": "context-slider-wrapper", "index": ALL}, "style"),
     Output({"type": "context-slider", "index": ALL}, "value")],
    [Input("x-context-drop", "value"), Input("y-context-drop", "value"), Input("context_clickable_plot", "clickData")],
    [State({"type": "context-slider", "index": ALL}, "id"), State({"type": "context-slider", "index": ALL}, "value")]
)
def handle_sliders_visibility_and_values(x_ctx, y_ctx, click_data, slider_ids, current_values):
    styles = []
    new_values = list(current_values)
    
    clicked_x_val = None
    clicked_y_val = None
    if click_data and "points" in click_data:
        point = click_data["points"][0]
        if "customdata" in point and point["customdata"] is not None:
            clicked_x_val, clicked_y_val = point["customdata"][0], point["customdata"][1]

    for i, s_id in enumerate(slider_ids):
        col_name = s_id["index"]
        if col_name == x_ctx or col_name == y_ctx:
            styles.append({"display": "none"})
            unique_vals = list(df[col_name].unique())
            if col_name == x_ctx and clicked_x_val in unique_vals:
                new_values[i] = unique_vals.index(clicked_x_val)
            elif col_name == y_ctx and clicked_y_val in unique_vals:
                new_values[i] = unique_vals.index(clicked_y_val)
        else:
            styles.append({"display": "block"})
            
    return styles, new_values

# Modes d'affichages simplifiés (plus besoin de tout reconstruire)
@app.callback(Output("tech-plot-mode-container", "children"), [Input("x-tech", "value"), Input("y-tech", "value"), Input("z-tech", "value")])
def update_tech_plot_mode_container(x, y, z):
    axes_count = sum(1 for axis in [x, y, z] if axis is not None)
    options = [{"label": " Boxplot", "value": "1"}, {"label": " Violin", "value": "2"}] if axes_count == 1 else \
              [{"label": " points 2d", "value": "1"}, {"label": " surface 2d", "value": "2"}, {"label": " densité 2d", "value": "3"}] if axes_count == 2 else \
              [{"label": " points 3d", "value": "1"}, {"label": " surface 3d", "value": "2"}]
    return html.Div([html.Label("Mode d'affichage :", className="fw-bold mb-2 me-3"), dbc.RadioItems(id="tech-plot-mode", options=options, value="1", inline=True, className="mb-3")])

@app.callback(Output("crit-plot-mode-container", "children"), [Input("x-crit", "value"), Input("y-crit", "value"), Input("z-crit", "value")])
def update_crit_plot_mode_container(x, y, z):
    axes_count = sum(1 for axis in [x, y, z] if axis is not None)
    options = [{"label": " boxplot", "value": "1"}, {"label": " Violin", "value": "2"}] if axes_count == 1 else \
              [{"label": " points 2d", "value": "1"}, {"label": " surface 2d ", "value": "2"}, {"label": " densité 2d", "value": "3"}] if axes_count == 2 else \
              [{"label": " points 3d", "value": "1"}, {"label": " surface 3d ", "value": "2"}]
    return html.Div([html.Label("Mode d'affichage :", className="fw-bold mb-2 me-3"), dbc.RadioItems(id="crit-plot-mode", options=options, value="1", inline=True, className="mb-3")])

@app.callback(
    Output("tech_plot", "figure"),
    [Input("x-tech", "value"), Input("y-tech", "value"), Input("z-tech", "value"), Input("tech-plot-mode", "value"), Input("year-slider-cont", "value")]
)
def update_tech_graph(x, y, z, mode, yr):
    if df is None: return go.Figure()
    slice_tuple = (0,) * len(usagegrid)
    active_axes = [axis for axis in [x, y, z] if axis is not None]
    if len(active_axes) == 1: return create_boxplot(active_axes[0], mode, year_dispo[yr], slice_tuple)
    return create_fig(active_axes[0], active_axes[1], active_axes[2] if len(active_axes)>2 else None, mode, yr, *slice_tuple)

from dash import ctx  # Assure-toi que ctx est importé depuis dash tout en haut de ton script

@app.callback(
    Output("crit_plot", "figure"),
    [Input("x-crit", "value"), 
     Input("y-crit", "value"), 
     Input("z-crit", "value"), 
     Input("crit-plot-mode", "value"), 
     Input("year-slider-cont", "value"),
     Input("context_clickable_plot", "clickData"), # On écoute directement le clic ici
     Input({"type": "context-slider", "index": ALL}, "id"), 
     Input({"type": "context-slider", "index": ALL}, "value")],
    [State("x-context-drop", "value"),
     State("y-context-drop", "value")]
)
def update_criteria_graph(x, y, z, mode, yr, click_data, slider_ids, slider_values, x_ctx_col, y_ctx_col):
    if df is None: 
        return go.Figure()
        
    # 1. On reconstruit d'abord le dictionnaire des valeurs actuelles des sliders
    mapping_sliders = {sid["index"]: sval for sid, sval in zip(slider_ids, slider_values)}
    
    # 2. Si le callback a été déclenché par un clic sur le graphique de contexte, 
    # on intercepte les coordonnées cliquées pour écraser temporairement les valeurs des sliders masqués
    if ctx.triggered_id == "context_clickable_plot" and click_data and "points" in click_data:
        point = click_data["points"][0]
        if "customdata" in point and point["customdata"] is not None:
            clicked_x_val, clicked_y_val = point["customdata"][0], point["customdata"][1]
            
            # On retrouve l'index correspondant à la valeur cliquée dans l'unique grid pour chaque axe
            if x_ctx_col in mapping_sliders:
                unique_x = list(df[x_ctx_col].unique())
                if clicked_x_val in unique_x:
                    mapping_sliders[x_ctx_col] = unique_x.index(clicked_x_val)
                    
            if y_ctx_col in mapping_sliders:
                unique_y = list(df[y_ctx_col].unique())
                if clicked_y_val in unique_y:
                    mapping_sliders[y_ctx_col] = unique_y.index(clicked_y_val)

    # 3. Réordonnancement strict pour correspondre au format attendu par le cache Numpy / Reshape
    full_slider_values = [mapping_sliders[col] for col in contexte_dispo]
    
    active_axes = [axis for axis in [x, y, z] if axis is not None]
    if len(active_axes) == 1: 
        return create_boxplot(active_axes[0], mode, year_dispo[yr], full_slider_values)
        
    return create_fig(active_axes[0], active_axes[1], active_axes[2] if len(active_axes) > 2 else None, mode, yr, *full_slider_values)

if __name__ == "__main__":
    app.run(debug=True)