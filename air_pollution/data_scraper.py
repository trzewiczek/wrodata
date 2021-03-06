#!/usr/bin/env python

''' Scraper for Wrocław, Poland air pollution data collected by PIOŚ '''

import json
import os
import shutil
import sys
import time

from datetime import date, datetime, timedelta

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException


def download_csv_file(url, browser):
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
            vertical_offset = csv_link.location['y'] - half_the_browser
            browser.execute_script('window.scroll(0,{})'.format(vertical_offset))

            csv_link.click()

            return True
        except (WebDriverException, NoSuchElementException):
            trials += 1

    return False


def get_dates_for(station):
    ''' Prepare starting date and date range to be downloaded

        :station: a dict with station metadata
        :return: a tuple of starting date and date range to be downloaded
    '''
    try:
        # get the date for the most recent data available from the csv file name
        newest = sorted(os.listdir(station['name'])).pop()
        from_date = datetime.strptime(newest[:-4], '%Y-%m-%d').date() + timedelta(days=1)
    except FileNotFoundError:
        # no raw data folder for this station, i.e. no data collected yet
        os.mkdir(station['name'])
        from_date = datetime.strptime(station['begins'], '%Y-%m-%d').date()
    except IndexError:
        # or go till the begining of air monitoring, i.e. 2014-03-05
        from_date = datetime.strptime(station['begins'], '%Y-%m-%d').date()

    # to keep daily data consistant start from yesterday (won't affect monthly)
    yesterday = date.today() - timedelta(days=1)
    date_range = (yesterday - from_date).days + 1

    return from_date, date_range


def scrape(base_url, stations):
    ''' Scraper's entry point

        :base_url: common part of the stations urls
        :stations: list of dicts containing station information
    '''
    browser = webdriver.Chrome()

    for station in stations:
        from_date, date_range = get_dates_for(station)
        print('>>> Focusing on {}'.format(station['name']))
        print('>>> Last data available: {}'.format(from_date))

        visited_urls = set()
        for delta in range(date_range):
            current_date = from_date + timedelta(days=delta)

            url_date_format = '%d.%m.%Y' if station['period'] == 'daily' else '%m.%Y'
            url = base_url + station['url'] + current_date.strftime(url_date_format)

            if url in visited_urls:
                continue
            else:
                visited_urls.add(url)

            if not download_csv_file(url, browser):
                print('!!! Problem while processing {}'.format(current_date))
                continue

            time.sleep(2)
            downloads_folder = os.path.join(os.environ['HOME'], 'Downloads')
            fname = [f for f in os.listdir(downloads_folder) if f.startswith('dane')].pop()

            csv_date_format = '%Y-%m-%d' if station['period'] == 'daily' else '%Y-%m'
            data_file = '{}.csv'.format(current_date.strftime(csv_date_format))

            shutil.move(os.path.join(downloads_folder, fname),
                        os.path.join(station['name'], data_file))

    browser.quit()


if __name__ == '__main__':
    with open('sources.json', 'r', encoding='utf-8') as metadata:
        SOURCES = json.loads(metadata.read())

    sys.exit(scrape(**SOURCES))
