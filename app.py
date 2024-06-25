import dash
from dash import dcc
from dash import html
from dash import dash_table
import pandas as pd
from dash.dependencies import Output, Input
import plotly.express as px
from google.cloud import bigquery
import os
from dash.exceptions import PreventUpdate
import google.auth
#caching stuff

#GCloud Stuff
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"
os.environ["GCLOUD_PROJECT"]='liquid-evening-342715'

credentials, project_id = google.auth.default()

ON_HEROKU = os.environ.get('ON_HEROKU')
if ON_HEROKU:
    port = int(os.environ.get("PORT", 8080)) 
else:
    port = 8080

client = bigquery.Client(project = 'liquid-evening-342715')

query_config = bigquery.QueryJobConfig(use_legacy_sql=True)


app = dash.Dash(__name__)
server = app.server

#one thing I need to fix is to map circuit to round c
from_table = """ FROM `liquid-evening-342715.alkamel_data.alkamel_timing_board_with_stint` tbws """
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

def pull_filters():
    query = """select championship, season, round_event, session, class
    from `liquid-evening-342715.alkamel_data.alkamel_timing_board_with_stint`
    group by 1,2,3,4,5
    order by 1,2,3,4,5"""
    df = client.query(query).to_dataframe().to_json(orient='split')
    return df

#I didn't write this code so let's see if we can try to rewrite this so it looks better.
app.layout = html.Div(children=[ 
        #title div
    html.Div(children=[
        html.H1(children="Alkamel Systems Lap Time Analyzer", className="header-title"), #title
        html.P(className="header-description",), #header
        html.Div(children=dcc.Store(id='filters', data=pull_filters())),
        html.Div(children=dcc.Store(id='alkamel_data')),
        html.Div(children=dcc.Store(id='alkamel_data_filtered')),
        ],className="header",), #header class for css
    html.Div(children=[ 
        html.Div(children=[
            html.Div(children="Championship", className="menu-title"),#championship picker
            dcc.Dropdown(id="championship_filter", options = [],clearable=False, className="dropdown",)
            ],className = 'menu-item'
        ),
        html.Div(children=[
            html.Div(children="Season", className="menu-title"),#season picker
            dcc.Dropdown(id="season_filter",options=[], clearable=False, className="dropdown",)
            ],className = 'menu-item'
        ),
        html.Div(children=[
            html.Div(children="Circuit", className="menu-title"),#circuit picker -> this should change to round
            dcc.Dropdown(id="circuit_filter",options=[], clearable=False, className="dropdown")
            ],className = 'menu-item'
        ),
        html.Div(children=[
            html.Div(children="Session", className="menu-title"),#session picker
            dcc.Dropdown(id="session_filter",options=[],clearable=False,className="dropdown",)
            ],className = 'menu-item'
        ),
        html.Div(children=[
            html.Div(children="Class", className="menu-title"),#class picker
            dcc.Dropdown(id="class_filter",options=[], clearable=False, className="dropdown")
            ],className = 'menu-item'
        )
        ],className="menu",
    ),
    html.Div(
        children=[
            html.Div(children=dash_table.DataTable(id='team_classification_table'), className='dash-table'),
        ],className = 'wrapper'
    ),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="position_plot", config={"displayModeBar": True},),className = 'card',),
        ],className = 'wrapper'
    ),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="team_lap_time_plot", config={"displayModeBar": True},),className = 'card',),
        ],className = 'wrapper'
    ),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="team_stints_plot", config={"displayModeBar": True},),className="card",),
        ],className = 'wrapper'
    ),
    html.Div(
        children=[
            html.Div(children=dash_table.DataTable(id='driver_classification_table'), className='dash-table'),
        ],className = 'wrapper'
    ),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="driver_lap_time_plot", config={"displayModeBar": True},),className="card",),
        ],className = 'wrapper'
    ),
    html.Div(
        children=[
            html.Div(children=dcc.Graph(id="driver_stints_plot", config={"displayModeBar": True},),className="card",),
        ],className = 'wrapper'
    )
])
def create_where_query(column, selected):
    where_query = "WHERE " + column + "='" + selected + "' "
    return where_query
def create_and_query(column, selected):
    and_query = "AND " + column + "='" + selected + "' "
    return and_query    


#loading takes forever for the filters, i think idea is to pull once, grab the data and populate everything from that
@app.callback(
    Output('championship_filter', 'options'),
    Input('filters', 'data'),
)
def pull_dropdown_filters(filters):
    filter_pd = pd.read_json(filters, orient='split')
    filtered_data = filter_pd.groupby('championship').count().reset_index()
    filtered_data = filtered_data['championship']
    return [{'label':i, 'value':i } for i in filtered_data]

