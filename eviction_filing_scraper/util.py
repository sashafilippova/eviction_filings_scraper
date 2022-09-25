# imports
from selenium import webdriver
from selenium.webdriver.support.ui import Select    # for drop-down menu
from selenium.webdriver.support.ui import WebDriverWait       
from selenium.webdriver.common.by import By       
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.chrome.service import Service    
  
from fake_useragent import UserAgent
import time
from datetime import datetime as dt, timedelta as tdelta
import pandas as pd
import numpy as np
import math
import logging

logging.basicConfig(level=logging.INFO, filename='testing_update_records.log')

_EVICTION_CASES = {
                "CASE NUMBER": [], "COURT": [], "CASE CAPTION": [], "JUDGE": [], 
                "FILED DATE": [], "CASE TYPE": [], "AMOUNT": [], "DISPOSITION": [], 
                "plaintiff_name": [], "plaintiff_address": [], "defendant_attorney": [],
                "defendant_name": [], "defendant_address": [], "plaintiff_attorney": []}

_KEYS_LIST = [key for key in _EVICTION_CASES.keys()]

_WEBDRIVER_LOCATION = r"/Users/oleksandrafilippova/Downloads/chromedriver"


############# Eviction Scraper Class ####################
class Eviction_Scraper:
    
    def __init__(self):
        """
        Class to scrape court eviction filing records in Hamilton county, Ohio. 
        """
        self.eviction_cases = _EVICTION_CASES.copy()
        self.cases_with_issues = []


    def run_scraper(self, start_date, end_date):
        """
        Scrapes eviction court cases from the Hamilton County
        Clerk of Courts website, using "Selenium" package: 
        https://www.courtclerk.org/records-search/municipal-civil-listing-by-classification/.

        Inputs:
          start_date (str): must follow format 'mmddyyyy'
          end_date (str): must follow format 'mmddyyyy'
        
        Returns pandas dataframe.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.lst_time_periods = date_converter(self.start_date, self.end_date)


        self.driver, self.wait = initiate_driver(_WEBDRIVER_LOCATION)
        self.driver.get(
            "https://www.courtclerk.org/records-search/municipal-civil-listing-by-classification/")

        for start, end in self.lst_time_periods:
            try:
                self.__process_search_webpage(start, end)
                self.__scrape_one_period()
                logging.info(f'Finished scraping period between {start}-{end}')

            except TimeoutException:
                logging.info('entering timeout exception. Qutting & re-initiating the driver')
                self.driver.quit()
                self.driver, self.wait = initiate_driver(_WEBDRIVER_LOCATION)
                self.driver.get(
                    "https://www.courtclerk.org/records-search/municipal-civil-listing-by-classification/")

                self.__process_search_webpage(start, end)
                self.__scrape_one_period()
                logging.info(f'Finished scraping period between {start}-{end} (from second try)')
            except:
                logging.info(f"Unknown Exception- unable to finish scraping for the entire period. \
                    Finished scraping before {start} date.")
                break

            self.driver.back()
            self.driver.delete_all_cookies()

        self.driver.quit()
        return normalize_data(self.eviction_cases)


    def __scrape_one_period(self):

        try:
            # Show all records on one page 
            self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[1]/div[3]/button"))).click()
        except TimeoutException:
            print('Did not find the "show all rows" button. No records are probably present')

        records_xpath_list = self.driver.find_elements('xpath', "//td[5]/form")
        print(f'found {len(records_xpath_list)} records')

        if len(records_xpath_list) > 0:
            search_tab_handle = self.driver.current_window_handle
            self.local_records = {key: [None] * len(records_xpath_list) for key in _KEYS_LIST}

            for i, record in enumerate(records_xpath_list): 
                self.wait.until(EC.element_to_be_clickable(record)).click()
                # switch focus to the newly open tab to scrape data
                self.driver.switch_to.window(self.driver.window_handles[1])
                start_time = time.time()
                
                try:
                    summary_case_dict, party_info_dict = scrape_one_case(self.driver, self.wait)

                    for key, val in summary_case_dict.items():
                        if key in self.local_records:
                            self.local_records[key][i] = val                  
                    for key, val in party_info_dict.items():
                        self.local_records[key][i] = val 

                except ValueError:
                    logging.info('something went wrong- entering ValueError except statement')
                    case = self.wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[1]/table/tbody/tr[1]/td[1]/div[3]/table/tbody/tr[1]/td[2]')))
                    logging.info('scrapped case_id successfuly')
                    self.cases_with_issues.append(case.text)

                time.sleep(3)
                #print(f"It took to scrape this page {time.time() - start_time} ({i} out of {len(records_xpath_list)}) to run.")
                self.driver.close()
                self.driver.switch_to.window(search_tab_handle)
            
            logging.info(f'Scraped {len(records_xpath_list)} records.')

            #add records to the main eviction file
            for key, value in self.local_records.items():
                    self.eviction_cases[key] += value 


    def __process_search_webpage(self, start, end):
        """
        Processes search webpage by filling it out with classification code,
        start & end date periods to query the court website.

        Inputs:
          start (str): start date following format 'mm/dd/yyyy'
          end (str): end date following format 'mm/dd/yyyy'
        """
        Select(self.driver.find_element("name", "ccode")).select_by_value("G")

        beg_date = self.driver.find_element('name', 'begdate')
        final_date = self.driver.find_element('name','enddate')

        beg_date.clear()
        beg_date.send_keys(start)
        final_date.clear()
        final_date.send_keys(end)

        self.wait.until(EC.element_to_be_clickable((By.XPATH, 
            '//*[@id="cc_frm"]/input[3]'))).click()

        try:
            WebDriverWait(self.driver, 3).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert

            if "Date range cannot be greater than 7 days" in alert.text:
                print('issue with date range')
                alert.accept()

                # add original start date to the list to be processed in the end 
                self.lst_time_periods.append([start, start])    

                # replace beginning date with next date
                beg_date.clear()
                start_date = dt.strptime(start, "%m/%d/%Y").date() + tdelta(days = 1)
                start_date = start_date.strftime("%m/%d/%Y")
                beg_date.send_keys(start_date)
                
                self.wait.until(EC.element_to_be_clickable((By.XPATH, 
                    '//*[@id="cc_frm"]/input[3]'))).click()
            else:
                print('uknown alert')

        except TimeoutException:
            pass


    def scrape_cases_by_id(self, lst_case_ids, check_only_disposition = True):   
        """
        Scrapes case info for a provided list of case ids.

        Inputs:
          lst_case_ids (lst): a list of case ids where each id is a string.

        Returns dict
        """
        scraped_eviction_cases = {key: [None] * len(lst_case_ids) for key in _KEYS_LIST}
        self.driver.get("https://www.courtclerk.org/records-search/case-number-search/")

        for idx, case_id in enumerate(lst_case_ids):

            try:
                # enter case_id on the search page

                case_id_field = self.driver.find_element('name', 'casenumber')
                case_id_field.clear()
                case_id_field.send_keys(case_id)    

                # find search button and click on it
                self.driver.find_element('xpath', '//*[@id="cc_frm"]/p/input[3]').click()
                
                if check_only_disposition:
                    scraped_eviction_cases["CASE NUMBER"][idx] = case_id
                    disposition_tag = self.driver.find_element('xpath', '//*[@id="case_summary_table"]/tbody/tr[8]') 
                    disposition_string = disposition_tag.text.upper()            
                    if 'DISPOSITION' in disposition_string:
                        _, disposition_value = disposition_string.split(":", 1)
                        scraped_eviction_cases["DISPOSITION"][idx] = disposition_value.strip()

                else:
                    summary_case_dict, party_info_dict = scrape_one_case(self.driver, self.explicit_wait)
                    case_dict = summary_case_dict.update(party_info_dict)
                    for key, val in case_dict.items():
                        if key in scraped_eviction_cases:
                            scraped_eviction_cases[key][idx] = val       

                logging.info(f'Finished the try statement successfully for case {idx} out of {len(lst_case_ids)}')           
                
            except TimeoutError:
                logging.info('entering timeout exception. Qutting & re-initiating the driver')
                self.driver.quit()
                self.driver, self.wait = initiate_driver(_WEBDRIVER_LOCATION)
                self.driver.get("https://www.courtclerk.org/records-search/case-number-search/")

                # enter case_id on the search page
                case_id_field = self.driver.find_element('name', 'casenumber')
                case_id_field.clear()
                case_id_field.send_keys(id)
    
                # find search button and click on it
                self.driver.find_element('xpath', '/html/body/div[1]/div/div[2]/form/p/input[4]').click()
        
                summary_case_dict, party_info_dict = scrape_one_case(self.driver, self.explicit_wait)
                case_dict = summary_case_dict.update(party_info_dict)
                for key, val in case_dict.items():
                    if key in scraped_eviction_cases:
                        scraped_eviction_cases[key][idx] = val

            except NoSuchElementException:
                logging.info('No disposition present')
                pass
            except:
                logging.info('Something went wrong. Stopping scraping.')
                break 
            
            time.sleep(3)
            self.driver.back()  

        logging.info('scraped_eviction_cases_dict is: ', scraped_eviction_cases)      

        return scraped_eviction_cases          

    
    def __enter__(self): 
        self.driver, self.explicit_wait = initiate_driver(_WEBDRIVER_LOCATION)
        return self  


    def __exit__(self, type, value, traceback): 
        self.driver.quit()

#########################################################

def initiate_driver(webdriver_location):
    """
    Initiates Chrome webdriver.

    Inputs: 
      webdriver_location (str): a path to Chrome webdriver location.

    Returns webriver & explicit wait object
    """

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-proxy-server")
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")                
        
    ua = UserAgent()
    userAgent = ua.random
    chrome_options.add_argument(f'--user-agent={userAgent}')

    s = Service(webdriver_location)
    driver = webdriver.Chrome(service=s, options=chrome_options)

    explicit_wait = WebDriverWait(driver, 50)
    driver.implicitly_wait(20)
    driver.maximize_window()

    return driver, explicit_wait


def date_converter(start_date, end_date, max_period = 7):
    """
    The court website limits search of records to up to 7 days. This function
    breaks a given time period into several, smaller time periods containing up to max_period days.

    Inputs:
      start_date (str): format should be mmddyyyy
      end_date (str): format should be mmddyyyy

    Returns a list of lists where each inner list has 2 strings (start & end date). 
      Ex: [['01/01/2020', '01/08/2020'], ['01/09/2020', '01/17/2020']] 
    """
    start_date = dt.strptime(start_date,"%m%d%Y").date()
    end_date = dt.strptime(end_date, "%m%d%Y").date()

    assert start_date <= end_date, 'Start Date is greater than End Date. Try again'
    assert end_date <= dt.today().date(), "End Date is greater than today's date. Try again"

    number_batches = math.ceil((end_date  - start_date).days / max_period)
    lst_periods = list()

    for _ in range(number_batches + 1):
        end = start_date + tdelta(days = max_period)

        if end >= end_date:
            lst_periods.append([start_date.strftime("%m/%d/%Y"), end_date.strftime("%m/%d/%Y")])
            break
        else:
            lst_periods.append([start_date.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y")])
            start_date = end + tdelta(days = 1)
            
    return lst_periods  


def scrape_one_case(driver, explicit_wait):
    """
    Scrapes one court case from a given page webdriver is currently on. 

    Returns dict with scraped info for one case
    """
    # open parties table with plaintiff and defendant info
    explicit_wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/table/tbody/tr[1]/td[2]/form[4]/input[3]'))).click()
            
    # get a list of all rows containing data to be scraped 
    case_summary_table_rows = driver.find_elements('xpath', '//*[@id="case_summary_table"]/tbody/tr')
    party_info_table_rows = driver.find_elements('xpath', '//*[@id="party_info_table"]/tbody/tr')
            
    # process case summary table & party contact info table rows 
    summary_case_dict = extract_summary_case_data(case_summary_table_rows)
    party_info_dict = extract_party_info_data(party_info_table_rows)

    return summary_case_dict, party_info_dict


def extract_summary_case_data(case_summary_table_rows):
    """
    Takes in a list of case summary tags, unpacks them and returns a dictionary with 
      case summary info.  

    Inputs:
    case_summary_table_rows (lst): list of case_summary_table tags 
      where each tag represents one row.

    Returns (dict) with case summary.
    """
    case_summary_dict = dict()

    for row in case_summary_table_rows: 
        # convert tag into string, apply upper case, and split string by ":"
        # example of row is 'CASE NUMBER: A1111111'
        field_name, field_value = row.text.upper().split(":", 1)
        case_summary_dict[field_name.strip()] = field_value.strip()

    return case_summary_dict


def extract_party_info_data(party_info_table_rows):
    """
    Takes in a list of party contact info table tags, unpacks them 
    and returns a dictionary with the processed info.  

    Inputs:
    party_info_table_rows (lst): list of party_info_table tags 
      where each tag represents one column.
    
    Returns (dict) with case parties info.
    """
    num_parties = 0
    party_info_dict = dict()

    for row in party_info_table_rows:
        # put row fields in a list row_fields
        row_fields = [val.text.replace('\n', '') for val in row.find_elements('xpath', '*')]

        if len(row_fields) >= 3:               
            party = row_fields[2]            
            if party == 'P 1':
                party_info_dict["plaintiff_name"] = row_fields[0]
                party_info_dict["plaintiff_address"] = row_fields[1]
                
                # check whether plaintiff has attorney
                if len(row_fields) >= 4:
                    party_info_dict["plaintiff_attorney"] = row_fields[3]

            elif party == 'D 1' or ('D' in party and num_parties < 1):
                num_parties += 1
                party_info_dict["defendant_name"] = row_fields[0]
                party_info_dict["defendant_address"] = row_fields[1]

                # check whether defendant has an attorney
                if len(row_fields) >= 4:
                    party_info_dict["defendant_attorney"] = row_fields[3]
        
    return party_info_dict


def normalize_data(dict_w_scraped_cases):
    """
    Converts data from dictionary into a pandas dataframe. Cleans & normalizes the data.

    Inputs:
      dict_w_scraped_cases (dict): a dictionary containing scraped cases.

    Returns pandas df
    """
    df  = pd.DataFrame(dict_w_scraped_cases) 

    df.rename(columns={"CASE NUMBER":"case_id", "COURT":"court", "CASE CAPTION": "case_caption",
            "JUDGE":"judge", "FILED DATE": "filed_date", "CASE TYPE": "case_type", "AMOUNT": "amount",
            "DISPOSITION": "disposition"}, inplace=True)

    df = df.drop_duplicates()
    df = df.dropna(subset=['case_id']) 

    df = df.replace(r'^\s*$', None, regex=True)
    df = df.replace({np.nan: None})   

    df['amount'] = round(pd.to_numeric(df['amount'], errors= 'coerce'))
    df['filed_date'] = pd.to_datetime(df['filed_date']).dt.date
    df['last_updated'] = dt.today().date()

    # checks whether all values in the disposition column are 'None'
    if df.disposition.isnull().all():
        df['disposition_date'] = None
    else:
        df[['disposition_date', 'disposition']] = df['disposition'].str.split(' - ', n=1, expand=True)

    return df