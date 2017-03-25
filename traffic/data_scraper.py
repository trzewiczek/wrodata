import io
import json
import os
import sys
import time

from datetime import date, datetime, timedelta
from PIL import Image
from selenium import webdriver

def scrape_diagram_for(current_date, browser, path, crossroad_number):
    # catch the diagram
    widget_id = 'lineChart{}{}'.format(crossroad_number, current_date)
    widget = browser.find_element_by_id(widget_id)

    # save it to disk
    png_path = os.path.join(path, '{}.png'.format(current_date))
    widget.screenshot(png_path)

    return png_path


def scrape_data_from(png_path):
    img = Image.open(png_path)
    pixels = img.load()

    with open(png_path.replace('png', 'csv'), 'w') as csv:
        csv.write('time,value\n')
        # Data is available within the rectangle:
        # x: 65 --> 372
        # y: 22 --> 252
        # Time scale of diagram is:
        # h:  5 --> 23
        for h, x in enumerate(range(65, 372, 17), 5):
            for y in range(22, 252):
                r, g, b, a = pixels[x,y]
                # three classes of colors are used in the diagram:
                # - grays  --> r ~= g ~= b
                # - green  --> r == 141 g == 198 b ==  63
                # - orange --> r  > 200 g  > 100 b  < 100
                if r > 200 and g > 100 and b < 100:
                    value = 1.0 - ((y - 22) / (252 - 22))
                    csv.write('{:02}:00,{:.2f}\n'.format(h, value))
                    # save the fisrt encountered value and get to next hour
                    break


def scrape(crossroad):
    try:
        last_file = sorted([fn for fn in os.listdir(crossroad['name']) if fn.endswith('csv')]).pop()
        last_date = datetime.strptime(last_file[:10], '%Y-%m-%d').date()
        yesterday = date.today() - timedelta(days=1)

        date_range = (yesterday - last_date).days
        # no new data available
        if not date_range:
            return 0

    except FileNotFoundError:
        # no raw data folder for this station
        # no files has been downloaded yet
        # download the whole history, i.e. 26 days
        os.mkdir(crossroad['name'])
        date_range = 27

    except IndexError:
        # no files has been downloaded yet
        # download the whole history, i.e. 26 days
        date_range = 27

    browser = webdriver.Firefox()
    browser.get(crossroad['url'])
    time.sleep(3)

    # links to past data start two days before yesterday
    # so yestreday has to be scraped before going to history data
    yesterday = date.today() - timedelta(days=1)
    fname = scrape_diagram_for(yesterday, browser,
                               crossroad['name'], crossroad['url'][-3:])
    scrape_data_from(fname)

    day_before = date.today() - timedelta(days=2)
    fname = scrape_diagram_for(day_before, browser,
                               crossroad['name'], crossroad['url'][-3:])
    scrape_data_from(fname)

    past_links = [link.get_attribute('href').split(';')[0] for link in
                  browser.find_elements_by_partial_link_text('Statystyka z')]
    # download only missing dates starting from day before yesterday
    past_links = past_links[:(date_range-1)]

    for link in past_links:
        browser.get(link)
        time.sleep(3)

        current_date = link.split('-z-')[-1][:10]
        fname = scrape_diagram_for(current_date, browser,
                                   crossroad['name'], crossroad['url'][-3:])
        scrape_data_from(fname)

    browser.quit()


if __name__ == '__main__':
    with open('sources.json', 'r', encoding='utf-8') as sources:
        crossroads = json.loads(sources.read())

    for crossroad in crossroads:
        print(">>> Scraping {}".format(crossroad['name']))
        scrape(crossroad)
