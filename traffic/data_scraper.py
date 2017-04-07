import json
import os
import time

from datetime import date, datetime, timedelta
from PIL import Image
from selenium import webdriver


def scrape_diagram_for(current_date, path, crossroad_number, browser):
    ''' Save a screenshot of the traffic diagram.

        :current_date: string or date object for which a diagram to scrape
        :path: a path to folder where a diagram should be saved
        :crossroad_number: internal ITS crossroad id
        :browser: a webdriver instance

        :return: a string with a path to saved png file
    '''
    # catch the diagram
    widget_id = 'lineChart{}{}'.format(crossroad_number, current_date)
    widget = browser.find_element_by_id(widget_id)

    # save it to disk
    png_path = os.path.join(path, '{}.png'.format(current_date))
    widget.screenshot(png_path)

    return png_path


def scrape_data_from(png_path):
    ''' Scrapes the data points values from the png diagram

        :png_path: a path to png diagram
    '''
    img = Image.open(png_path)
    pixels = img.load()

    # TODO move csv and png files into different locations 
    with open(png_path.replace('png', 'csv'), 'w') as csv:
        csv.write('time,value\n')
        # The data is read by going pixel by pixel from the top of the diagram
        # to the first occurence of the orange colour. This point is taken as
        # a value for a certain hour. Pixels are read in columns representing
        # time of the day on x axis, which in practice is every 17th column.
        #         
        # Data is available on the bitmap within the rectangle:
        # x: 65px -- 372px
        # y: 22px -- 252px
        # Timescale of the diagram is:
        # h: 5:00 -- 23:00
        x_min, x_max = 65, 372
        y_min, y_max = 22, 252
        column_offset = 17
        start_time = 5

        for h, x in enumerate(range(x_min, x_max, column_offset),  start_time):
            for y in range(y_min, y_max):
                r, g, b, a = pixels[x,y]
                # three classes of colors are used in the diagram:
                # - grays  --> r ~= g ~= b
                # - green  --> r == 141 g == 198 b ==  63
                # - orange --> r  > 200 g  > 100 b  < 100
                if r > 200 and g > 100 and b < 100:
                    # reading from the top a diagram drawn from the bottom, 
                    # so the value has to be flipped, i.e. 1.0 - value
                    value = 1.0 - ((y - y_min) / (y_max - y_min))
                    csv.write('{:02}:00,{:.2f}\n'.format(h, value))
                    # save the first encountered value and get to next hour
                    break


def how_many_days_to_scrape_for(crossroad_name):
    ''' Determines how many days of data (starting from yesterday) is missing 
        for given crossroad. If no data has been downloaded yet or the gap is
        greater than all history available on ITS site, take all that is 
        available, i.e. last 26 days starting from yestreday. 

        :crossroad_name: a string with a name of the crossroad

        :return: a number of days to be scraped
    '''
    whole_history = 26 # days
    try:
        last_file = sorted([fn for fn in os.listdir(crossroad_name) if fn.endswith('csv')]).pop()
        last_date = datetime.strptime(last_file[:10], '%Y-%m-%d').date()
        yesterday = date.today() - timedelta(days=1)

        date_range = (yesterday - last_date).days - 1 # as data starts from yesterday

    except FileNotFoundError:
        # no raw data folder for this crossroad yet
        # no files has been downloaded yet
        os.mkdir(crossroad_name)
        date_range = whole_history

    except IndexError:
        # no files has been downloaded yet
        date_range = whole_history

    return date_range


def scrape(crossroad):
    ''' Scrape new data for a given crossroad.

        :crossroad: a dict representing a single crossroad
    '''
    date_range = how_many_days_to_scrape_for(crossroad['name'])
    if date_range <= 0:
        return

    browser = webdriver.Firefox()
    browser.get(crossroad['url'])
    # give Flash widgets a few ticks to load the data
    time.sleep(3)

    # links to past data start two days before yesterday so for both yestreday
    # and day before yesterday data has to be scraped on an entry site of the 
    # given crossroad before going into history data
    for number_of_days in [1, 2]:
        diagram_date = date.today() - timedelta(days=number_of_days)
        fname = scrape_diagram_for(diagram_date, 
                                   crossroad['name'], crossroad['url'][-3:],
                                   browser)
        scrape_data_from(fname)

    past_links = [link.get_attribute('href').split(';')[0] for link in
                  browser.find_elements_by_partial_link_text('Statystyka z')]
    # download only missing dates starting from day before yesterday
    past_links = past_links[:date_range]

    for link in past_links:
        browser.get(link)
        time.sleep(3)

        # TODO document example of the link that is split here
        current_date = link.split('-z-')[-1][:10]
        fname = scrape_diagram_for(current_date,
                                   crossroad['name'], crossroad['url'][-3:],
                                   browser)
        scrape_data_from(fname)

    browser.quit()


if __name__ == '__main__':
    with open('sources.json', 'r', encoding='utf-8') as sources:
        crossroads = json.loads(sources.read())

    for crossroad in crossroads:
        print(">>> Scraping {}".format(crossroad['name']))
        scrape(crossroad)
