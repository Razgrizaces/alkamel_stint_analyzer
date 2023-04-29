import dash
from dash import dcc
from dash import html
import pandas as pd
from dash.dependencies import Output, Input
import plotly.express as px
from google.cloud import bigquery
import os
import json
from flask_caching import Cache
#caching stuff

#GCloud Stuff
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="application_default_credentials.json"
os.environ["GCLOUD_PROJECT"]='liquid-evening-342715'
client = bigquery.Client()

sql = """
    SELECT *
    FROM `liquid-evening-342715.alkamel_data.alkamel_timing_board`
    LIMIT 100
"""
query_config = bigquery.QueryJobConfig(use_legacy_sql=True)
app = dash.Dash(__name__)
cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache/'
})

TIMEOUT = 60

#one thing I need to fix is to map circuit to round 
from_table = """ FROM `liquid-evening-342715.alkamel_data.alkamel_timing_board` """
def sql_pull_one_column(column,where_query):
    select_column = "SELECT " + column + '\n'
    groupby_column = "GROUP BY " + column + '\n'
    where_column = ""
    if(where_query != ""):
        where_column = where_query + '\n'
    sql = select_column + from_table + where_column + groupby_column 

    # TODO: Set project_id to your Google Cloud Platform project ID.
    df = client.query(sql).to_dataframe()
    return df[column]

#I didn't write this code so let's see if we can try to rewrite this so it looks better.
app.layout = html.Div(children=[
        #title div
    html.Div(children=[
        html.H1(children="Alkamel Systems Lap Time Analyzer", className="header-title"), #title
        html.P(className="header-description",), #header
        ],className="header",), #header class for css
    html.Div(children=[ #pickers
        html.Div(children=[
                #championship picker
            html.Div(children="Championship", className="menu-title"),
            dcc.Dropdown(id="championship_filter",
                options=[{"label": championship, "value": championship}for championship in sql_pull_one_column("championship", "")],
                value="FIA WEC", clearable=False, className="dropdown",)
            ],className = 'menu-item'
        ),
        html.Div(children=[
                #season picker
            html.Div(children="Season", className="menu-title"),
            dcc.Dropdown(id="season_filter",options=[], clearable=False, className="dropdown",)
            ],className = 'menu-item'
        ),
        html.Div(children=[
                #circuit picker -> this should change to round
            html.Div(children="Circuit", className="menu-title"),
            dcc.Dropdown(id="circuit_filter",options=[], clearable=False, className="dropdown")
            ],className = 'menu-item'
        ),
        html.Div(children=[
            #session picker
            html.Div(children="Session", className="menu-title"),
            dcc.Dropdown(id="session_filter",options=[],clearable=False,className="dropdown",)
            ],className = 'menu-item'
        ),
        html.Div(children=[
            #class picker
            html.Div(children="Class", className="menu-title"),
            dcc.Dropdown(id="class_filter",options=[], clearable=False, className="dropdown")
            ],className = 'menu-item'
        ),
    ],className="menu",
),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="lap_time_plot", config={"displayModeBar": False},),className = 'card',),
            html.Div(children=dcc.Graph(id="position_plot", config={"displayModeBar": False},),className = 'card',),
            html.Div(children=dcc.Store(id='alkamel_data')),
            html.Div(children=dcc.Store(id='alkamel_data_filtered')),
        ],className="wrapper",
    ),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="driver_lap_time_plot", config={"displayModeBar": False},),className="card",),
        ],className = 'wrapper'
    )
])
def create_where_query(column, selected):
    where_query = "WHERE " + column + "='" + selected + "' "
    return where_query
def create_and_query(column, selected):
    and_query = "AND " + column + "='" + selected + "' "
    return and_query    

def pull_data_sql(filters):
    #what columns do I really need?
    #potentially down the line
    #int, class_int, gap, class_gap
    select_query = """SELECT key, lap_time_seconds, pit_time_seconds, session, round_event, team_no, 
    position, class_position, driver_name, championship, manufacturer, vehicle, class, elapsed_seconds"""
    full_query = select_query + from_table + filters
    df = client.query(full_query).to_dataframe()
    return df

@app.callback(
    Output('class_filter', 'options'),
    Input('championship_filter', 'value'), Input('circuit_filter', 'value'), Input('season_filter', 'value')
)
def set_class_options(championship, circuit, season):
    where_query = create_where_query("championship", championship)
    circuit_query = ""
    circuit_query_json = None
    if(season != None):
        where_query = where_query + create_and_query("season", season)
    if(circuit != None):
        circuit_query = create_and_query("round_event", circuit)
        circuit_query_json = json.dumps(circuit_query)
        where_query = where_query + circuit_query
    if championship != None :
        df = sql_pull_one_column("class", where_query).sort_values()
        #also add other classes
        other_classes = pd.Series()
        if championship == "LeMansCup" or championship == "ELMS":
            other_classes = pd.Series(['Overall'])
        else:
            other_classes = pd.Series(['Overall', 'GTs', 'LMPs'])
        df = pd.concat([other_classes, df]).reset_index(drop=True)
        return [{'label': i, 'value': i} for i in df]

@app.callback(
    Output('season_filter', 'options'),
    Input('championship_filter', 'value')
)
def set_season_options(selected):
    where_query = create_where_query("championship", selected)
    df = sql_pull_one_column("season", where_query).sort_values()
    return [{'label': i, 'value': i} for i in df]

@app.callback(
    Output('circuit_filter', 'options'),
    Input('season_filter', 'value'),Input('championship_filter', 'value')
)
def set_circuit_options(season, championship):
    where_query = create_where_query("championship", championship)
    if(season != None):
        where_query = where_query + create_and_query("season", season)
    df = sql_pull_one_column("round_event", where_query).sort_values()
    return [{'label': i, 'value': i} for i in df]

