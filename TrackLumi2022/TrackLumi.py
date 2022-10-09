import os
import subprocess
from tkinter import E
import pandas as pd


PLT_PATH = "/eos/home-n/nkarunar/workrepos/PLTOffline/"
FILE_PATH = "/home/nkarunar/root_files/"
FILE_EXT = ".root"


def pltTimestamps():
    # import pltTimestamps.csv file as dataframe (contains slink_files and workloop timestamps corresponding to all stable beam fills)
    def parseDate(x): return pd.to_datetime(x, format='%Y%m%d.%H%M%S')
    with open('/eos/home-n/nkarunar/workrepos/PLTOffline/pltTimestamps.csv', 'r') as tsFile:
        cols = tsFile.readline().strip().split('|')
        tsFile.seek(0)
        dtypes = dict(zip(cols, ['int']+9*['str']))
        # [https://stackoverflow.com/a/37453925/13019084]
        pltTS = pd.read_csv(
            tsFile, sep='|', dtype=dtypes, parse_dates=cols[1:5], date_parser=parseDate)
    pltTS = pltTS.set_index('fill').fillna('')
    return pltTS


def runMakeTrack(arg_MakeTrack):
    cmd_MakeTrack = [PLT_PATH + "MakeTracks_nk"] + arg_MakeTrack
    print("\n"+"*"*150)
    print("Running : ", cmd_MakeTrack)
    print("*"*150)
    x = subprocess.run(cmd_MakeTrack)
    print(x)


def combine_root_files(fill, StartTime, EndTime, nslink_files):
    print(" Combining", nslink_files, "root files.")
    rootfName = str(fill) + "_" + StartTime + "_" + EndTime
    cmd_hadd = ["hadd", "-f"] + [rootfName + "_raw" + FILE_EXT]
    for i in range(nslink_files):
        cmd_hadd += [str(fill) + "_" + str(i) + "_" +
                     StartTime + "_" + EndTime + FILE_EXT]
    x = subprocess.run(cmd_hadd, cwd=FILE_PATH)
    print(x)
    run_fix_track_numbers(rootfName)


def run_fix_track_numbers(rootfName):
    print("Processing track numbers in file", rootfName)
    cmd_fixTrackNo = ["root", "-b", "-l", "-q"] + \
        ["fix_track_numbers.C(\"" + rootfName + "\")"]
    x = subprocess.run(cmd_fixTrackNo)
    print(x)


def getTracks(pltTS):

    for index, row in pltTS.iterrows():
        fill = int(row.name)
        print("Working on", fill)

        hh = row.start_stable_beam.hour
        mm = row.start_stable_beam.minute
        StartTime = str(hh*3600 + mm*60)

        hh = row.end_stable_beam.hour
        mm = row.end_stable_beam.minute
        EndTime = str(hh*3600 + mm*60)

        # Naming the file as usual, time relative to the day
        rootfName = str(fill) + "_" + StartTime + "_" + EndTime
        print("Check if", rootfName, "already exists.")

        if os.path.isfile(FILE_PATH + rootfName + FILE_EXT):
            print("ROOT file", rootfName, "already exists. Skipping..")
            # return

        print("ROOT file not found. Creating", rootfName)

        gainCal = os.path.join(
            PLT_PATH, f"GainCal/2020/GainCalFits_{row.gainCal}.dat")
        alignment = os.path.join(PLT_PATH, "ALIGNMENT", row.alignment)

        slink_files = row.slinkTS.split()
        # print(slink_files)
        nslink_files = len(slink_files)
        if nslink_files == 0:
            print(f"No slink file. Skipping {fill}")
            continue

        year = slink_files[0][:4]
        if year != '2022':
            print("Only checked for 2022. Check before running")
            continue

        arg_MakeTrack = ["", gainCal, alignment, str(fill), StartTime, EndTime]

        if nslink_files >= 2:
            print("Slink is split into", nslink_files, "files.")
            # run for each file
            for i, slink_file in enumerate(slink_files):
                arg_MakeTrack[3] = str(fill) + "_" + str(i)
                arg_MakeTrack[0] = os.path.join(
                    '/localdata', year,  f'SLINK/Slink_{slink_file}.dat')

                slink_date = pd.to_datetime(slink_file, format='%Y%m%d.%H%M%S')
                startTime_adjust = int(
                    (row.start_stable_beam.date() - slink_date.date()) / pd.Timedelta(1, 'D'))
                endTime_adjust = int(
                    (row.end_stable_beam.date() - slink_date.date()) / pd.Timedelta(1, 'D'))

                AStartTime = int(StartTime) + startTime_adjust * 24 * 3600
                AEndTime = int(EndTime) + endTime_adjust * 24 * 3600
                arg_MakeTrack[4] = str(AStartTime)
                arg_MakeTrack[5] = str(AEndTime)

                runMakeTrack(arg_MakeTrack)
            combine_root_files(fill, StartTime, EndTime, nslink_files)

        else:
            # run once
            arg_MakeTrack[0] = os.path.join(
                '/localdata', year,  f'SLINK/Slink_{slink_files[0]}.dat')

            slink_date = pd.to_datetime(slink_files[0], format='%Y%m%d.%H%M%S')
            startTime_adjust = int(
                (row.start_stable_beam.date() - slink_date.date()) / pd.Timedelta(1, 'D'))
            endTime_adjust = int(
                (row.end_stable_beam.date() - slink_date.date()) / pd.Timedelta(1, 'D'))

            AStartTime = int(StartTime) + startTime_adjust * 24 * 3600
            AEndTime = int(EndTime) + endTime_adjust * 24 * 3600
            arg_MakeTrack[4] = str(AStartTime)
            arg_MakeTrack[5] = str(AEndTime)

            runMakeTrack(arg_MakeTrack)


def main():
    pltTS = pltTimestamps()

    start_fill, end_fill = 8149, 8149
    pltTS = pltTS[(pltTS.index >= start_fill) & (pltTS.index <= end_fill)]

    # print(pltTS)
    getTracks(pltTS)


if __name__ == "__main__":
    main()
