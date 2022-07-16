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

base_url = "http://fiawec.alkamelsystems.com/"
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

def get_championship_folder_elements_id(driver, file_name_to_look_for, championship):
    t_elements = driver.find_elements_by_class_name("t")
    championship_id = ""
    for index in range(0, len(t_elements)):
        if(championship == "FIA WEC"):
            if("FIA WEC" in t_elements[index].text or "24 HEURES DU MANS" in t_elements[index].text):
                #we have to add son to the element
                championship_id = t_elements[index].get_attribute('id') + "son"
                break
    folder_elements = ""
    try:
        folder_elements = driver.find_element_by_id(championship_id).find_elements_by_class_name("t")
    except NoSuchElementException:
        print("The championship is not in the pages.")
        return
    race_id = ""
    for index in range(0, len(folder_elements)):
        if(folder_elements[index].text.strip() == file_name_to_look_for.upper()):
            #we have to add son to the element
            race_id = folder_elements[index].get_attribute('id') + "son"
            break
    return race_id

def get_file_path_for_other_session(driver, file_name_to_look_for, championship):
    #here we look through the Ts to grab where the FIA WEC folder is
    race_id = get_championship_folder_elements_id(driver, file_name_to_look_for, championship)
    #all things have 23_Analysis_ + the file name to look for, but we probably want to make sure we're looking for the right thing
    file_path = ""
    element = -1
    try:
        while "23_Analysis" not in file_path:
            results_id = driver.find_element_by_id(race_id).find_elements_by_class_name("t")[element].get_attribute('id')
            result_elements = driver.find_elements_by_id(results_id)
            print(result_elements)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
                file_path = csv_elements[0].get_attribute('href')
                if "23_Analysis" in file_path:
                    if ".CSV" in file_path:
                        print(file_path)
                        return file_path
            element = element - 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException:
        print ("Element not found.")
    except TypeError:
        print ("Element not found.")
    return file_path

#deprecated, not needed anymore
def get_file_path_for_race(driver):
    #here we look through the Ts to grab where the FIA WEC folder is
    race_id = get_championship_folder_elements_id(driver, 'FIA WEC', 'RACE')
    file_path = ""
    element = -1
    try:
        #probably don't need this anymore and can use the above func
        while '.CSV' not in file_path:
            results_id = driver.find_element_by_id(race_id).find_elements_by_class_name("folder")[element].get_attribute('id')
            result_elements = driver.find_elements_by_id(results_id)
            print(result_elements)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if '23_Analysis_Race' in file_path :
                    if '.CSV' in file_path:
                        return file_path
            element = element - 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException:
        print ("Element not found.")
    except TypeError:
        print ("Element not found.")
    return file_path

def pull_and_save_csvs(driver, season_option, event_option, championship, round):
    print(event_option.text)
    print(season_option.text)
    #selectors based on the event + what we want to pull. this is only specific to FIA WEC. would have to look at the other things stored here to grab the data.
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
    print(session_types)
    for k in session_types:
        df = pd.DataFrame()
        try:
            df = pd.read_csv(get_file_path_for_other_session(driver, k, championship), delimiter = ";")
        except FileNotFoundError:
            print("File name not found, likely FIA WEC row doesn't exist!")
            continue
        except TypeError:
            print("File name not found, likely FIA WEC row doesn't exist!")
            continue
        except UnicodeDecodeError:
            print("Pulled a pdf by accident since the row pulled doesn't exist.")
            continue
        #add the wec season and circuit to the data, for later. 
        df['championship'] = 'FIA WEC'
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

def main():
    driver = initialize_driver()
    driver.get(base_url)
    #pull the season selectors
    season_selector = Select(driver.find_element_by_name("season"))
    season_options = season_selector.options
    #pull the event selectors
    for i in range(10, len(season_options)):
        season_selector.select_by_index(i)
        try:
            event_selector = Select(driver.find_element_by_name("evvent"))
            event_options = event_selector.options
            #loops through the events
            for j in range (3, len(event_options)):
                #pull the event
                event_selector.select_by_index(j)
                #we get into race conditions if we don't update the elements here, so we pull them before we load
                event_selector = Select(driver.find_element_by_name("evvent"))
                event_options = event_selector.options
                season_selector = Select(driver.find_element_by_name("season"))
                season_options = season_selector.options
                #obtain the csv and save it to a df. 
                pull_and_save_csvs(driver, season_options[i], event_options[j], "FIA WEC", j)
                #not really sure if this wait does anything...
                driver.implicitly_wait(2)
        except TimeoutException:
            print ("Loading took too much time?...")
    driver.close()
main()