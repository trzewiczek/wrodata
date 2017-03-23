import os
import shutil
import time

from datetime import date, datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException


def scrape_data(url, browser):
    ''' Scrapes pollution data for a given url

        :url: data collection url
        :browser: a webdriver browser instance
        :return: boolean for success
    '''
    browser.get(url)

    # let's give it up to five seconds
    trials = 0
    while trials < 5:
        # wait for JavaScript to load the data
        time.sleep(1)
        try:
            csv_link = browser.find_element_by_link_text('CSV')
            # one can only click what is visible
            half_the_browser = browser.get_window_size()['height'] / 2
            vertical_offset  = csv_link.location['y'] - half_the_browser
            browser.execute_script('window.scroll(0,{})'.format(vertical_offset))

            csv_link.click()

            return True
        except (WebDriverException, NoSuchElementException):
            trials += 1

    return False


base_url = 'https://demo.dacsystem.pl/dane-pomiarowe/{}/{}'
stations = [
    {
        'name': 'bartnicza',
        'station': 'automatyczne/stacja/14/parametry/254-259-255-257/dzienny',
        'period': 'daily'
    },
    {
        'name': 'korzeniowskiego',
        'station': 'automatyczne/stacja/12/parametry/209-215-543-545-222-223-216-544-218/dzienny',
        'period': 'daily'
    },
    {
        'name': 'wisniowa',
        'station': 'automatyczne/stacja/13/parametry/241-245-242-238-244/dzienny',
        'period': 'daily'
    },
]

browser = webdriver.Chrome()

# to keep daily data consistant start from yesterday (won't affect monthly)
from_date = date.today() - timedelta(days=1)

for station in stations:
    try:
        # get the date for the most recent data available from the csv file name
        data_path = os.path.join('raw_data', 'air', station['name'])
        newest    = sorted(os.listdir(data_path)).pop()
        till_date = datetime.strptime(newest[:-4], '%Y-%m-%d').date()
    except FileNotFoundError:
        # no raw data folder for this station, i.e. no data collected yet
        os.mkdir(os.path.join('raw_data', 'air', station['name']))
        till_date = date(2017, 3, 4)
    except IndexError:
        # or go till the begining of air monitoring, i.e. 2014-03-05
        till_date = date(2017, 3, 4)


    date_range = (from_date - till_date).days
    print('>>> Focusing on {}'.format(station['name']))
    print('>>> Downloading data for {} days'.format(date_range))

    for delta in range(date_range):
        current_date = from_date - timedelta(days=delta)

        url_date_format = '%d.%m.%Y' if station['period'] == 'daily' else '%m.%Y'
        url = base_url.format(station['station'],
                              current_date.strftime(url_date_format))

        if not scrape_data(url, browser):
            print('!!! Problem while processing {}'.format(current_date))
            continue

        time.sleep(5)
        downloads_folder = os.path.join(os.environ['HOME'], 'Downloads')
        fname = [f for f in os.listdir(downloads_folder) if f.startswith('dane')].pop()
        data_file = '{}.csv'.format(current_date.strftime('%Y-%m-%d'))

        shutil.move(os.path.join(downloads_folder, fname),
                    os.path.join(station['name'], data_file))


browser.quit()
