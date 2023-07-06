import pandas as pd
from glob import glob
import uproot4 as uproot
from os.path import join
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplhep as hep
hep.style.use("CMS")

import matplotlib.dates as mdates

# get all the root files
file_list = glob("/home/nkarunar/hit_root_files/8997_*.root")
df_list = []

# loop over all the files
for file in file_list:
    tree = uproot.open(f'{file}:T')
    nentries = tree.num_entries
    print(nentries)
    tree.show()
    bx_temp = tree.arrays(["timesec", "bx"], library="pd")
    df_list.append(bx_temp)

bxt = pd.concat(df_list)

# convert timesec to datetime
bxt['newtime'] = pd.to_datetime(bxt['timesec'], unit='s')

# add 1 to bx
bxt['bx'] = bxt['bx'] + 1

bxt.sort_values(by=['timesec'], inplace=True)

bxt.to_csv("bx.csv", mode='w', index=False, header=False)
# bxt = pd.read_csv("bx.csv")

# plot bx vs time
date_format = mdates.DateFormatter('%H:%M:%S')
fig, ax = plt.subplots(figsize=(16, 30))
ax.plot(bxt['newtime'], bxt.bx, '.')
ax.xaxis.set_major_formatter(date_format)
fig.autofmt_xdate()
plt.ylim(1000, 1250)

# turn on minor ticks
ax.minorticks_on()

# set major and minor ticks
# ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
# ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
ax.yaxis.set_major_locator(plt.MultipleLocator(10))
ax.yaxis.set_minor_locator(plt.MultipleLocator(1))


# grid for major axis and minor axis on both x and y axis
ax.grid(which='major', axis='both', linestyle='-', linewidth='0.5', color='red')
ax.grid(which='minor', axis='both', linestyle=':', linewidth='0.5', color='black')

plt.savefig('Trigger_data.png', dpi=300)
plt.show()


# # histogram y range in multiple plots. each plot has a range 100
# plt.figure(figsize=(20, 20))

# for i in range(0, 10):
#     plt.subplot(5, 2, i+1)
#     plt.hist(bxt.bx, bins=3564, range=(i*100, (i+1)*100))
#     plt.xlabel("BX")
#     plt.ylabel("Number of events")
#     plt.xlim(i*100, (i+1)*100)
#     plt.yscale("log")