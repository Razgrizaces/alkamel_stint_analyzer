from codecs import charmap_decode
from unittest import result
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
import numpy as np
import requests as req
import json

delay = 5 #seconds

#likely deprecated
def get_file_path_for_other_session_with_file_name(driver, file_name_to_look_for, championship):
    #here we look through the Ts to grab where the file to look for is
    #all things have 23_Analysis_ + the file name to look for, but we probably want to make sure we're looking for the right thing
    file_path = ""
    element = 0
    championship_id = get_championship_folder_elements_id(driver, championship)
    race_id = get_single_race_id(driver, file_name_to_look_for, championship_id)
    try:
        while "23_Analysis" not in file_path or "23_Time" not in file_path:
            #this moves the element back 1, so cycling through different files in the folders
            #okay this is kinda interesting: might need to make a method for this 
            #print(race_id)
            results_id = driver.find_element(By.ID, race_id).find_elements(By.CLASS_NAME, "t")[element].get_attribute('id')
            result_elements = driver.find_elements(By.ID, results_id)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements(By.TAG_NAME, 'a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if "23_Analysis" in file_path or "23_Time" in file_path:
                    if ".CSV" in file_path:
                        return file_path
            element = element + 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException or TypeError:
        print ("Element not found.")
    return file_path

#this is prob going to be deprecated - it is
def grab_event_selectors(championship, season_option, event_option):
    if championship == 'FIA WEC':
        if event_option.text == "LE MANS":
            if(season_option.text == "2019-2020"):
                session_types = ["Free Practice","Qualifying Practice 1", "Qualifying Practice 2", "Qualifying Practice 3",\
                        "Qualifying LMGTE Pro & LMGTE Am", "Qualifying LMP1 & LMP2", "Hyperpole", "Warm Up"]
            elif(season_option.text == "2021" or season_option.text == "2022"):
                session_types = ["Free Practice 1", "Qualifying Practice", "Free Practice 2", "Free Practice 3", "Hyperpole", "Free Practice 4",  "Warm Up"]
            elif(season_option.text == "2013"):
                session_types = ["Free Practice", "Qualifying Practice 1", "Qualifying Practice 2", "Hyperpole", "Warm Up"]
            else:
                session_types = ["Free Practice", "Qualifying Practice 1", "Qualifying Practice 2", "Qualifying Practice 3", "Hyperpole", "Warm Up"]
        else:
            if(season_option.text == "2013" or season_option.text == "2014"):
                session_types = ["Free Practice 1", "Free Practice 2", "Free Practice 3", "Qualifying Practice"]
            elif(season_option.text == "2018-2019" or season_option.text == "2019-2020"):
                session_types = ["Free Practice 1", "Free Practice 2", "Free Practice 3", "Qualifying LMGTE Pro - LMGTE Am", "Qualifying LMP1 - LMP2"]
            elif(season_option.text == "2021" or season_option.text == "2022"):
                session_types = ["Free Practice 1", "Free Practice 2", "Free Practice 3", "Qualifying LMGTE Pro - LMGTE Am", "Qualifying HYPERCAR - LMP2", "Race"]
            else:
                session_types = ["Free Practice 1", "Free Practice 2", "Free Practice 3", "Qualifying LMGTE Pro & LMGTE Am", "Qualifying LMP1 & LMP2"]
    elif championship == 'IMSA':
        #session_types = ["Practice 1", "Practice 2","Practice 3","Practice 4", "Qualifying", "Warm-Up", "Race"]
        session_types = ["Race"]
    return session_types

#deprecated, not needed anymore
def get_file_path_for_race(driver):
    #here we look through the Ts to grab where the FIA WEC folder is
    championship_id = get_championship_folder_elements_id(driver, 'IMSA')
    file_path = ""
    element = -1
    try:
        #probably don't need this anymore and can use the above func
        while '.CSV' not in file_path:
            results_id = driver.find_element(By.ID, championship_id).find_elements(By.CLASS_NAME, "folder")[element].get_attribute('id')
            result_elements = driver.find_elements(By.ID, results_id)
            print(result_elements)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements(By.TAG_NAME, 'a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if "23_Analysis" in file_path or "23_Time" in file_path:
                    if '.CSV' in file_path:
                        return file_path
            element = element + 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException:
        print ("Element not found.")
    except TypeError:
        print ("Element not found.")
    return file_path

#this pulls csvs but it only does it if it has the session type built in, deprecated
def pull_and_save_csvs(driver, season_option, event_option, championship, round):
    print(event_option.text)
    print(season_option.text)
    #selectors based on the event + what we want to pull. this is only specific to FIA WEC. would have to look at the other things stored here to grab the data.
    session_types = grab_event_selectors(championship, season_option, event_option)
    for k in session_types:
        df = pd.DataFrame()
        try:
            df = pd.read_csv(get_file_path_for_other_session_with_file_name(driver, k, championship), delimiter = ";")
        except FileNotFoundError:
            print("File name not found, likely the championship row doesn't exist!")
            continue
        except UnicodeDecodeError:
            print("Pulled a pdf by accident since the row pulled doesn't exist.")
            continue
        except ValueError:
            print("Wrong File Pulled?...")
            continue
        except TypeError:
            print("Wrong File Pulled?...")
            continue
        #add the wec season and circuit to the data, for later. 
        df['championship'] = championship
        df['session_type'] = k
        df['season'] = season_option.text
        df['circuit'] = event_option.text
        df['round'] = round + 1
        save_file_path = "data/" + season_option.text + "_" + event_option.text + "_" + k +  ".csv"
        save_file_path = save_file_path.replace(" ", "_")
        try:
            df.to_csv(save_file_path)
        except FileNotFoundError:
            print("File name not found, save not completed.")

def initialize_driver():
    #setting chrome options; note this uses chromedriver_81, use whatever driver you have
    chrome_options = Options()
    """chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--disable-extensions"); # disabling extensions
    chrome_options.add_argument("--disable-gpu"); # applicable to windows os only
    chrome_options.add_argument("--disable-dev-shm-usage"); # overcome limited resource problems
    chrome_options.add_argument("--no-sandbox");
    chrome_options.add_argument("--remote-debugging-port=9225");"""
    prefs = {"download.default_directory":"C:\\Users\\trist\\Documents\\coding\\wec_stint_analyzer\\data\\"}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options = chrome_options)
    return driver

def get_single_race_id(driver, file_name_to_look_for, championship_id):
    folder_elements = ""
    try:
        folder_elements = driver.find_element(By.ID, championship_id).find_elements(By.CLASS_NAME, "t")
    except NoSuchElementException:
        print("The championship is not in the pages.")
        return
    race_id = ""
    for index in range(0, len(folder_elements)):
        if(folder_elements[index].text.strip() == file_name_to_look_for.upper()):
            #we have to add son to the element to get the files
            race_id = folder_elements[index].get_attribute('id') + "son"
            break
    return race_id

def get_championship_folder_elements(driver, championship):
    t_elements = driver.find_elements(By.CLASS_NAME, "t")
    championship_id = ""
    for index in range(0, len(t_elements)):
        #print(t_elements)
        if(championship == "FIAWEC"):
            if("TEST" not in t_elements[index].text):
                #print(t_elements[index].get_attribute('id'), "TEST" not in t_elements[index].text)
                if("FIA WEC" in t_elements[index].text or "24 HEURES DU MANS" in t_elements[index].text):
                    #we have to add son to the element
                    print(t_elements[index].get_attribute('id'))
                    championship_id = t_elements[index].get_attribute('id') + "son"
                #break
        elif (championship == "IMSA"):
            if("WEATHERTECH SPORTSCAR CHAMPIONSHIP" in t_elements[index].text):
                championship_id = t_elements[index].get_attribute('id') + "son"
                break
        elif(championship == "ELMS"):
            if("COLLECTIVE TEST DAY" not in t_elements[index].text):
                if("ELMS" in t_elements[index].text or "EUROPEAN LE MANS SERIES" in t_elements[index].text):
                    championship_id = t_elements[index].get_attribute('id') + "son"
                    break
        elif(championship == "LeMansCup"):
            if("ENTRY LIST" not in t_elements[index].text):
                if("LE MANS" in t_elements[index].text):
                    championship_id = t_elements[index].get_attribute('id') + "son"
                    break
    try:
        print(championship_id)
        folder_elements = driver.find_element(By.ID, championship_id).find_elements(By.CLASS_NAME, "t")
    except NoSuchElementException:
        print("The championship is not in the pages.")
        return None
    return folder_elements

def get_base_url(championship):
    if(championship == "FIAWEC"):
        base_url = "http://fiawec.alkamelsystems.com/"  
    elif(championship == "IMSA"):
        base_url = "http://imsa.alkamelsystems.com/"
    elif(championship == "ELMS"):
        base_url = "http://elms.alkamelsystems.com/"
    elif(championship == "LeMansCup"):
        base_url = "http://lemanscup.alkamelsystems.com/"
    return base_url

def get_file_path_by_session_id(driver, session_id, file_type):
    #here we look through the Ts to grab where the file to look for is
    #all things have 23_Analysis_ + the file name to look for, but we probably want to make sure we're looking for the right thing
    file_path = ""
    element = 0
    try:
        if(file_type == 'analysis'):
            while "23_Analysis" not in file_path or "23_Time" not in file_path:
                #this moves the element back 1, so cycling through different files in the folders
                #okay this is kinda interesting: might need to make a method for this 
                #fuji 2012 edge case, don't ask why'
                if(session_id =='jtz193son'):
                    csv_element = driver.find_element(By.ID, 'jtz1115').find_elements(By.TAG_NAME, 'a')
                    file_path = csv_element[0].get_attribute('href')
                    print(file_path)
                    return file_path
                else:
                    results_id = driver.find_element(By.ID, session_id).find_elements(By.CLASS_NAME, "t")[element].get_attribute('id')
                    result_elements = driver.find_elements(By.ID, results_id)
                for i in range(0, len(result_elements)):
                    csv_elements = result_elements[i].find_elements(By.TAG_NAME, 'a')
                    file_path = csv_elements[0].get_attribute('href')
                    print(file_path)
                    if ("23_Analysis" in file_path or "23_Time" in file_path or "23_Analsysis" in file_path) and ".CSV" in file_path:
                        if ".CSV" in file_path:
                            return file_path
                        else:
                            file_path = ""
                element = element + 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
        elif file_type == 'classification':
            while "Grid" not in file_path or "Classification" not in file_path or 'Results' in file_path:
                results_id = driver.find_element(By.ID, session_id).find_elements(By.CLASS_NAME, "t")[element].get_attribute('id') 
                result_elements = driver.find_elements(By.ID, results_id)
                print(results_id)
                for i in range(0, len(result_elements)):
                    csv_elements = result_elements[i].find_elements(By.TAG_NAME, 'a')
                    file_path = csv_elements[0].get_attribute('href')
                    print(file_path)
                    if "Classification" in file_path or 'Results' in file_path:
                        if ".CSV" in file_path:
                            return file_path
                        else:
                            file_path = ""
                element = element + 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException or TypeError:
        print ("Element not found.")
        return
    except IndexError:
        print ("Out of bounds. (Index)")
        return
    return file_path

def get_race_session_id(championship, season_option, session_elements, event_option):
    if(championship == "IMSA"):
        print(season_option.text)
        if(season_option.text == '2017' or season_option.text == '2018' or season_option.text == '2019'):
            session_id = session_elements[-2].get_attribute('id')
        else:
            session_id = session_elements[-1].get_attribute('id')
    elif (championship == "ELMS"):
        print(event_option.text)
        if(season_option.text == '2013'):
            session_id = session_elements[-2].get_attribute('id')
        else:
            if("IMOLA" in event_option.text or "SILVERSTONE" in event_option.text) and (season_option.text == "2014"):
                session_id = session_elements[-2].get_attribute('id')
            else:
                session_id = session_elements[-1].get_attribute('id')
    #edge case handling
    elif (championship == "FIAWEC"):
        if(season_option.text == '2012'):
            if("FUJI" in event_option.text):
                session_id = session_elements[-3].get_attribute('id')
            elif("SHANGHAI" in event_option.text):
                session_id = session_elements[-2].get_attribute('id')
            elif("SPA F" in event_option.text):
                session_id = session_elements[-1].get_attribute('id')
            else:
                session_id = session_elements[-1].get_attribute('id')
        elif(season_option.text == '2013'):
            session_id = session_elements[-2].get_attribute('id')
        elif(season_option.text == '2014'):
            if("CIRCUIT" in event_option.text or "FUJI" in event_option.text or "INTERLAGOS" in event_option.text):
                session_id = session_elements[-1].get_attribute('id')
            else:
                session_id = session_elements[-2].get_attribute('id')
        elif(season_option.text == '2015' or season_option.text == '2017' or season_option.text == '2021'):
            if("LE MANS" in event_option.text):
                session_id = session_elements[-2].get_attribute('id')
            else:
                session_id = session_elements[-1].get_attribute('id')
        else:
            session_id = session_elements[-1].get_attribute('id')
    else:
        session_id = session_elements[-1].get_attribute('id')
    return session_id

#this checks if we need to merge the dfs to get classification columns, true if we do, false if we don't
def check_merge_season(championship, index):
    if(championship == 'ELMS'):
        if(index < 10):
            return True
    elif(championship == 'FIAWEC'):
        if(index < 4):
            return True
    elif(championship == 'IMSA'):
        if(index < 6):
            return True
    elif(championship == 'LeMansCup'):
        return True
    return False

def pull_sessions_from_file_prefixes(driver, folder_elements, championship, season_year, season_option, event_option, round):
    file_prefixes = ["SESSION", "QUALIFYING", "RACE", "PRACTICE", "WARM UP"]
    session_id = ""
    for index in range(0, len(folder_elements)):
        #if the piece is in the element, we should look for it and pull the relevant session
        for i in file_prefixes:
            current_file_prefix = folder_elements[index].text.strip()
            if(i in current_file_prefix):
                session_id = folder_elements[index].get_attribute('id') + "son"
                #if race is in the prefix, but it's not the race folder, then we have to break
                if "RACEWAY" in current_file_prefix or "PRE-RACE" in current_file_prefix:
                    break
                if 'RACE' in current_file_prefix:
                    session_elements = driver.find_element(By.ID, session_id).find_elements(By.CLASS_NAME, 'folder')
                    if(len(session_elements) >= 2):
                        session_id = get_race_session_id(championship, season_option, session_elements, event_option)
                #this has to be changed
                #I think we just have to pull a lap_df
                try:
                    lap_df = pd.read_csv(get_file_path_by_session_id(driver, session_id, 'analysis'), delimiter = ";", dtype=str)
                    class_df = pd.read_csv(get_file_path_by_session_id(driver, session_id, 'classification'), delimiter = ";", dtype=str)
                except FileNotFoundError:
                    print("File name not found, likely the championship row doesn't exist!")
                    continue
                except UnicodeDecodeError:
                    print("Pulled a pdf by accident since the row pulled doesn't exist.")
                    continue
                except TypeError:
                    print("Wrong File Pulled?...")
                    continue
                except ValueError:
                    print("Wrong File Pulled?...")
                    continue
                #fix the columns of the dfs
                class_df.columns = class_df.columns.str.strip()
                class_df.columns = class_df.columns.str.lower()


                lap_df.columns = lap_df.columns.str.strip()
                lap_df.columns = lap_df.columns.str.lower()

                lap_df.replace('',pd.NA).dropna(how="all")

                #get the columns of the classifcation df we want
                if(check_merge_season(championship, season_year) == True):
                    class_wanted_columns = ['number', 'class', 'group', 'team', 'vehicle']
                else:
                    class_wanted_columns = ['number', 'vehicle']
                #print(class_df.columns)
                try:
                    class_df = class_df[class_wanted_columns]
                except: 
                    print("Column not in df, ok to merge.")
                    class_df['vehicle'] = class_df['car']
                    class_df = class_df[class_wanted_columns]

                df = lap_df
                if(check_merge_season(championship, season_year) == True):
                    lap_df_dup_columns = ['class', 'group', 'team']
                    try:
                        for c in lap_df_dup_columns:
                            df = df.drop(c, axis=1)
                    except:
                        print("Column not in df, ok to merge.")
                df = pd.merge(lap_df, class_df, on = 'number')
                #add the wec season and circuit to the data, for later. 
                df['championship'] = championship
                df['session_type'] = current_file_prefix
                #print(current_file_prefix)
                df['season'] = season_option.text
                df['circuit'] = event_option.text
                df['round'] = round
                #print(df.columns)
                save_file_path = "data/" + championship + "/" + season_option.text + "_" + event_option.text + "_" + current_file_prefix +  ".csv"
                save_file_path = save_file_path.replace(" ", "_")
                print(save_file_path)
                try:
                    df.to_csv(save_file_path)
                except FileNotFoundError:   
                    print("File name not found, save not completed.")

def main():
    driver = initialize_driver()
    championships = ['IMSA']
    for c in championships:
        base_url = get_base_url(c)
        driver.get(base_url)
        #pull the season selectors
        season_selector = Select(driver.find_element(By.NAME, "season"))
        season_options = season_selector.options
        #pull the event selectors
        if(c == 'ELMS'):
            s = 18
            r = 0
        elif(c == 'FIAWEC'):
            s = 11
            r = 0
        elif(c == 'IMSA'):
            s = 8
            r = 0
        elif(c == 'LeMansCup'):
            s = 6
            r = 0
        for i in range(s, len(season_options)):
            season_selector.select_by_index(i)
            try:
                event_selector = Select(driver.find_element(By.NAME, "evvent"))
                event_options = event_selector.options
                #loops through the events
                for j in range (r, len(event_options)):
                    #pull the event
                    event_selector.select_by_index(j)
                    #we get into race conditions if we don't update the elements here, so we pull them before we load
                    event_selector = Select(driver.find_element(By.NAME, "evvent"))
                    event_options = event_selector.options
                    season_selector = Select(driver.find_element(By.NAME, "season"))
                    season_options = season_selector.options

                    #get the folder elements
                    folder_elements = get_championship_folder_elements(driver, c)
                    #obtain the csv and save it to a df. 
                    if(folder_elements != None):
                        pull_sessions_from_file_prefixes(driver, folder_elements, c, s, season_options[i], event_options[j], j+1)
                    #not really sure if this wait does anything...
                    driver.implicitly_wait(2)
            except TimeoutException:
                print ("Loading took too much time?...")
    driver.close()
main()