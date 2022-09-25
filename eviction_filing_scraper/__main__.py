import sys
from util import Eviction_Scraper

if __name__ == '__main__':

    if len(sys.argv) == 4:        # create brand new csv file with scraped records between start-end dates
        new_csv_file_path = sys.argv[1]
        start_date = sys.argv[2]
        end_date = sys.argv[3]
        df = Eviction_Scraper().run_scraper(start_date, end_date)
        df.to_csv(new_csv_file_path, index=False)

    else:
        print("Incorrect number of arguments. Try again")
