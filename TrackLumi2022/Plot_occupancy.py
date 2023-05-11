from utilities import FEDtoReadOut
import sys
from os.path import join
import pathlib
from glob import glob
import numpy as np
import uproot4 as uproot
import concurrent.futures
import matplotlib.pyplot as plt
import argparse
# from tqdm import tqdm
import mplhep as hep


sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
from nf import post_to_slack
hep.style.use("CMS")

IN_FILE_PATH = "/home/nkarunar/hit_root_files/"
OUT_FILE_PATH = "/home/nkarunar/PLTOffline/TrackLumi2022/plots/occupancy/"

executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

MAX_ROW = 80
MAX_COL = 52
BOUNDARY = 5  # masking 5 pixels from the edge


def plot_occupancy_hist(fill, occupancy_hist):
    for channel in range(16):
        print(f"Making plots for channel {channel}")
        fig, ax = plt.subplots(1, 3, figsize=(20, 6))

        for roc in range(3):
            pcm = ax[roc].pcolormesh(occupancy_hist[channel][roc], cmap='jet')

            ax[roc].set_title(f"ROC{roc}")
            ax[roc].set_xlabel("col")
            ax[roc].set_ylabel("row")

            fig.colorbar(pcm, ax=ax[roc], pad=0)
            plt.subplots_adjust(left=0.1,
                                bottom=0.15,
                                right=0.9,
                                top=0.8,
                                wspace=0.2,
                                hspace=0.1)

        fig.suptitle(f"Occupancy for channel {channel}")
        fig.savefig(join(OUT_FILE_PATH, f"{fill}_occupancy_ch{channel}.png"))
        plt.close()


def process_chunk(df, xedges, yedges):
    """ Process a chunk of the root file and add hits to the histogram """
    hist_chunk = np.zeros((16, 3, MAX_ROW, MAX_COL))
    df.channel = df.channel.map(FEDtoReadOut())
    for channel in sorted(df.channel.unique()):
        per_ch_df = df[df.channel == channel]
        for roc in range(3):
            per_roc_df = per_ch_df[per_ch_df.roc == roc]
            x = per_roc_df.col
            y = per_roc_df.row
            H, _, _ = np.histogram2d(x, y, bins=[xedges, yedges])
            H = H.T

            H = np.where(H == 0, np.nan, H)
            hist_chunk[channel][roc] += H

    return hist_chunk


def get_histogram_from_hits(fill, file):
    occupancy_hist = np.zeros((16, 3, MAX_ROW, MAX_COL))
    xedges = np.arange(0, MAX_COL + 1, 1)
    yedges = np.arange(0, MAX_ROW + 1, 1)

    tree = uproot.open(file + ':T')
    nentries = tree.num_entries
    cols_to_read = ['event', 'channel', 'roc', 'row', 'col']

    print(f"Number of entries: {nentries}")

    for df, report in tree.iterate(cols_to_read, step_size="40 MB", library='pd', report=True, interpretation_executor=None):
        print(f'File read progress : {report.stop/nentries*100:0.2f}%')

        # print(df.head())
        hist_chunk = process_chunk(df, xedges, yedges)
        occupancy_hist[:][:] += hist_chunk[:][:]
        # break

    # Save the full histogram
    np.save(join(OUT_FILE_PATH, f'{fill}_occupancy_hist.npy'), occupancy_hist)

    # Replace the edges with nan
    mask = np.empty_like(occupancy_hist[0][0])
    mask[:] = np.nan
    mask[BOUNDARY:-BOUNDARY, BOUNDARY:-BOUNDARY] = 1  # 1 for inside, nan for outside
    occupancy_hist = mask * occupancy_hist[:][:]

    return occupancy_hist


def main(args):
    files = glob(join(IN_FILE_PATH, "????.root"))

    if len(files) == 0:
        print("No files to process")
        return

    for file in files:
        fill = int(pathlib.Path(file).stem)
        if fill < args.start or fill > args.end:
            continue

        print(f"Plotting occupancy for {file}")
        post_to_slack(message_text=f"Plotting occupancy for {file}")

        try:
            occupancy_hist = get_histogram_from_hits(fill, file)
            plot_occupancy_hist(fill, occupancy_hist)
            post_to_slack(message_text=f"Occupancy completed for {fill}")
        except Exception as e:
            print(e)
            post_to_slack(message_text=str(e))


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description='Plot occupancy from hit root files')
    parser.add_argument('--start', type=int, required=True, help='Start fill (inclusive))')
    parser.add_argument('--end', type=int, required=True, help='End fill (inclusive))')
    args = parser.parse_args()

    main(args)
