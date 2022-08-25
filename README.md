# Stint Analyzer for Alkamel Systems Data

## Introduction - How did I get this data?
The data here I scraped myself from the alkamel systems website from a few different domains based on the alkamel live timing systems. I've pulled almost every session based on the main championships. [FIA WEC](https://fiawec.alkamelsystems.com), [IMSA](https://imsa.alkamelsystems.com), [ELMS](https://elms.alkamelsystems.com) using Selenium to scrape through the HTML to download all of the csv files for the each of the season that contains CSVs This is located in wec_data_scraper.py and was how I got the old data. ~~I was able to get race data, but qualifying data shouldn't be too much harder, I would have to just change the tags over from race to qualifying (might be added in another version).~~ I was able to get qualifying, practice, test sessions and race data from the csvs. I scraped over 1000 files from the website, and am planning on showing how I think that this data can be stored in a more efficient manner, still working on my pipelines. 

## What is this data?
This data I have here contains all of the CSV files scraped from the website combined together into one neatly packaged file for use on [Kaggle](https://www.kaggle.com/datasets/tristenterracciano/fia-wec-lap-data-20122022). There's some stuff I'd like to fix on it, like making the size smaller and grouped into multiple CSV files so you don't have to load a 200+ MB file into Pandas every time. Working on it now (as of June 2022). Essentially, it contains the lap data by team, car, class, driver, circuit, season, etc. for the FIA WEC (World Endurance Championship). I added a lot of my own columns as I felt the data here didn't explain everything well enough, like team_no, the position at the time of the lap, the gap and interval, etc.

## What can you do with this data?
There's quite a lot, what I did was cursory lap time plot analysis with the [Sebring 2022 data (first round of 2022)](https://www.kaggle.com/code/tristenterracciano/sebring-2022-lap-time-analysis). This might not be as comprehensive and doesn't show what I built into the data set. I will be working on an interactive dashboard that can show you the position over time of the cars and the lap plots per class. 

### (work in progress)
