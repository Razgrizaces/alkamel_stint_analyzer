import pandas as pd
import numpy as np

def convert_to_ms(x):
    hour = 0
    try:
        hour, minutes, second = x.split(":")
    except ValueError:
        minutes, second = x.split(":")
    hour_seconds = int(hour)*60*60
    seconds, ms = second.split(".")
    minute_seconds = (int(minutes)*60 + int(seconds) + int(hour_seconds))*1000 
    total_ms = minute_seconds + int(ms)
    return total_ms


def search_key_in_dicts(key, dict):
    for d in dict:
        if d['key'] == key:
            return d
    return None
def update_value_in_dicts(key, dict, col, value):
    dict_key = search_key_in_dicts(key, dict)
    dict_key.update({col : value})
def increment_position(key, dict):
    update_value_in_dicts(key, dict, 'position', search_key_in_dicts(key, dict).get('position') + 1)
    return search_key_in_dicts(key, dict).get('position')
def increment_class_position(key, dict):
    update_value_in_dicts(key, dict, 'class_position', search_key_in_dicts(key, dict).get('class_position') + 1)
    return search_key_in_dicts(key, dict).get('class_position')
def main():
    fia_wec_data = pd.read_csv("2012-2022_FIA_WEC_FULL_LAP_DATA_v7.csv", index_col=0)
    fia_wec_data['season'] = fia_wec_data['season'].map(str)
    fia_wec_data.groupby('season').mean()
    year_filter = ['2012']
    data_w_filters = fia_wec_data[
        (fia_wec_data['season'].isin(year_filter))]
    data_w_filters['elapsed_s'] = data_w_filters.elapsed.map(convert_to_ms)/1000

    #something I didn't think about is gap and position, maybe let's see if we can create one 

    data_w_filters_sorted_hour = data_w_filters.sort_values(['round', 'lap_number', 'elapsed_s']).reset_index(drop=True)

    data_w_filters_sorted_hour['key'] = data_w_filters_sorted_hour['season'] + "_" +  data_w_filters_sorted_hour['round'].map(int).map(str) + "_" + data_w_filters_sorted_hour['lap_number'].map(int).map(str) 
    wanted_columns = ['key', 'round', 'lap_number']
    data_keys = data_w_filters_sorted_hour.groupby('key').mean().reset_index()[wanted_columns].sort_values(['round','lap_number']).reset_index(drop=True)
    data_keys['position'] = 0
    data_keys_dict = data_keys.to_dict('records')

    data_w_filters_sorted_hour['key_class'] = data_w_filters_sorted_hour['key'] + "_" +  data_w_filters_sorted_hour['class']
    wanted_columns = ['key_class', 'round', 'lap_number']
    data_keys_class = data_w_filters_sorted_hour.groupby('key_class').mean().reset_index()[wanted_columns].sort_values(['round','lap_number']).reset_index(drop=True)
    data_keys_class['key'] = data_keys_class['key_class']
    data_keys_class = data_keys_class.drop(['key_class'], axis=1)
    data_keys_class['class_position'] = 0
    data_keys_class_dict = data_keys_class.to_dict('records')
    for i in range(0, len(data_w_filters_sorted_hour)):
        x = data_w_filters_sorted_hour.iloc[i]
        increment_position(x['key'], data_keys_dict)
        increment_class_position(x['key_class'], data_keys_class_dict)
        data_w_filters_sorted_hour.at[i, 'position'] = search_key_in_dicts(x['key'], data_keys_dict).get('position')
        data_w_filters_sorted_hour.at[i, 'class_position'] = search_key_in_dicts(x['key_class'], data_keys_class_dict).get('class_position')
    print(data_w_filters_sorted_hour)
main()