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

df['Date']   = [e.date() for e in raw_data.Timestamp]
df['Time']   = [e.time() for e in raw_data.Timestamp]
df['Season'] = ['Cold' if e.month in COLD_MONTHS else 'Warm' for e in df.Date]
df['Data']   = raw_data[[station+'25']]  # hard-coded --> only PM2.5 now

df = df[df.Data.notnull()]

collections = [
        df,
        df[df.Season == 'Warm'],
        df[df.Season == 'Cold']
    ]
for i, collection in enumerate(collections, 1):

    days = collection.groupby('Date')

    means = sorted(days.get_group(d).Data.mean() for d in days.groups)

    plt.subplot('31{}'.format(i))
    plt.style.use('seaborn-pastel')

    plt.xlim([0, len(means)])
    plt.ylim([0, 300])

    plt.bar(range(len(means)), means, linewidth=0, color='#e8fb93')

    plt.hlines(25, *plt.xlim(), colors=['#ff5c64'])

    x_ticks_pos = [len(means) * e for e in [0.25,0.5,0.75]]
    plt.vlines(x_ticks_pos, *plt.xlim(), colors=['#dddddd'])
    plt.xticks(x_ticks_pos, ['25%', '50%', '75%'])

plt.show()

