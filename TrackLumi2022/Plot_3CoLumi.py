from utilities import FEDtoReadOut
import sys
import argparse
import pandas as pd
from glob import glob
import uproot4 as uproot
import pathlib
from os.path import join
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplhep as hep
hep.style.use("CMS")

sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
from nf import post_to_slack

IN_FILE_PATH = "/home/nkarunar/hit_root_files/"
OUT_FILE_PATH = "/home/nkarunar/PLTOffline/TrackLumi2022/output/plots/3co/"


def make_plot(table, fill, interval):
    channels = [i for i in table.columns if isinstance(i, (int))]
    minus_channels = [i for i in channels if i < 8]
    plus_channels = [i for i in channels if i >= 8]

    dfmt = mdates.DateFormatter("%H:%M")
    plt.figure(figsize=(16, 9))
    for ch in minus_channels:
        plt.plot(table.index, table[ch], 'o-', label=f'ch{ch}')
    plt.gca().xaxis.set_major_formatter(dfmt)
    plt.xticks(rotation=90)
    plt.xlabel('Time (UTC)')
    plt.ylabel("SLINK Triple-Coincidence")
    plt.legend(loc="lower left", ncol=4)
    plt.tight_layout()
    plt.savefig(join(OUT_FILE_PATH, f"{fill}_3Co_{interval}_M.png"), dpi=600)
    plt.clf()

    plt.figure(figsize=(16, 9))
    for ch in plus_channels:
        plt.plot(table.index, table[ch], 'o-', label=f'ch{ch}')
    plt.gca().xaxis.set_major_formatter(dfmt)
    plt.xticks(rotation=90)
    plt.xlabel('Time (UTC)')
    plt.ylabel("SLINK Triple-Coincidence")
    plt.legend(loc="lower left", ncol=4)
    plt.tight_layout()
    plt.savefig(join(OUT_FILE_PATH, f"{fill}_3Co_{interval}_P.png"), dpi=600)
    plt.clf()


def sum_channels(df):
    validCh = [0, 1, 2, 3, 10, 11, 12, 14, 15]
    # validCh = [str(i) for i in validCh]

    df['slink_valid'] = df[[col for col in df.columns if col in validCh]].sum(axis=1)
    df['slink_all'] = df[[col for col in range(16)]].sum(axis=1)
    return df


def get_3Co(df):
    df.drop(columns=['row', 'col'], inplace=True)
    df.drop_duplicates(['event', 'channel', 'roc'], inplace=True)
    table = df.pivot_table(values='roc', index=['timesec', 'timemsec'], columns='channel', aggfunc='count')
    table = table[table == 3].dropna(how='all').fillna(0).astype('int').replace(3, 1).reset_index().rename_axis(None, axis=1)
    table.timesec = table.timesec.map(str)
    table.timemsec = table.timemsec.map(str).str.zfill(3)
    table.insert(2, 'timestamp', pd.to_datetime(table.timesec + table.timemsec, unit='ms') + pd.Timedelta(hours=2))
    table.drop(['timesec', 'timemsec'], axis=1, inplace=True)
    return table


def aggregate_to(df, interval='1min'):
    df.timestamp = df.timestamp.dt.round(interval)
    df = df.groupby('timestamp').sum()
    df.reset_index(inplace=True)
    return df


def remove_edges(df, edge=4):
    MAX_ROW = 80
    MAX_COL = 52
    df = df[(df.row >= edge) | (df.row < MAX_ROW - edge) | (df.col >= edge) | (df.col < MAX_COL - edge)]
    return df

def process_chunk(df, table_chunks, interval):
    df.channel = df.channel.map(FEDtoReadOut())
    df = remove_edges(df, 4)
    table = get_3Co(df)
    # table = sum_channels(table)
    table = aggregate_to(table, interval)

    return table


def process_file(file, fill, interval):
    tree = uproot.open(f'{file}:T')
    nentries = tree.num_entries
    print(f"Number of entries: {nentries}")

    table_chunks = []
    for df, report in tree.iterate(['timesec', 'timemsec', 'event', 'channel', 'roc', 'row', 'col'], step_size="30 MB", library='pd', report=True):
        print(f'File read progress : {report.stop/nentries*100:0.2f}%')

        table = process_chunk(df, table_chunks, interval)
        table_chunks.append(table)

    table = pd.concat(table_chunks)
    table = table.groupby('timestamp').sum()
    table.reset_index(inplace=True)
    print(table.head())
    table.to_csv(join(OUT_FILE_PATH, f'{fill}_3Co_{interval}.csv'), index=False)

    return table


def main(args):
    files = glob(join(IN_FILE_PATH, "????.root"))

    if len(files) == 0:
        print("No files to process")
        return

    for file in files:
        fill = int(pathlib.Path(file).stem)
        if fill < args.start or fill > args.end:
            continue

        print(f"Plotting 3Co for {file}")
        post_to_slack(f"Plotting 3Co for {file}")
        
        try:  
            table = process_file(file, fill, args.interval)
            make_plot(table, fill, args.interval)
            print(f"Finished plotting 3Co {file}")
            post_to_slack(f"Finished plotting 3Co {file}")
        except Exception as e:
            print(f"Error plotting 3Co {file}")
            print(e)
            post_to_slack(f"Error plotting 3Co {file}: {e.__class__.__name__}")
            continue


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description='Plot tripl coincidance rate from hit data')
    parser.add_argument('--start', type=int, required=True, help='Start fill (inclusive))')
    parser.add_argument('--end', type=int, required=True, help='End fill (inclusive))')
    parser.add_argument('--interval', type=str, default='5min', help='Interval to plot')
    args = parser.parse_args()

    main(args)
