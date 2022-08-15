from codecs import charmap_decode
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

import pandas as pd
import numpy as np
import requests as req
import json

delay = 5 #seconds

def initialize_driver():
    #setting chrome options; note this uses chromedriver_81, use whatever driver you have
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--disable-extensions"); # disabling extensions
    chrome_options.add_argument("--disable-gpu"); # applicable to windows os only
    chrome_options.add_argument("--disable-dev-shm-usage"); # overcome limited resource problems
    chrome_options.add_argument("--no-sandbox");
    chrome_options.add_argument("--remote-debugging-port=9225");
    prefs = {"download.default_directory":"C:\\Users\\trist\\Documents\\coding\\wec_stint_analyzer\\data\\"}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome("dependencies\\chromedriver.exe", options=chrome_options)
    return driver

def get_single_race_id(driver, file_name_to_look_for, championship_id):
    folder_elements = ""
    try:
        folder_elements = driver.find_element_by_id(championship_id).find_elements_by_class_name("t")
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
            print(race_id)
            results_id = driver.find_element_by_id(race_id).find_elements_by_class_name("t")[element].get_attribute('id')
            result_elements = driver.find_elements_by_id(results_id)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if "23_Analysis" in file_path or "23_Time" in file_path:
                    if ".CSV" in file_path:
                        return file_path
            element = element + 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException or TypeError:
        print ("Element not found.")
    return file_path

#deprecated, not needed anymore
def get_file_path_for_race(driver):
    #here we look through the Ts to grab where the FIA WEC folder is
    championship_id = get_championship_folder_elements_id(driver, 'IMSA')
    file_path = ""
    element = -1
    try:
        #probably don't need this anymore and can use the above func
        while '.CSV' not in file_path:
            results_id = driver.find_element_by_id(championship_id).find_elements_by_class_name("folder")[element].get_attribute('id')
            result_elements = driver.find_elements_by_id(results_id)
            print(result_elements)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
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

#this is prob going to be deprecated 
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

def get_championship_folder_elements_id(driver, championship):
    t_elements = driver.find_elements_by_class_name("t")
    championship_id = ""
    for index in range(0, len(t_elements)):
        if(championship == "FIA WEC"):
            if("FIA WEC" in t_elements[index].text or "24 HEURES DU MANS" in t_elements[index].text):
                #we have to add son to the element
                championship_id = t_elements[index].get_attribute('id') + "son"
                break
        elif (championship == "IMSA"):
            if("WEATHERTECH SPORTSCAR CHAMPIONSHIP" in t_elements[index].text):
                championship_id = t_elements[index].get_attribute('id') + "son"
                break
        elif(championship == "ELMS"):
            if(" ELMS" == t_elements[index].text or "EUROPEAN LE MANS SERIES" in t_elements[index].text):
                championship_id = t_elements[index].get_attribute('id') + "son"
                break
    return championship_id

def get_base_url(championship):
    if(championship == "FIA WEC"):
        base_url = "http://fiawec.alkamelsystems.com/"  
    elif(championship == "IMSA"):
        base_url = "http://imsa.alkamelsystems.com/"
    elif(championship == "ELMS"):
        base_url = "http://elms.alkamelsystems.com/"
    elif(championship == "LeMansCup"):
        base_url = "http://lemanscup.alkamelsystems.com/"
    return base_url

def get_file_path_by_session_id(driver, session_id):
    #here we look through the Ts to grab where the file to look for is
    #all things have 23_Analysis_ + the file name to look for, but we probably want to make sure we're looking for the right thing
    file_path = ""
    element = 0
    try:
        while "23_Analysis" not in file_path or "23_Time" not in file_path:
            #this moves the element back 1, so cycling through different files in the folders
            #okay this is kinda interesting: might need to make a method for this 
            results_id = driver.find_element_by_id(session_id).find_elements_by_class_name("t")[element].get_attribute('id')
            result_elements = driver.find_elements_by_id(results_id)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if ("23_Analysis" in file_path or "23_Time" in file_path) and ".CSV" in file_path:
                    return file_path
            element = element + 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException or TypeError:
        print ("Element not found.")
        return
    except IndexError:
        print ("Element not found.")
        return
    return file_path