@app.callback(
    Output('season_filter', 'options'),
    Input('championship_filter', 'value'),
    Input('filters', 'data')
)
def set_season_options(selected, filter_data):
    filtered_data = pd.read_json(filter_data, orient='split')
    filtered_data = filtered_data[filtered_data['championship'] == selected]
    filtered_data = filtered_data.groupby('season').count().reset_index()
    filtered_data = filtered_data['season']
    return [{'label': i, 'value': i} for i in filtered_data]

@app.callback(
    Output('circuit_filter', 'options'),
    Input('season_filter', 'value'),Input('championship_filter', 'value'),
    Input('filters', 'data')
)
def set_circuit_options(season, championship, filter_data):
    filtered_data = pd.read_json(filter_data, orient='split')
    filtered_data = filtered_data[(filtered_data['championship'] == championship)&(filtered_data['season']==season)]
    filtered_data = filtered_data.groupby('round_event').count().reset_index()
    filtered_data = filtered_data['round_event']
    return [{'label': i, 'value': i} for i in filtered_data]

@app.callback(
    Output('session_filter', 'options'),
    Input('championship_filter', 'value'), Input('season_filter', 'value'), Input('circuit_filter', 'value'), Input('filters', 'data')
)
def set_session_options(championship,season, circuit, filter_data):
    filtered_data = pd.read_json(filter_data, orient='split')
    filtered_data = filtered_data[(filtered_data['championship'] == championship)&(filtered_data['season']==season)&(filtered_data['round_event']==circuit)]
    filtered_data = filtered_data.groupby('session').count().reset_index()
    filtered_data = filtered_data['session']
    return [{'label': i, 'value': i} for i in filtered_data]

@app.callback(
    Output('class_filter', 'options'),
    Input('championship_filter', 'value'), Input('circuit_filter', 'value'), Input('season_filter', 'value'), Input('filters', 'data')
)
def set_class_options(championship, circuit, season,filter_data):
    filtered_data = pd.read_json(filter_data, orient='split')
    filtered_data = filtered_data[(filtered_data['championship'] == championship)&(filtered_data['season']==season)&(filtered_data['round_event']==circuit)]
    filtered_data = filtered_data.groupby('class').count().reset_index()
    filtered_data = filtered_data['class']
    #also add other classes
    other_classes = pd.Series()
    if championship == "LeMansCup" or championship == "ELMS":
        other_classes = pd.Series(['Overall'])
    else:
        other_classes = pd.Series(['Overall', 'GTs', 'LMPs'])
    df = pd.concat([other_classes, filtered_data]).reset_index(drop=True)
    return [{'label': i, 'value': i} for i in df]


def pull_data_sql(filters, query_type):
    #what columns do I really need?
    #potentially down the line
    #int, class_int, gap, class_gap
    #type 
    if (query_type == "all"):
        select_query = """SELECT key, lap_time_seconds, pit_time_seconds, session, round_event, team_no, crossing_finish_line_in_pit,
        position, class_position, driver_name, championship, manufacturer, vehicle, class, elapsed_seconds, team_stint, driver_stint"""
        full_query = select_query + from_table + filters
        df = client.query(full_query).to_dataframe()
        return df
    elif query_type == "class":
        class_query = f"""
        with get_position_based_on_time as(
        select team_no, position, class_position, championship, season, round, class_int, class_gap, max(elapsed_seconds) as completed_time
        FROM `liquid-evening-342715.alkamel_data.alkamel_timing_board_with_stint` tbws
        {filters}
        group by 1,2,3,4,5,6,7,8),
        get_classification as(
            SELECT team_no, vehicle, class, tbws.group, max(lap_number) as laps_completed,
            min(s1_seconds) as fastest_s1, min (s2_seconds) as fastest_s2, min(s3_seconds) as fastest_s3, min(lap_time_seconds) as fastest_lap, 
            max(elapsed_seconds) as completed_time
            FROM `liquid-evening-342715.alkamel_data.alkamel_timing_board_with_stint` tbws
        {filters}
        group by 1,2,3,4)
        select 
        rank() over (order by laps_completed desc, classification.completed_time asc) position, 
        rank() over (partition by class order by laps_completed desc, classification.completed_time asc) class_position,
        class_int,
        class_gap,
        pos.team_no, 
        vehicle, class, classification.group, laps_completed,
        fastest_s1,fastest_s2, fastest_s3,fastest_lap, pos.completed_time
        from get_position_based_on_time pos
        join get_classification classification
        on pos.completed_time = classification.completed_time
        order by laps_completed desc, completed_time asc"""
        df = client.query(class_query).to_dataframe()
        return df
    elif query_type == "drivers":
        driver_query = f"""
        with get_fastest_drivers as(
        select driver_name, team_no, class, min(lap_time_seconds) as fastest_lap_time, min(s1_seconds) as fastest_s1, min(s2_seconds) as fastest_s2, min(s3_seconds) as fastest_s3
        FROM `liquid-evening-342715.alkamel_data.alkamel_timing_board_with_stint` tbws
        {filters}
        group by 1,2,3
        order by 4 asc)
        select * from get_fastest_drivers"""
        df = client.query(driver_query).to_dataframe()
        return df

    else:
        return pd.DataFrame()

