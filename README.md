# Stint Analyzer for Alkamel Systems Data

## Introduction - How did I get this data?
The data here I scraped myself from the alkamel systems website from a few different domains based on the alkamel live timing systems. I've pulled almost every session based on the main championships. [FIA WEC](https://fiawec.alkamelsystems.com), [IMSA](https://imsa.alkamelsystems.com), [ELMS](https://elms.alkamelsystems.com) using Selenium to scrape through the HTML to download all of the csv files for the each of the season that contains CSVs This is located in wec_data_scraper.py and was how I got the old data. ~~I was able to get race data, but qualifying data shouldn't be too much harder, I would have to just change the tags over from race to qualifying (might be added in another version).~~ I was able to get qualifying, practice, test sessions and race data from the csvs. 

## What can you do with this data?
I created an interactive dashboard [here](http://alkamelanalyzer.razgrizaces.com/). I am currently actively working on it, please create an issue or a request if you would like me to add features or anything similar. I am aware that it does not work currently on mobile, since that is a limitation of the framework (Dash). I might look into adjusting or changing this later, but I am currently happy with how it is. I might work on qualifying and other session data, but in testing it doesn't show as nicely as I want so I have only put race data for the time being. 

### 