def pull_sessions_from_file_prefixes(driver, championship_id, championship, round, season_option, event_option):
    folder_elements = ""
    file_prefixes = ["SESSION", "QUALIFYING", "RACE", "PRACTICE", "WARM UP"]
    try:
        folder_elements = driver.find_element_by_id(championship_id).find_elements_by_class_name("t")
    except NoSuchElementException:
        print("The championship is not in the pages.")
        return
    session_id = ""
    for index in range(0, len(folder_elements)):
        #if the piece is in the element, we should look for it and pull the relevant session
        for i in file_prefixes:
            current_file_prefix = folder_elements[index].text.strip()
            if(i in current_file_prefix):
                session_id = folder_elements[index].get_attribute('id') + "son"
                print(current_file_prefix)
                if current_file_prefix == "RACEWAY":
                    break
                if 'RACE' in current_file_prefix:
                    session_elements = driver.find_element_by_id(session_id).find_elements_by_class_name('folder')
                    print(len(session_elements))
                    if(len(session_elements) > 2):
                        if(championship == "IMSA"):
                            print(season_option.text)
                            if(season_option.text == '2020' or season_option.text == '2021' or season_option.text == '2022'):
                                session_id = session_elements[-1].get_attribute('id')
                            else:
                                session_id = session_elements[-2].get_attribute('id')
                        else:
                            session_id = session_elements[-1].get_attribute('id')
                df = pd.DataFrame()
                try:
                    df = pd.read_csv(get_file_path_by_session_id(driver, session_id), delimiter = ";")
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
                #add the wec season and circuit to the data, for later. 
                df['championship'] = championship
                df['session_type'] = current_file_prefix
                df['season'] = season_option.text
                df['circuit'] = event_option.text
                df['round'] = round + 1
                save_file_path = "data/" + season_option.text + "_" + event_option.text + "_" + current_file_prefix +  ".csv"
                save_file_path = save_file_path.replace(" ", "_")
                print(save_file_path)
                try:
                    df.to_csv(save_file_path)
                except FileNotFoundError:
                    print("File name not found, save not completed.")
                
def loop_through_championship(driver, season_option, event_option, championship, round):
    print(event_option.text)
    print(season_option.text)
    #-son contains the folder, also is class folder
    #xx without son contains the name/container, is class t
    
    #this gets the championshipid from the folders
    championship_id = get_championship_folder_elements_id(driver, championship)
    #now we want to pull the sessions in the folder
    pull_sessions_from_file_prefixes(driver, championship_id, championship, round, season_option, event_option)
    
def main():
    driver = initialize_driver()
    championship = "IMSA"
    base_url = get_base_url(championship)
    driver.get(base_url)
    #pull the season selectors
    season_selector = Select(driver.find_element_by_name("season"))
    season_options = season_selector.options
    #pull the event selectors
    for i in range(4, len(season_options)):
        season_selector.select_by_index(i)
        try:
            event_selector = Select(driver.find_element_by_name("evvent"))
            event_options = event_selector.options
            #loops through the events
            for j in range (0, len(event_options)):
                #pull the event
                event_selector.select_by_index(j)
                #we get into race conditions if we don't update the elements here, so we pull them before we load
                event_selector = Select(driver.find_element_by_name("evvent"))
                event_options = event_selector.options
                season_selector = Select(driver.find_element_by_name("season"))
                season_options = season_selector.options
                #obtain the csv and save it to a df. 
                #pull_and_save_csvs(driver, season_options[i], event_options[j], championship, j)
                loop_through_championship(driver, season_options[i], event_options[j], championship, j)
                #not really sure if this wait does anything...
                driver.implicitly_wait(2)
        except TimeoutException:
            print ("Loading took too much time?...")
    driver.close()
main()