#@cache.memoize(timeout=TIMEOUT)
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
        return pull_data_sql(where_query, "all").to_json(orient='split')
    else:
        return pull_data_sql("LIMIT 0", "all").to_json(orient='split')

@app.callback(
    Output('team_classification_table', 'data'),
    Output('driver_classification_table', 'data'),
    Input('championship_filter', 'value'),
    Input('season_filter', 'value'),
    Input('circuit_filter', 'value'),
    Input('class_filter', 'value'),
)
def load_classification(championship, season, circuit, alk_class):
    where_query = ""
    team_wanted_columns = ['team_no', 'vehicle', 'class', 'group', 'round_event', 'lap_number','fastest_s1','fastest_s2','fastest_s3', 'fastest_lap','completed_time']
    team_class_df = pd.DataFrame(columns=team_wanted_columns)
    driver_wanted_colums = ['driver_name', 'team_no', 'fastest_lap_time','fastest_s1', 'fastest_s2','fastest_s3']
    driver_class_df = pd.DataFrame(columns=driver_wanted_colums)
    if(championship != None):
        where_query = create_where_query("championship", championship)
        if(season != None): 
            where_query = where_query + create_and_query("season", season)
            if(circuit != None):
                where_query = where_query + create_and_query("round_event", circuit)
                team_class_df = pull_data_sql(where_query, "class")
                driver_class_df = pull_data_sql(where_query, "drivers")
                if(alk_class != None):
                    team_class_df = filter_class(team_class_df,alk_class)
                    driver_class_df = filter_class(driver_class_df,alk_class)
                team_class_df = team_class_df.to_dict('records')
                driver_class_df = driver_class_df.to_dict('records')
                return team_class_df, driver_class_df
    raise PreventUpdate

def filter_class(df, wec_class):
    if(wec_class != 'Overall'):
        if wec_class == 'GTs':
            return df[(df['class'].str.contains("GT"))]
        elif wec_class == 'LMPs':
            return df[((df['class'].str.contains("LM P"))|(df['class'].str.contains("LMP"))|(df['class'].str.contains("P")))&~(df['class'].str.contains("GTE"))]
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
    [Output("position_plot", "figure"), Output("team_lap_time_plot", "figure"),Output("driver_lap_time_plot", "figure")],
    [Input('class_filter', 'value'),Input('alkamel_data_filtered', 'data')]
)
def update_dlt_plot(wec_class, alkamel_data_filtered):
    fia_wec_data_filtered = pd.read_json(alkamel_data_filtered, orient='split')
    fia_wec_data_filtered = fia_wec_data_filtered.reset_index(drop=True)
    #why was this not needed before?... so stupid lmao
    fia_wec_data_filtered = fia_wec_data_filtered.sort_values(by='elapsed_seconds')

    #filter for laps that aren'
    fia_wec_data_filtered = fia_wec_data_filtered[fia_wec_data_filtered['crossing_finish_line_in_pit'] != 'B']
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
    driver_lap_time_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black",legend_font_color="white")
    driver_lap_time_plot.update_yaxes(showticklabels=False)

    #this is the position plot format.
    if(wec_class == 'Overall' or wec_class == 'GTs' or wec_class == 'LMPs'):
        position_plot = px.line(fia_wec_data_filtered, x = 'elapsed_seconds', y = 'position', \
            color = "team_no", color_discrete_sequence=color_sequence)
    else:
        position_plot = px.line(fia_wec_data_filtered, x = 'elapsed_seconds', y = 'class_position',\
            color = "team_no", color_discrete_sequence=color_sequence)
    position_plot['layout']['yaxis']['autorange'] = "reversed"
    position_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black", legend_font_color="white")

    fia_wec_data_with_cutoff_time = fia_wec_data_filtered[fia_wec_data_filtered['lap_time_seconds'] < cutoff_time]
    lap_time_plot = px.box(fia_wec_data_with_cutoff_time, y = 'team_no', x = 'lap_time_seconds', color = "team_no", color_discrete_sequence=color_sequence,title=box_plot_title)
    lap_time_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black", legend_font_color="white")
    lap_time_plot.update_yaxes(showticklabels=False)

    return position_plot, lap_time_plot, driver_lap_time_plot