@cache.memoize(timeout=TIMEOUT)
@app.callback(
    Output('alkamel_data', 'data'),
    Input('championship_filter', 'value'), Input('season_filter', 'value'), Input('circuit_filter', 'value')
)
def create_sql_query(championship, season, circuit):
    #selector for championship
    if(championship != None):
        where_query = create_where_query("championship", championship)
        if(season != None): 
            where_query = where_query + create_and_query("season", season)
        if(circuit != None):
            where_query = where_query + create_and_query("round_event", circuit)
    #here, we should pull the data, but if the data is empty we just make it empty
        return pull_data_sql(where_query).to_json(orient='split')
    else:
        return json.dumps({'data':pull_data_sql("LIMIT 0")})

@app.callback(
    Output('session_filter', 'options'),
    Input('championship_filter', 'value'), Input('season_filter', 'value'), Input('circuit_filter', 'value')
)
def set_session_options(championship,season, circuit):
    where_query = ""
    if(championship != None):
        where_query = create_where_query("championship", championship)
        if(season != None): 
            where_query = where_query + create_and_query("season", season)
        if(circuit != None):
            where_query = where_query + create_and_query("round_event", circuit)
    df = sql_pull_one_column("session", where_query).sort_values()
    return [{'label': i, 'value': i} for i in df]

def filter_class(df, wec_class):
    if(wec_class != 'Overall'):
        if wec_class == 'GTs':
            return df[(df['class'].str.contains("GT"))]
        elif wec_class == 'LMPs':
            return df[(df['class'].str.contains("LM P"))|(df['class'].str.contains("LMP"))|(df['class'].str.contains("P"))]
        elif wec_class == 'LMP1/Hypercar':
            return df[(df['class'] == 'LMP1')|(df['class'] == 'LM P1')|(df['class'] == 'DPi')|(df['class'] == 'HYPERCAR')]
        else:
            return df[(df['class'] == wec_class)]
    return df

@app.callback(
    Output('alkamel_data_filtered', 'data'),
    Input("class_filter", "value"),Input("session_filter", "value"), Input('alkamel_data', 'data')
)
def pull_and_filter_alkamel_data(alk_class, session, fia_wec_data):
    fia_wec_data = pd.read_json(fia_wec_data, orient='split')
    fia_wec_data = filter_class(fia_wec_data, alk_class)
    fia_wec_data = fia_wec_data[fia_wec_data['session'] == session]
    return fia_wec_data.to_json(orient='split')
    
#callback for the charts
@app.callback(
    [Output("position_plot", "figure"), Output("lap_time_plot", "figure"),Output("driver_lap_time_plot", "figure")],
    [Input('class_filter', 'value'),Input('alkamel_data_filtered', 'data')]
)
def update_dlt_plot(wec_class, alkamel_data_filtered):
    fia_wec_data_filtered = pd.read_json(alkamel_data_filtered, orient='split')
    fia_wec_data_filtered = fia_wec_data_filtered.reset_index(drop=True)
    #filter for team + drivers
    #this is the position plot format.
    color_sequence = px.colors.qualitative.Alphabet
    #adding a lap time plot as well
    cutoff_time = 0
    if(wec_class == 'Overall'):
        #factor for cutoff time is changed a bit to show all laps. I think 1.6 works? 
        cutoff_time = fia_wec_data_filtered['lap_time_seconds'].min()*1.6
        box_plot_title = '160% Time Box Plots (Lower is Faster)'
    elif (wec_class == 'LMPs'):
    #ah if it's lmps, should be a bit smaller
        cutoff_time = fia_wec_data_filtered['lap_time_seconds'].min()*1.3
        box_plot_title = '130% Time Box Plots (Lower is Faster)'
    else:
        cutoff_time = fia_wec_data_filtered['lap_time_seconds'].min()*1.1
        box_plot_title = '110% Time Box Plots (Lower is Faster)'
    fia_wec_data_with_cutoff_time = fia_wec_data_filtered[fia_wec_data_filtered['lap_time_seconds'] < cutoff_time]

    driver_lap_time_plot = px.box(fia_wec_data_with_cutoff_time,y ='driver_name', x='lap_time_seconds', color = "driver_name", color_discrete_sequence=color_sequence, title=box_plot_title)
    driver_lap_time_plot.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black", 
        legend_font_color="white")
        
    #this is the position plot format.
    if(wec_class == 'Overall' or wec_class == 'GTs' or wec_class == 'LMPs'):
        position_plot = px.line(fia_wec_data_filtered, x = 'elapsed_seconds', y = 'position', \
            color = "team_no", color_discrete_sequence=color_sequence)
    else:
        position_plot = px.line(fia_wec_data_filtered, x = 'elapsed_seconds', y = 'class_position',\
            color = "team_no", color_discrete_sequence=color_sequence)
    position_plot['layout']['yaxis']['autorange'] = "reversed"
    position_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black")

    fia_wec_data_with_cutoff_time = fia_wec_data_filtered[fia_wec_data_filtered['lap_time_seconds'] < cutoff_time]
    lap_time_plot = px.box(fia_wec_data_with_cutoff_time, y = 'team_no', x = 'lap_time_seconds', color = "team_no", color_discrete_sequence=color_sequence,title=box_plot_title)
    lap_time_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black", legend_font_color="white")
    lap_time_plot.update_yaxes(showticklabels=False)

    return position_plot, lap_time_plot, driver_lap_time_plot
if __name__ == "__main__":
    app.run_server(debug=True)