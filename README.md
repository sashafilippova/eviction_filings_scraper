# Court Eviction Filings Scraper

  In one of my work projects, we tried to estimate impact of federal rent assistance (ERA) program on eviction filing rates in Cincinnati, OH. 
The ERA program was launched in the begining of Covid-19 and it has been providing rent assistance dollars to qualifying renters in an effort to 
stabilize their financial situation and prevent evictions. So the hypothesis was that the ERA program should reduce eviction filings 
in the city. My team also wanted to see whether attorney representation for renters had a positive effect on the eviction case outcome. 

## Problem:
  I wasn't able to find a data source offering data that could be easily ingested and/or that had eviction filings at a granular level. For example, [the Eviction Lab at Princeton University](https://evictionlab.org/) has a vast data library on eviction filings across the US, but the data is already aggregated at a census tract level; the data also doesn't provide any information on the outcome of the eviction filings (i.e., whether the case resulted in eviction of a tenant). 
[The Hamilton County Clerk of Courts](https://www.courtclerk.org/) provides access to the records, but there is no API on the website that would allow extracting multiple records at once. Given these limitations, I decided to build my own webcrawler to scrape eviction filing records from the court website, so we would have the necessary data for the analyses.

## Requirements:
* **MacOS**
> the crawler was built on macOS and may not be properly working on Windows; during development, some website HTML tags differed between the two systems
* **Google Chrome**
* **Chromedriver** 
> Note, both Google Chrome & Chromedriver must be the same versions. I used Version 105. 



## Directory:
* **README.md**: this file
* **requirements.txt**: list of Python packages required to run the application
* **eviction_filing_scraper/**: application folder. See description of files & subfolders below:
  * **data/**: contains scraped eviction filing records (stored as a csv file) between Jan 2019-June 2022
  * **util.py**: contains Eviction_Scraper class & other helper functions to scrape data from the court website
  * **__main__.py**: entry point of the app

## Data: 
Scraped data can be found [here](https://github.com/sashafilippova/eviction_filings_scraper/tree/main/eviction_filing_scraper/data). The data is "raw": 
it hasn't been cleaned. If the fields are `None`, the website didn't have any info. For example, defendants in most cases don't have an attorney, so the field was left empty. 

## Next Steps: 
- [ ] build a REST API to automate the scraper & provide access to the data
- [ ] clean addresses and geocode them into longitude/latitude
