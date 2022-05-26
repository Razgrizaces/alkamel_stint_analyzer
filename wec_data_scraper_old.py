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
    prefs = {"download.default_directory":"C:\\Users\\trist\\Documents\\coding\\wec_stint_analyzer\\imsa_data\\"}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome("dependencies\\chromedriver.exe", options=chrome_options)
    return driver

def find_element_id_by_t_class(t_elements, type):
    for index in range(0, len(t_elements)):
        if type == "WEC":
            if("FIA WEC" in t_elements[index].text or "24 HEURES DU MANS" in t_elements[index].text):
                #we have to add son to the element
                element_id = t_elements[index].get_attribute('id') + "son"
                return element_id
        elif type == "IMSA":
            if("IMSA WEATHERTECH SPORTSCAR CHAMPIONSHIP" in t_elements[index].text):
                #we have to add son to the element
                element_id = t_elements[index].get_attribute('id') + "son"
                return element_id
    return None

def get_file_path_for_race(driver, type):
    #here we look through the Ts to grab where the FIA WEC folder is
    t_elements = driver.find_elements_by_class_name("t")
    element_id = find_element_id_by_t_class(t_elements, type)
    
    if element_id == None:
        return None

    folder_elements = driver.find_element_by_id(element_id).find_elements_by_class_name("t")
    race_id = ""
    for index in range(0, len(folder_elements)):
        if(folder_elements[index].text.strip() == "RACE"):
            #we have to add son to the element
            race_id = folder_elements[index].get_attribute('id') + "son"

    file_path = ""
    element = 1
    print(race_id)
    try:
        print(driver.find_element_by_id(race_id).find_elements_by_class_name("folder"))
        #while '.CSV' not in file_path:
            #results_id = driver.find_element_by_id(race_id).find_elements_by_class_name("folder")
    except NoSuchElementException:
        print ("Element not found.")
    except TypeError:
        print ("Element not found.")
    return file_path

def loop_through_season_options(driver, type):
    season_selector = Select(driver.find_element_by_name("season"))
    season_options = season_selector.options
    #pull the event selectors
    for i in range(10, len(season_options)):
        season_selector.select_by_index(i)
        try:
            event_selector = Select(driver.find_element_by_name("evvent"))
            event_options = event_selector.options
            for j in range (0, len(event_options)):
                #obtain the csv and save it to a df. 
                    event_selector.select_by_index(j)
                    df = pd.DataFrame()
                    try:
                        df = pd.read_csv(get_file_path_for_race(driver, type), delimiter = ";")
                    except FileNotFoundError:
                        print("File name not found, likely FIA WEC row doesn't exist!")
                        continue
                    except TypeError:
                        print("File name not found, likely FIA WEC row doesn't exist!")
                        continue
                    except ValueError:
                        print("File name not found, likely FIA WEC row doesn't exist!")
                        continue
                    #have to call this wait here in order for the race condition to solve itself, otherwise we get an exception here
                    driver.implicitly_wait(1)
                    event_selector = Select(driver.find_element_by_name("evvent"))
                    event_options = event_selector.options
                    season_selector = Select(driver.find_element_by_name("season"))
                    season_options = season_selector.options

                    #add the wec season and circuit to the data, for later. 
                    df['season'] = season_options[i].text
                    df['circuit'] = event_options[j].text
                    df['round'] = j + 1
                    save_file_path = "data/" + season_options[i].text + "_" + event_options[j].text + ".csv"
                    save_file_path = save_file_path.replace(" ", "_")
                    try:
                        df.to_csv(save_file_path)
                    except FileNotFoundError:
                        print("File name not found, save not completed.")
            season_selector = Select(driver.find_element_by_name("season"))
            season_options = season_selector.options
        except TimeoutException:
            print ("Loading took too much time?...")
    driver.close()

def main():
    driver = initialize_driver()
    driver.get(base_url)
    #pull the season selectors
    loop_through_season_options(driver, "WEC")
main()