@app.callback(
    Output('team_stints_plot', 'figure'),
    [Input('alkamel_data_filtered', 'data'), Input("team_lap_time_plot", "hoverData")]
)
def update_team_stints_plot(alkamel_data_filtered, selected_team):
    
    fia_wec_data_filtered = pd.read_json(alkamel_data_filtered, orient='split')
    fia_wec_data_filtered = fia_wec_data_filtered.reset_index(drop=True)
    #why was this not needed before?... so stupid lmao
    fia_wec_data_filtered = fia_wec_data_filtered.sort_values(by='elapsed_seconds')
    fia_wec_data_filtered = fia_wec_data_filtered[fia_wec_data_filtered['crossing_finish_line_in_pit'] != 'B']
    color_sequence = px.colors.qualitative.Alphabet
    
    #if we're using just comparing stints, we prob don't need that high of a filter
    cutoff_time = fia_wec_data_filtered['lap_time_seconds'].min()*1.1
    box_plot_title = '110% Time Box Plots (Lower is Faster)'
    fia_wec_data_with_cutoff_time = fia_wec_data_filtered[fia_wec_data_filtered['lap_time_seconds'] < cutoff_time]
    if(selected_team != None):
        fia_wec_data_with_cutoff_time = fia_wec_data_with_cutoff_time[fia_wec_data_with_cutoff_time['team_no'] == selected_team['points'][0]['y']]
    
    team_stints_plot = px.box(fia_wec_data_with_cutoff_time, y = 'team_stint', x = 'lap_time_seconds', color = "team_stint", color_discrete_sequence=color_sequence, title=box_plot_title, )
    team_stints_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black", legend_font_color="white",clickmode ="event+select")
    team_stints_plot.update_yaxes(showticklabels=False)

    return team_stints_plot

@app.callback(
    Output('driver_stints_plot', 'figure'),
    [Input('alkamel_data_filtered', 'data'), Input("driver_lap_time_plot", "hoverData")]
)
def update_driver_stints_plot(alkamel_data_filtered, selected_driver):
    
    fia_wec_data_filtered = pd.read_json(alkamel_data_filtered, orient='split')
    fia_wec_data_filtered = fia_wec_data_filtered.reset_index(drop=True)
    #why was this not needed before?... so stupid lmao
    fia_wec_data_filtered = fia_wec_data_filtered.sort_values(by='elapsed_seconds')
    fia_wec_data_filtered = fia_wec_data_filtered[fia_wec_data_filtered['crossing_finish_line_in_pit'] != 'B']
    color_sequence = px.colors.qualitative.Alphabet
    
    #if we're using just comparing stints, we prob don't need that high of a filter
    cutoff_time = fia_wec_data_filtered['lap_time_seconds'].min()*1.1
    box_plot_title = '110% Time Box Plots (Lower is Faster)'
    fia_wec_data_with_cutoff_time = fia_wec_data_filtered[fia_wec_data_filtered['lap_time_seconds'] < cutoff_time]
    if(selected_driver != None):
        fia_wec_data_with_cutoff_time = fia_wec_data_with_cutoff_time[fia_wec_data_with_cutoff_time['driver_name'] == selected_driver['points'][0]['y']]

    team_stints_plot = px.box(fia_wec_data_with_cutoff_time, y = 'driver_stint', x = 'lap_time_seconds', color = "driver_stint", color_discrete_sequence=color_sequence, title=box_plot_title, )
    team_stints_plot.update_layout(paper_bgcolor="black",plot_bgcolor="black", legend_font_color="white",clickmode ="event+select")
    team_stints_plot.update_yaxes(showticklabels=False)

    return team_stints_plot

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
    #app.run(host='127.0.0.1', port=8070, debug=True, dev_tools_hot_reload=True)