from utilities import pltTimestamps
import os
import sys
import subprocess
import pandas as pd
import argparse

sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
from nf import post_to_slack


PLT_PATH = os.getcwd().split("PLTOffline")[0] + "PLTOffline/"
HIT_FILE_PATH = "/home/nkarunar/hit_root_files/"
TRACK_FILE_PATH = "/home/nkarunar/track_root_files/"
SLINK_FILE_PATH = "/localdata/"
FILE_PATH = "null"
FILE_EXT = ".root"

print("Working from:", PLT_PATH)


def runMakeTrack_version(arg_MakeTrack, mode):
    if mode == "hits":
        process = "MakeTracks_hits_nk"
    elif mode == "tracks":
        process = "MakeTracks_nk"

    cmd = [os.path.join(PLT_PATH, process)] + arg_MakeTrack
    print("\n" + "*" * 50)
    print("Running : ", cmd)
    print("*" * 50)
    x = subprocess.run(cmd)
    print(x)
    if x.returncode != 0:
        raise Exception("Error in MakeTracks")


def combine_root_files(fill, nslink_files):
    print(" Combining", nslink_files, "root files.")
    rootfName = str(fill)
    cmd_hadd = ["hadd", "-f"] + [rootfName + "_raw" + FILE_EXT]
    for i in range(nslink_files):
        cmd_hadd += [str(fill) + "_" + str(i) + FILE_EXT]
    x = subprocess.run(cmd_hadd, cwd=FILE_PATH)
    print(x)
    run_fix_track_numbers(rootfName)


def run_fix_track_numbers(rootfName):
    print("Processing track numbers in file", rootfName)
    cmd_fixTrackNo = ["root", "-b", "-l", "-q"] + \
        ["fix_track_numbers.C(\"" + rootfName + "\")"]
    x = subprocess.run(cmd_fixTrackNo)
    print(x)


def getTracks(pltTS, mode):

    for index, row in pltTS.iterrows():
        fill = int(row.name)

        # Send notifications
        post_to_slack(message_text="Working on " + str(fill))
        print("Working on", fill)

        # Read the start and end times
        hh = row.start_stable_beam.hour
        mm = row.start_stable_beam.minute
        StartTime = str(hh * 3600 + mm * 60)

        hh = row.end_stable_beam.hour
        mm = row.end_stable_beam.minute
        EndTime = str(hh * 3600 + mm * 60)

        rootfName = str(fill)

        if os.path.isfile(FILE_PATH + rootfName + FILE_EXT):
            print(f"ROOT file with {mode}", rootfName, "already exists. Skipping..")
            continue
        else:
            print("ROOT file not found. Creating", rootfName)

        gainCal = os.path.join(PLT_PATH, f"GainCal/2020/GainCalFits_{row.gainCal}.dat")
        alignment = os.path.join(PLT_PATH, "ALIGNMENT", row.alignment)

        slink_files = row.slinkTS.split()
        nslink_files = len(slink_files)

        if nslink_files == 0:
            print(f"No slink file. Skipping {fill}")
            continue

        year = slink_files[0][:4]
        if year not in ['2022', '2023']:
            print("Only checked for 2022 and 2023. Skipping..")
            continue

        arg_MakeTrack = ["", gainCal, alignment, str(fill), StartTime, EndTime, ""]

        # run for each file
        if nslink_files > 1:
            print("SLINK data is split into", nslink_files, "files.")

            for i, slink_file in enumerate(slink_files):
                arg_MakeTrack[3] = str(fill) + "_" + str(i)
                arg_MakeTrack = get_makeTrack_args(slink_file, row, arg_MakeTrack, StartTime, EndTime)

                runMakeTrack_version(arg_MakeTrack, mode)
            combine_root_files(fill, nslink_files)

        else:
            # run once
            arg_MakeTrack = get_makeTrack_args(slink_files[0], row, arg_MakeTrack, StartTime, EndTime)

            runMakeTrack_version(arg_MakeTrack, mode)

        post_to_slack(message_text=f"Finished collecting {mode} for " + str(fill))


def get_makeTrack_args(slink_file_name, row, arg_MakeTrack, StartTime, EndTime):
    slink_date = pd.to_datetime(slink_file_name, format='%Y%m%d.%H%M%S')
    startTime_adjust = int((row.start_stable_beam.date() - slink_date.date()) / pd.Timedelta(1, 'D'))
    endTime_adjust = int((row.end_stable_beam.date() - slink_date.date()) / pd.Timedelta(1, 'D'))

    dateToSend = row.start_stable_beam.date()

    if startTime_adjust < 0:
        dateToSend = dateToSend + pd.Timedelta(abs(startTime_adjust), 'D')
        startTime_adjust = 0
    if endTime_adjust < 0:
        endTime_adjust = 0

    AStartTime = int(StartTime) + startTime_adjust * 24 * 3600
    AEndTime = int(EndTime) + endTime_adjust * 24 * 3600

    arg_MakeTrack[0] = os.path.join(SLINK_FILE_PATH, slink_date.strftime("%Y"), f'SLINK/Slink_{slink_file_name}.dat')
    arg_MakeTrack[4] = str(AStartTime)
    arg_MakeTrack[5] = str(AEndTime)
    arg_MakeTrack[6] = str(dateToSend.strftime("%s"))

    return arg_MakeTrack


def get_fills_to_run(start_fill, end_fill):
    pltTS = pltTimestamps(PLT_PATH)
    exclude_fill = [8178]

    pltTS = pltTS[(pltTS.index >= start_fill) & (pltTS.index <= end_fill)]

    fills_to_run = [fill for fill in list(pltTS.index) if fill not in exclude_fill]
    return pltTS.loc[fills_to_run]


def main(args):

    fills_to_run = get_fills_to_run(args.start, args.end)
    print("List of fills:", list(fills_to_run.index))
    post_to_slack(message_text="Found:" + str.join(",", [str(i) for i in list(fills_to_run.index)]))

    try:
        getTracks(fills_to_run, args.mode)
    except Exception as exception:
        print(exception)
        post_to_slack(message_text=str(exception))


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description='Collect SLINK tracks or hits')
    parser.add_argument('--mode', type=str, choices=["hits", "tracks"], default="hits", help='Program to run', required=True)
    parser.add_argument('--start', type=int, default=8700, help='Start fill (inclusive))')
    parser.add_argument('--end', type=int, default=8700, help='End fill (inclusive))')
    args = parser.parse_args()

    if args.mode == "hits":
        FILE_PATH = HIT_FILE_PATH
        print("Collecting hits")
    elif args.mode == "tracks":
        FILE_PATH = TRACK_FILE_PATH
        print("Collecting tracks")

    main(args)
