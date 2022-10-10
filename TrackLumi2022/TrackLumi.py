import os
import sys
import subprocess
import pandas as pd

sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
from nf import post_to_slack

# PLT_PATH = "/eos/home-n/nkarunar/workrepos/PLTOffline/"
# PLT_PATH = "/home/nkarunar/PLTOffline/"
PLT_PATH = os.getcwd().rsplit("/", 1)[0]
FILE_PATH = "/home/nkarunar/root_files/"
FILE_EXT = ".root"

print("Working from:", PLT_PATH)


def pltTimestamps():
    # import pltTimestamps.csv file as dataframe (contains slink_files and workloop timestamps corresponding to all stable beam fills)
    def parseDate(x): return pd.to_datetime(x, format='%Y%m%d.%H%M%S')
    with open(os.path.join(PLT_PATH, 'pltTimestamps.csv'), 'r') as tsFile:
        cols = tsFile.readline().strip().split('|')
        tsFile.seek(0)
        dtypes = dict(zip(cols, ['int']+9*['str']))
        # [https://stackoverflow.com/a/37453925/13019084]
        pltTS = pd.read_csv(
            tsFile, sep='|', dtype=dtypes, parse_dates=cols[1:5], date_parser=parseDate)
    pltTS = pltTS.set_index('fill').fillna('')
    return pltTS


def runMakeTrack(arg_MakeTrack):
    cmd_MakeTrack = [os.path.join(PLT_PATH, "MakeTracks_nk")] + arg_MakeTrack
    print("\n"+"*"*50)
    print("Running : ", cmd_MakeTrack)
    print("*"*50)
    x = subprocess.run(cmd_MakeTrack)
    print(x)


def combine_root_files(fill, StartTime, EndTime, nslink_files):
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


def getTracks(pltTS):

    for index, row in pltTS.iterrows():
        fill = int(row.name)

        # Send notifications
        post_to_slack(message_text="Working on "+str(fill))

        print("Working on", fill)

        hh = row.start_stable_beam.hour
        mm = row.start_stable_beam.minute
        StartTime = str(hh*3600 + mm*60)

        hh = row.end_stable_beam.hour
        mm = row.end_stable_beam.minute
        EndTime = str(hh*3600 + mm*60)

        rootfName = str(fill)  # + "_" + StartTime + "_" + EndTime
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

                dateToSend = row.start_stable_beam.date()

                if startTime_adjust < 0:
                    dateToSend = dateToSend + pd.Timedelta(abs(startTime_adjust), 'D')
                    startTime_adjust = 0
                if endTime_adjust < 0:
                    endTime_adjust = 0

                AStartTime = int(StartTime) + startTime_adjust * 24 * 3600
                AEndTime = int(EndTime) + endTime_adjust * 24 * 3600

                arg_MakeTrack[4] = str(AStartTime)
                arg_MakeTrack[5] = str(AEndTime)
                arg_MakeTrack.append(str(dateToSend.strftime("%s")))

                runMakeTrack(arg_MakeTrack)
            combine_root_files(fill, str(AStartTime),
                               str(AEndTime), nslink_files)

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

            dateToSend = row.start_stable_beam.date()
            print(dateToSend)
            # print(dateToSend.strftime("%s"))

            if startTime_adjust < 0:
                dateToSend = dateToSend + pd.Timedelta(abs(startTime_adjust), 'D')
                startTime_adjust = 0
            if endTime_adjust < 0:
                endTime_adjust = 0

            AStartTime = int(StartTime) + startTime_adjust * 24 * 3600
            AEndTime = int(EndTime) + endTime_adjust * 24 * 3600

            arg_MakeTrack[4] = str(AStartTime)
            arg_MakeTrack[5] = str(AEndTime)
            arg_MakeTrack.append(str(dateToSend.strftime("%s")))

            runMakeTrack(arg_MakeTrack)


def main():
    pltTS = pltTimestamps()

    # start_fill, end_fill = 8112, 8220 #8149, 8149
    start_fill, end_fill = 8121, 8121  # 8149, 8149
    exclude_fill = [8178]

    pltTS = pltTS[(pltTS.index >= start_fill) & (pltTS.index <= end_fill)]
    try:
        pltTS = pltTS.loc[pltTS.index.drop(exclude_fill)]
    except:
        pass

    print("List of fills:", list(pltTS.index))
    post_to_slack(message_text="Found:"+str.join(",",
                  [str(i) for i in list(pltTS.index)]))
    try:
        getTracks(pltTS)
    except Exception as e:
        print(e)
        post_to_slack(message_text=e)


if __name__ == "__main__":
    main()
