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

def get_file_path_for_race(driver, file_name_to_look_for):
    #here we look through the Ts to grab where the FIA WEC folder is
    t_elements = driver.find_elements_by_class_name("t")
    fia_wec_id = ""
    for index in range(0, len(t_elements)):
        if("FIA WEC" in t_elements[index].text or "24 HEURES DU MANS" in t_elements[index].text):
            #we have to add son to the element
            fia_wec_id = t_elements[index].get_attribute('id') + "son"
            break

    folder_elements = driver.find_element_by_id(fia_wec_id).find_elements_by_class_name("t")
    race_id = ""
    for index in range(0, len(folder_elements)):
        if(folder_elements[index].text.strip() == "RACE"):
            #we have to add son to the element
            race_id = folder_elements[index].get_attribute('id') + "son"

    #print(race_id)

    file_path = ""
    element = -1
    try:
        while '.CSV' not in file_path:
            results_id = driver.find_element_by_id(race_id).find_elements_by_class_name("folder")[element].get_attribute('id')
            result_elements = driver.find_element_by_id(results_id).find_elements_by_class_name("t")
            print(results_id)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if '23_Analysis_Race' in file_path or '23_Analsysis_Race' in file_path:
                    if '.CSV' in file_path:
                        return file_path
            element = element - 1 #if it doesn't exist, check the previous one, (should only happen with lemans 2021)
    except NoSuchElementException:
        print ("Element not found.")
    except TypeError:
        print ("Element not found.")
    return file_path

def main():
    driver = initialize_driver()
    driver.get(base_url)
    #pull the season selectors
    season_selector = Select(driver.find_element_by_name("season"))
    season_options = season_selector.options
    #pull the event selectors
    for i in range(1, len(season_options)):
        season_selector.select_by_index(i)
        try:
            event_selector = Select(driver.find_element_by_name("evvent"))
            event_options = event_selector.options
            for j in range (0, len(event_options)):
                #obtain the csv and save it to a df. 
                    event_selector.select_by_index(j)
                    df = pd.DataFrame()
                    try:
                        df = pd.read_csv(get_file_path_for_race(driver, "Classification_Race_Hour"), delimiter = ";")
                    except FileNotFoundError:
                        print("File name not found, likely FIA WEC row doesn't exist!")
                        continue
                    except TypeError:
                        print("File name not found, likely FIA WEC row doesn't exist!")
                        continue
                    event_selector = Select(driver.find_element_by_name("evvent"))
                    event_options = event_selector.options
                    season_selector = Select(driver.find_element_by_name("season"))
                    season_options = season_selector.options
                    #have to call this wait here in order for the race condition to solve itself, otherwise we get an exception here
                    driver.implicitly_wait(2)
                    
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
main()