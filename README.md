# Stint Analyzer for FIA WEC Data

## Introduction - How did I get this data?
The data here I scraped myself from the alkamel systems website at fiawec.alkamelsystems.com using Selenium to scrape through the HTML to download all of the csv files for the 2012 to the 2022 seasons. This is located in wec_data_scraper.py and was how I got the old data. I was able to get race data, but qualifying data shouldn't be too much harder, I would have to just change the tags over from race to qualifying (might be added in another version)

## What is this data?
This data I have here contains all of the CSV files scraped from the website combined together into one neatly packaged file for use on [Kaggle](https://www.kaggle.com/datasets/tristenterracciano/fia-wec-lap-data-20122022). There's some stuff I'd like to fix on it, like making the size smaller and grouped into multiple CSV files so you don't have to load a 200+ MB file into Pandas every time. Working on it now (as of June 2022). Essentially, it contains the lap data by team, car, class, driver, circuit, season, etc. for the FIA WEC (World Endurance Championship). I added a lot of my own columns as I felt the data here didn't explain everything well enough.

## 
