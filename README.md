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

## Running the app locally:

#### 1. Clone this repo and cd into your local copy.

```
git clone https://github.com/sashafilippova/eviction_filings_scraper.git
cd eviction_filings_scraper
```

#### 2. Create & activate virtual envirenment, install dependencies:
```
python3 -m venv env 
source env/bin/activate
pip install -r requirements.txt
```

#### 3. Update the _WEBDRIVER_LOCATION variable in **util.py** file with the location of webdriver on your local machine (line 29 as shown below):
<img width="639" alt="image" src="https://user-images.githubusercontent.com/89982437/192162161-c48e1d12-bf03-47f1-8dbe-b8d52c38528a.png">

#### 4. Run scraper, using the following format: 
*python3 eviction_filing_scraper <file_name.csv> <start_date> <end_date>*

Where *<start_date>* & *<end_date>* must follow **mmddyyyy** format. 

For example, if we want to scrape records between August 1, 2022 - September 1, 2022 and save the result in the same repo named as test.csv, we would run 
the following command from the terminal: 
```
python3 eviction_filing_scraper 'test.csv' '08012022' '09012022'
```

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
- [ ] build a REST API to automate the scraper & provide access to the data (in progress)
- [ ] clean addresses and geocode them into longitude/latitude
