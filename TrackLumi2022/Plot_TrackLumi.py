from utilities import FEDtoReadOut
import sys
import pathlib
from os.path import join
import uproot4 as uproot
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from glob import glob
import argparse
import mplhep as hep
hep.style.use("CMS")

sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
from nf import post_to_slack

IN_FILE_PATH = "/home/nkarunar/track_root_files/"
OUT_FILE_PATH = "/home/nkarunar/PLTOffline/TrackLumi2022/plots/track_rates/"


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
    plt.ylabel("No. of Tracks")
    plt.legend(loc="lower left", ncol=4)
    plt.tight_layout()
    plt.savefig(join(OUT_FILE_PATH, f"{fill}_{interval}_M.png"), dpi=300)
    plt.clf()

    plt.figure(figsize=(16, 9))
    for ch in plus_channels:
        plt.plot(table.index, table[ch], 'o-', label=f'ch{ch}')
    plt.gca().xaxis.set_major_formatter(dfmt)
    plt.xticks(rotation=90)
    plt.xlabel('Time (UTC)')
    plt.ylabel("No. of Tracks")
    plt.legend(loc="lower left", ncol=4)
    plt.tight_layout()
    plt.savefig(join(OUT_FILE_PATH, f"{fill}_{interval}_P.png"), dpi=300)
    plt.clf()


def convert_to_timestamp(df):
    """Converts the timesec and timemsec columns to a timestamp column"""
    df.timesec = df.timesec.map(str)
    df.timemsec = df.timemsec.map(str).str.zfill(3)
    df.insert(2, 'timestamp', pd.to_datetime(df.timesec + df.timemsec, unit='ms') + pd.Timedelta(hours=2))
    df.drop(['timesec', 'timemsec'], axis=1, inplace=True)
    return df


def get_agg_table(file, interval):
    """Returns a pivot table with the number of tracks per channel per interval"""
    tree = uproot.open(f"{file}:T")
    df = tree.arrays(['timesec', 'timemsec', 'Channel'], library='pd')
    df = convert_to_timestamp(df)

    int_value = interval.replace('min', '')
    if not int(int_value) == 0:
        df['timestamp'] = df['timestamp'].dt.round(interval)

    table = df.pivot_table(index='timestamp', columns=['Channel'], aggfunc=len, fill_value=0).rename(columns=FEDtoReadOut())
    return table


def process_file(file, fill, interval):
    table = get_agg_table(file, interval)
    table.to_csv(join(OUT_FILE_PATH, f"{fill}_track_{interval}.csv"))
    make_plot(table, fill, interval)


def main(args):
    files = glob(join(IN_FILE_PATH, "????.root"))

    if len(files) == 0:
        print("No files to process")
        return

    for file in files:
        fill = int(pathlib.Path(file).stem)
        if fill < args.start or fill > args.end:
            continue

        print(f"Plotting track rate for {file}")
        post_to_slack(f"Plotting track rate for {file}")

        try:
            process_file(file, fill, args.interval)
            print(f"Finished plotting track rate for {file}")
            post_to_slack(f"Finished plotting track rate for {file}")
        except Exception as e:
            print(f"Error processing {file}: {e}")
            post_to_slack(f"Error processing {file}: {e.__class__.__name__}")
            continue


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description='Plot luminosity from track data')
    parser.add_argument('--start', type=int, required=True, help='Start fill (inclusive))')
    parser.add_argument('--end', type=int, required=True, help='End fill (inclusive))')
    parser.add_argument('--interval', type=str, default='5min', help='Interval to plot')
    args = parser.parse_args()

    main(args)
