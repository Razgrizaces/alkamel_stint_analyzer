from select import select
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from dash.dependencies import Output, Input
import plotly.express as px
import seaborn as sns

fia_wec_data = pd.read_csv("2012-2022_FIA_WEC_FULL_LAP_DATA.csv", index_col = 0)
fia_wec_data.season = fia_wec_data.season.map(str)

#these we'll get rid of after we load the data in
fia_wec_data['elapsed_s'] = fia_wec_data['elapsed_ms']/1000
fia_wec_data['circuit_season'] = fia_wec_data['round'].map(int).map(str) + " - " + fia_wec_data['circuit'].str.replace("_", " ")
fia_wec_data['championship'] = 'FIA WEC'
fia_wec_data['session'] = 'Race'
app = dash.Dash(__name__)
fia_classes = ['Overall', 'LMGTE', 'LMGTE Pro', 'LMGTE Am', 'LMPs', 'LMP1/Hypercar', 'LMP2', 'CNDT (LeMans Only)', 'LMP1-H (2014 Only)', 'LMP1-L (2014 Only)']

#one thing I need to fix is to map circuit to round 

#I didn't write this code so let's see if we can try to rewrite this so it looks better.
app.layout = html.Div(
    children=[
        html.Div(
            children=[
                #title
                html.H1(
                    children="Alkamel Systems Lap Time Analyzer", className="header-title"
                ),
                #header description
                html.P(
                    className="header-description",
                ),
            ],
            #header class
            className="header",
        ),
        html.Div(
            #pickers, but I think this is weird/wrong, bc it doesn't do what I want, let's try to use dbc
            children=[
                    html.Div(
                        children=[
                            #championship picker
                            html.Div(children="Championship", className="menu-title"),
                            dcc.Dropdown(
                                id="championship_filter",
                                options=[
                                    {"label": championship, "value": championship}
                                    for championship in np.sort(fia_wec_data.championship.unique())
                                ],
                                value="FIA WEC",
                                clearable=False,
                                className="dropdown",
                            )
                        ],className = 'menu-item'
                    ),
                    html.Div(
                        children=[
                            #season picker
                            html.Div(children="Season", className="menu-title"),
                            #these use dcc dropdowns, so we'll have to swap to dbc
                            dcc.Dropdown(
                                id="season_filter",
                                options=[
                                ],
                                clearable=False,
                                className="dropdown",
                            )
                        ],className = 'menu-item'
                    ),
                    html.Div(
                        children=[
                            #circuit picker -> this should change to round
                            html.Div(children="Circuit", className="menu-title"),
                            dcc.Dropdown(
                                id="circuit_filter",
                                options=[
                                ],
                                clearable=False,
                                className="dropdown",
                            )
                        ],className = 'menu-item'
                    ),
                    html.Div(
                        children=[
                        #class picker
                            html.Div(children="WEC Class", className="menu-title"),
                            dcc.Dropdown(
                                id="wec_class_filter",
                                options=[
                                    {"label": value, "value": value}
                                    for value in fia_classes
                                ],
                                clearable=False,
                                className="dropdown",
                            )
                        ],className = 'menu-item'
                    ),
                    html.Div(
                        children=[
                        #class picker
                            html.Div(children="Session", className="menu-title"),
                            dcc.Dropdown(
                                id="session_filter",
                                options=[
                                    {"label": "Race", "value": "Race"}
                                ],
                                clearable=False,
                                className="dropdown",
                            )
                        ],className = 'menu-item'
                    ),
                ],
                className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="lap_time_plot", 
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="position_plot", 
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
        
    ]
)

#callbacks/functions for the filters

#
@app.callback(
    Output('circuit_filter', 'options'),
    Input('season_filter', 'value')
)
def set_circuit_options(selected):
    return [{'label': i, 'value': i} for i in fia_wec_data[fia_wec_data['season']==selected].circuit_season.unique()]

@app.callback(
    Output('season_filter', 'options'),
    Input('championship_filter', 'value')
)
def set_season_options(selected):
    return[{'label': i, 'value': i} for i in fia_wec_data[fia_wec_data['championship']==selected].season.unique()]

@app.callback(
    [Output("position_plot", "figure"), Output("lap_time_plot", "figure")],
    [
        Input("championship_filter", "value"),
        Input("season_filter", "value"),
        Input("circuit_filter", "value"),
        Input("wec_class_filter", "value"),
        Input("session_filter", "value"),
    ],
)
def update_charts(championship, season, circuit, wec_class, session):

    #selector for championship
    fia_wec_data_filtered = fia_wec_data[fia_wec_data['championship'] == championship]
    #selector for round
    fia_wec_data_filtered = fia_wec_data_filtered[fia_wec_data_filtered['season'] == season]
    fia_wec_data_filtered = fia_wec_data_filtered[fia_wec_data_filtered['circuit_season'] == circuit]
    #selector for session
    fia_wec_data_filtered = fia_wec_data_filtered[fia_wec_data_filtered['session'] == session]
    #selector for class
    if(wec_class != 'Overall'):
        if wec_class == 'LMGTE':
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == 'LMGTE Pro')|(fia_wec_data_filtered['class'] == 'LMGTE Am')]
        elif wec_class == 'LMPs':
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == 'LMP2')|(fia_wec_data_filtered['class'] == 'LMP1')|\
                (fia_wec_data_filtered['class'] == 'LMP1-H')|(fia_wec_data_filtered['class'] == 'LMP1-L')|\
                    (fia_wec_data_filtered['class'] == 'HYPERCAR')]
        elif wec_class == 'CNDT (LeMans Only)':
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == 'CDNT')| (fia_wec_data_filtered['class'] == 'INNOVATIVE CAR')]
        elif wec_class == 'LMP1-H (2016 Only)':
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == 'LMP1-H')]
        elif wec_class == 'LMP1-L (2016 Only)':
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == 'LMP1-L')]
        elif wec_class == 'LMP1/Hypercar':
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == 'LMP1')|(fia_wec_data_filtered['class'] == 'HYPERCAR')|\
                (fia_wec_data_filtered['class'] == 'LMP1-H')|(fia_wec_data_filtered['class'] == 'LMP1-L')]
        else:
            fia_wec_data_filtered = fia_wec_data_filtered[(fia_wec_data_filtered['class'] == wec_class)]
    fia_wec_data_filtered = fia_wec_data_filtered.reset_index(drop=True)

    #this is the position plot format.
    if(wec_class == 'Overall' or wec_class == 'LMGTE' or wec_class == 'LMPs'):
        position_plot = px.line(fia_wec_data_filtered, x = 'elapsed_s', y = 'position', color = "team_no", color_discrete_sequence=px.colors.qualitative.Alphabet)
    else:
        position_plot = px.line(fia_wec_data_filtered, x = 'elapsed_s', y = 'class_position', color = "team_no", color_discrete_sequence=px.colors.qualitative.Alphabet)
    position_plot['layout']['yaxis']['autorange'] = "reversed"
    position_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black")

    #adding a lap time plot as well
    cutoff_time = 0
    if(wec_class == 'Overall'):
        #factor for cutoff time is changed a bit to show all laps. I think 1.6 works? 
        cutoff_time = fia_wec_data_filtered['lap_time_ms'].min()*1.6
        box_plot_title = '160% Time Box Plots'
    elif (wec_class == 'LMPs'):
    #ah if it's lmps, should be a bit smaller
        cutoff_time = fia_wec_data_filtered['lap_time_ms'].min()*1.3
        box_plot_title = '130% Time Box Plots'
    else:
        cutoff_time = fia_wec_data_filtered['lap_time_ms'].min()*1.1
        box_plot_title = '110% Time Box Plots'
    fia_wec_data_with_cutoff_time = fia_wec_data_filtered[fia_wec_data_filtered['lap_time_ms'] < cutoff_time]
    lap_time_plot = px.box(fia_wec_data_with_cutoff_time, y = 'team_no', x = 'lap_time_s', color = "team_no", color_discrete_sequence=px.colors.qualitative.Alphabet,title=box_plot_title)
    lap_time_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black", legend_font_color="white")

    return position_plot, lap_time_plot

if __name__ == "__main__":
    app.run_server(debug=True)