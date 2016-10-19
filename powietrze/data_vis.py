# coding: utf-8

import pandas as pd
import sys

from matplotlib import pyplot as plt
from datetime   import date, time

COLD_MONTHS = [1, 2, 3, 10, 11, 12]

try:
    station = sys.argv[1].upper()
    if station not in 'KW':
        raise Exception('Unsupported option.')
except Exception:
    print("Select one of two data sources:")
    print("  w - ul. Wiśniowa")
    print("  k - ul. Korzeniowskiego\n")
    print("Run script as:")
    print("python data_vis.py [w|k]")
    sys.exit(1)

raw_data = pd.read_excel('Wroclaw_PM10_PM2.5.xlsx', skiprows=[0,1])
raw_data.columns = ['Timestamp', 'K10', 'K25', 'W25']

df = pd.DataFrame()

df['Date']     = [e.date() for e in raw_data.Timestamp]
df['Time']     = [e.time() for e in raw_data.Timestamp]
df['Season']   = ['Cold' if e.month in COLD_MONTHS else 'Warm' for e in df.Date]
df['DayNight'] = ['Day' if time(5) < e < time(20) else 'Night' for e in df.Time]
df['Data']     = raw_data[[station+'25']]  # hard-coded --> only PM2.5 now

df = df[df.Data.notnull()]

seasons = df.groupby(['Season', 'DayNight'])
for i, group in enumerate(seasons.groups, 1):

    pm25 = seasons.get_group(group).Data

    plt.subplot('22{}'.format(i))

    plt.style.use('seaborn-pastel')
    plt.ylim([0, df.Data.max()])
    plt.ylabel('Poziom pyłu zawieszonego PM2.5')
    plt.xlim([0, len(pm25)])
    plt.xlabel('Wyniki wszystkich pomiarow w sezonie')
    plt.title('Poziom PM2.5 w sezonie {} {}'.format(*group))

    # mark the norm level
    plt.hlines(25, *plt.xlim(), colors=['#F17373'])
    plt.annotate('Norma', (10, 28), color='#F17373')

    # build quarter-based grid
    x_ticks_pos = [len(pm25) * e for e in [0.25,0.5,0.75]]
    plt.vlines(x_ticks_pos, *plt.xlim(), colors=['#dddddd'])
    plt.xticks(x_ticks_pos, ['25%', '50%', '75%'])

    # plot the data
    plt.plot(sorted(pm25), lw=2, color='k')

plt.show()
