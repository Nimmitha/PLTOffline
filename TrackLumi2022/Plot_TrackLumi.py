import pathlib
import uproot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from glob import glob
import mplhep as hep
hep.style.use("CMS")

def pltChannelMap() -> pd.DataFrame:
    quadrants = pd.Series(['-zNear','-zFar','+zNear','+zFar']).repeat(12)
    flavor = pd.Series(['Calabrese','Diavola','Capricciosa','Margherita']).repeat(12)
    mFec = pd.Series(['8-1','8-2','7-1','7-2']).repeat(12)
    anaLV = pd.Series(f'PLT_1.8_H{q}' for q in ['mN','mF','pN','pF']).repeat(12)
    digLV = pd.Series(f'PLT_2.5_H{q}' for q in ['mN','mF','pN','pF']).repeat(12)
    HV = pd.Series(f'PLTHV_H{q}T{ch}' for q in ['mN','mF','pN','pF'] for ch in [*range(4)]).repeat(3)
    hub = pd.Series(4*['H05','H13','H21','H29']).repeat(3)
    roc = pd.Series(16*[0,1,2])
    roCh = pd.Series([*range(16)]).repeat(3)
    pixCh = pd.Series(sorted([*range(1,24)][::3] + [*range(1,24)][1::3])).repeat(3)
    fOrCh = pd.Series(f'{fed}-{fo}' for fed in [0,1] for i in [1,4,10,13,19,22,28,31] for fo in [*range(i,i+3)])
    data = zip(quadrants, flavor, mFec, anaLV, digLV, HV, hub, roCh, pixCh, roc, fOrCh)
    cols = ['quadrant','flavor','mFecCh','analogLV','digitalLV','HV','hub','readoutCh','pixFEDCh','roc','forFEDCh']
    return pd.DataFrame(data=data, columns=cols)

FEDtoReadOut = dict (zip( pltChannelMap()['pixFEDCh'], pltChannelMap()['readoutCh'] ))

interval = '1min'
#files = glob('D:/Cernbox/data/slink_data/slink_tracks/????.root')
files = glob("/home/nkarunar/root_files/????.root")
print(files)

for file in files:
    fill = int(pathlib.Path(file).stem)
    if fill <=  8132: # Already done. Remove later
        continue
    print(fill)
    
    tree = uproot.open(f"{file}:T")
    df = tree.arrays(['event_time', 'Channel'], library='pd')
    df['event_time'] = pd.to_datetime(df['event_time'])
    df.loc[:, 'Count'] = 1
    
    table = df.pivot_table(index='event_time', columns=['Channel'], values='Count', aggfunc=np.sum, fill_value=0)
    table.reset_index(inplace=True)
    table['event_time'] = table['event_time'].dt.round(interval)
    
    acu_table = table.groupby('event_time').sum().rename(columns=FEDtoReadOut)
    
    dfmt = mdates.DateFormatter("%H:%M")
    plt.figure(figsize=(16, 9))
    for ch in range(0, 8):
        plt.plot(acu_table.index, acu_table[ch], '.-', label=f'ch{ch}')
    plt.gca().xaxis.set_major_formatter(dfmt)
    plt.xticks(rotation=90)
    plt.xlabel('Time (UTC)')
    plt.ylabel("No. of Tracks")
    plt.legend(loc="lower left", ncol=4)
    plt.tight_layout()
    plt.savefig(f"output/{fill}_{interval}_M.png", dpi=600)
    plt.clf()

    plt.figure(figsize=(16, 9))
    for ch in range(8, 16):
        plt.plot(acu_table.index, acu_table[ch], '.-', label=f'ch{ch}')
    plt.gca().xaxis.set_major_formatter(dfmt)
    plt.xticks(rotation=90)
    plt.xlabel('Time (UTC)')
    plt.ylabel("No. of Tracks")
    plt.legend(loc="lower left", ncol=4)
    plt.tight_layout()
    plt.savefig(f"output/{fill}_{interval}_P.png", dpi=600)
    plt.clf()

    df.drop
