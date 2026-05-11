import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot

df = pd.read_csv("data_dump\MCfulldata_ntechno3_N100_i11_j11_k3_l7_y5_dataframe.csv")

Ntechno = 3
Nyear = 5
Nsample = 100
usage_grid = [11, 11, 3, 7]

H2_cost = df['CRITERIA Hydrogen cost (€/kgH2)'].values.reshape(Ntechno, Nyear, Nsample, usage_grid[0], usage_grid[1], usage_grid[2], usage_grid[3])
SEC = df['TECHNICAL Specific electric energy consumption (kWh/kgH2)'].values.reshape(Ntechno, Nyear, Nsample, usage_grid[0], usage_grid[1], usage_grid[2], usage_grid[3])
lifetime = df['TECHNICAL Lifetime (kh)'].values.reshape(Ntechno, Nyear, Nsample, usage_grid[0], usage_grid[1], usage_grid[2], usage_grid[3])

AEL_2026_cost_5_3_0_0 = H2_cost[0, 0, :, 5, 3, 0, 0]
AEL_2026_SEC = SEC[0, 0, :, 0, 0, 0, 0]
AEL_2026_life = lifetime[0, 0, :, 0, 0, 0, 0]

SOEL_2026_cost_5_3_0_0 = H2_cost[1, 0, :, 5, 3, 0, 0]
SOEL_2026_SEC = SEC[1, 0, :, 0, 0, 0, 0]
SOEL_2026_life = lifetime[1, 0, :, 0, 0, 0, 0]

fig = make_subplots(rows=1, cols=2,
                    subplot_titles = ["Scatter plot of efficiency and lifetime colored by H2 cost", "Relative H2 cost difference"],
                    specs=[[{"type": "xy"}, {"type": "xy"}]])

fig.add_trace(go.Scatter(x=AEL_2026_life,
                         y=AEL_2026_SEC,
                         name="AEL 2026",
                         showlegend=False,
                         mode='markers',
                         marker=dict(color=AEL_2026_cost_5_3_0_0,
                                     colorscale='Viridis_r',
                                     size=8),
                         hovertemplate =
                                '%{x} kh<br>'+
                                '%{y} kWh/kgH2<br>'+
                                '%{customdata} €/kgH2',
                         customdata=np.round(AEL_2026_cost_5_3_0_0,2),),
                         row=1, col=1)

fig.add_trace(go.Scatter(x=SOEL_2026_life,
                         y=SOEL_2026_SEC,
                         name="SOEL 2026",
                         showlegend=False,
                         mode='markers',
                         marker=dict(color=SOEL_2026_cost_5_3_0_0,
                                     colorscale='Viridis_r',
                                     size=8),
                         hovertemplate =
                                '%{x} kh<br>'+
                                '%{y} kWh/kgH2<br>'+
                                '%{customdata} €/kgH2',
                         customdata=np.round(SOEL_2026_cost_5_3_0_0,2),),
                         row=1, col=1)
            

# Compare AEL and SOEL mean cost in 2038 for heat_cost=0.5 and 0 cycles
diff_contour_cost = np.zeros((11,11))
for i in range(11):
    for j in range(11):
        diff_contour_cost[i,j] = H2_cost[0, 2, :, i, j, 1, 0].mean() - H2_cost[1, 2, :, i, j, 1, 0].mean()

normalisation = max(abs(diff_contour_cost[:,:].min()), abs(diff_contour_cost[:,:].max()))
relative_diff_contour_cost = diff_contour_cost[:,:]/normalisation

elec_price_range = np.linspace(0., 120., 11)
FLH_range = np.linspace(2000., 8000., 11)
y,x = np.meshgrid(elec_price_range, FLH_range)
dfLCOH = pd.DataFrame([x.flatten(),
                       y.flatten(),
                       diff_contour_cost.flatten(),
                       relative_diff_contour_cost.flatten(),]).T
dfLCOH.columns = ['FLH', 'p_elec', 'diff_mean_cost', 'rel_diff_mean_cost']


fig.add_trace(go.Scatter(x=dfLCOH['FLH'],
                         y=dfLCOH['p_elec'],
                         mode='markers',
                         marker=dict(
                                size=37,
                                symbol="square",
                                color=dfLCOH['rel_diff_mean_cost'].values,
                                colorscale="RdBu_r",
                                cmin=-1.0,
                                cmax=1.0,
                                showscale=True,
                                colorbar=dict(outlinewidth=0,
                                        tickvals=[-1, 1],
                                        ticktext=["AEL", "SOEL"],),
                                opacity=1.,
                                ),
                         showlegend=False,
                         name="",
                         hovertemplate =
                                '%{x} h/year<br>'+
                                '%{y} €/MWh<br>'+
                                'diff=%{customdata} €/kgH2',
                         customdata=np.round(dfLCOH['diff_mean_cost'].values,2),
                         ),
                         row=1, col=2)

fig.update_layout(width=1200, height=600, showlegend=False,
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    font=dict(size=12)
                    )
plot(fig, auto_open=True)



