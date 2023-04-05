import math
import csv
import os
import pathlib
import sys
import subprocess
from glob import glob
import pandas as pd
from pandas.tseries.offsets import Minute

from utilities import pltTimestamps

HOSTNAME = os.uname()[1]
if HOSTNAME == "DELLNK":
    sys.path.insert(0, '/home/nimmitha/utils')
elif "lxplus" in HOSTNAME:
    sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
else:
    print("Hostname not recognized. Exiting.")
    sys.exit()

from nf import post_to_slack

# PLT_PATH = os.getcwd().rsplit("/", 1)[0]
PLT_PATH = os.getcwd().split("PLTOffline")[0] + "PLTOffline/"

# PLT_PATH = "/eos/home-n/nkarunar/workrepos/PLTOffline/"

# FILE_PATH = "/home/nkarunar/root_files/"
FILE_PATH = "/eos/home-n/nkarunar/data/slink_data/slink_tracks/"

FILE_EXT = ".root"

# check hostname in python
# https://stackoverflow.com/a/28950776/13019084
HOSTNAME = os.uname()[1]


def create_maketrack_fills_csv(df):
    print("Creating the list of fills to be collected.")
    idx_dup = df.index.duplicated(keep="first")
    fill_info = df[~idx_dup]
    df_dup = df[idx_dup]

    for idx in df_dup.index:
        if fill_info.at[idx, "start"] > df_dup.at[idx, "start"]:
            fill_info.at[idx, "start"] = df_dup.at[idx, "start"]
        if fill_info.at[idx, "end"] < df_dup.at[idx, "end"]:
            fill_info.at[idx, "end"] = df_dup.at[idx, "end"]

    fill_info.to_csv("_maketrack_fills.csv", encoding='utf-8',
                     header=False, columns=["start", "end"])

    print("_maketrack_fills.csv created.")


def run_fit_scripts(df_row):
    print("\n Running fit script ", end='')
    fill = str(df_row.index[0])

    StartTime = str(int(df_row.iat[0, 0].strftime("%s")) + 0 * 3600)
    EndTime = str(int(df_row.iat[0, 1].strftime("%s")) + 0 * 3600)

    step = str(df_row.iat[0, 2])

    print("for Fill", fill)
    cmd_runScript = ["root", "-b", "-l", "-q"] + [
        "calcF_timeBased.C(\"" + fill + "\"," + StartTime + "," + EndTime + "," + step + ")"]
    print(cmd_runScript)

    x = subprocess.run(cmd_runScript)
    print(x)


def get_inst_luminosity(df_row):

    def parseDateBrilcalc(x): return pd.to_datetime(
        x, format='%m/%d/%y %H:%M:%S')

    print("\n Running brilcalc ", end='')
    fill = str(df_row.index[0])

    hh, mm = df_row.iat[0, 0].strftime("%H:%M").split(":")
    StartTime = str(3600 * int(hh) + 60 * int(mm))

    hh, mm = df_row.iat[0, 1].strftime("%H:%M").split(":")
    EndTime = str(3600 * int(hh) + 60 * int(mm))

    # fName=str(fill) + "_" + StartTime + "_" + EndTime
    fName = str(fill)

    print("for Fill", fill)

    tempLumifPath = "temp/" + fName + "tempLumi.csv"

    cmd_brilcalc = ["brilcalc", "lumi", "--begin", "mm/dd/yy hh:mm:ss", "--end",
                    "mm/dd/yy hh:mm:ss", "--byls", "-u", "hz/ub", "--type", "PLTZERO", "-o", tempLumifPath]

    cmd_brilcalc[3] = df_row.iat[0, 0].strftime("%m/%d/%y %H:%M:%S")
    cmd_brilcalc[5] = df_row.iat[0, 1].strftime("%m/%d/%y %H:%M:%S")

    print(cmd_brilcalc)
    x = subprocess.run(cmd_brilcalc)
    print(x)

    df_lumi = pd.read_csv(tempLumifPath, comment="#", header=None, names=[
        "fill", "ls", "time", "status", "E", "del", "rec", "avgpu", "source"], parse_dates=["time"], date_parser=parseDateBrilcalc)
    # print(df_lumi.head())

    StartTime = df_row.iat[0, 0]
    EndTime = df_row.iat[0, 1]
    step = pd.Timedelta(seconds=df_row.iat[0, 2])

    t1 = StartTime
    h_max = int((EndTime - StartTime) / step)

    lumiLogfPath = "logs/" + fName + "Lumi.csv"
    lumiLogFile = open(lumiLogfPath, 'w')
    lumiLogFile.write("fill,h,t1,t2,mean_lumi,mean_sbil\n")

    collidingBunches = 1

    for i in range(h_max):
        t1 = StartTime + i * step
        t2 = StartTime + (i + 1) * step

        mean_lumi = df_lumi[(df_lumi["time"] >= t1) & (
            df_lumi["time"] < t2)]["del"].mean()
        mean_sbil = mean_lumi / collidingBunches

        t1_save = t1.strftime('%s')
        # int(t1.strftime("%H"))*3600 + int(t1.strftime("%M"))*60

        t2_save = int(t2.strftime('%s')) - 1
        # int(t2.strftime("%H"))*3600 + int(t2.strftime("%M"))*60 - 1

        lineToWrite = fill + "," + str(i) + "," + str(t1_save) + "," + str(
            t2_save) + "," + str(mean_lumi) + "," + str(mean_sbil) + "\n"
        lumiLogFile.write(lineToWrite)


def combineLogs(df_row):
    def getCB(fill):
        fill_info = pd.read_csv(os.path.join(PLT_PATH, 'fill_info.csv'), index_col='oms_fill_number')
        fill_info = fill_info[fill_info.oms_stable_beams == True]

        CB = int(fill_info.loc[fill, 'oms_bunches_colliding'])
        print(f"Using CB = {CB}")
        return CB

        # BC = {4958: 1453, 4979: 2028, 5038: 1884,
        #       5106: 2064, 5401: 2208, 5406: 2208, 5424: 2208, 8033: 974, 8057: 974, 8078: 1538,
        #       8210: 140, 8211: 146, 8212: 578, 8214: 1154, 8216: 1154, 8220: 2448, 8221: 2448,
        #       8222: 2448, 8223: 2448, 8225: 2448, 8226: 8, 8228: 2448, 8230: 2448, 8232: 8, 8233: 205,
        #       8236: 2448, 8238: 2448, 8245: 2448}
        # return BC[fill]

    print("\n Combining Log files ", end='')
    fill = str(df_row.index[0])

    hh, mm = df_row.iat[0, 0].strftime("%H:%M").split(":")
    StartTime = str(3600 * int(hh) + 60 * int(mm))

    hh, mm = df_row.iat[0, 1].strftime("%H:%M").split(":")
    EndTime = str(3600 * int(hh) + 60 * int(mm))

    # fName=str(fill) + "_" + StartTime + "_" + EndTime
    fName = str(fill)
    lumiLogPath = "logs/" + fName + "Lumi.csv"
    fLogPath = "logs/" + fName + "F.csv"
    resultPath = "results/" + fName + ".csv"

    print("of Fill", fill)

    lumi_df = pd.read_csv(lumiLogPath, index_col="h")
    f_df = pd.read_csv(fLogPath, index_col="h")

    if lumi_df.shape[0] != f_df.shape[0]:
        print("Lengths does not match")
        return

    result = pd.merge(lumi_df, f_df)
    result["fSlopeY(%)"] = result.apply(lambda x: x.bkg_frac * 100, axis=1)
    result["fSlopeY_e(%)"] = result.apply(
        lambda x: x.bkg_frac_e * 100, axis=1)
    result["fR(%)"] = result.apply(lambda x: 100 *
                                   (x.ntracks_time - x.ntracks_resi) / x.ntracks_time, axis=1)
    result["fR_e(%)"] = result.apply(
        lambda x: 100 * math.sqrt(x.ntracks_time - x.ntracks_resi) / x.ntracks_time, axis=1)
    result["mean_sbil"] = result.apply(
        lambda x: x.mean_sbil / getCB(x.fill), axis=1)
    result.to_csv(resultPath, encoding='utf-8', index=False)


# def parseDate_fillSeg(x):
#     return pd.to_datetime(x, format='%Y-%m-%d %H:%M')

def add_timestamps_to_fills(pltTS, df):
    start_stable = []
    end_stable = []
    for index in df.index:
        start_date = pltTS.loc[index, "start_stable_beam"]
        end_date = pltTS.loc[index, "end_stable_beam"]

        # not needed anymore
        if end_date.day - start_date.day == 1:
            print(f"\nFill: {index} - Please fix the time manually.")

        start_stable.append((start_date + pd.Timedelta(minutes=5)).round(freq="5T"))
        end_stable.append((end_date - pd.Timedelta(minutes=5)).round(freq="5T"))

    df["start"] = start_stable
    df["end"] = end_stable

    df = df[['start', 'end', 'duration']]

    return df
    # print(df)
    # df.to_csv("input_fills.csv", encoding='utf-8', header=True)


def generate_missing_fills():
    """
    Check the results folder and compare it with the decoded fills
    If there are newly decoded fills, create a list of them.
    This can also exclude some fills from the list
    """
    result_files = glob(os.path.join(PLT_PATH, 'BackgroundFraction/results', '????.csv'))
    result_files = [int(pathlib.Path(file).stem) for file in result_files]
    print(result_files)
    decoded_files = glob(os.path.join(FILE_PATH, '????.root'))
    decoded_files = [int(pathlib.Path(file).stem) for file in decoded_files]
    print(decoded_files)

    # Excluded fills
    excluded = [8178, 8225, 8381, 8385]

    missing_results = [fill for fill in decoded_files if fill not in result_files and fill not in excluded]
    print(missing_results)
    post_to_slack(message_text=f'Bkg will work on: {missing_results}')

    # Create a csv file with the missing fills
    df = pd.DataFrame(columns=['start', 'end', 'duration'], index=missing_results)
    df.index.name = 'fill'

    df.duration = 300
    df = add_timestamps_to_fills(df)

    df.to_csv("input_fills.csv", encoding='utf-8', header=True)



# def generate_missing_fills(pltTS):
#     generate_missing_fills()
#     add_timestamps_to_fills(pltTS)
    
#     df = pd.read_csv('input_fills.csv', index_col="fill")  # Read the csv file
#     add_timestamps_to_fills(pltTS, df)
#     df = pd.read_csv('input_fills.csv', index_col="fill", parse_dates=["start", "end"], date_parser=parseDate_fillSeg)
#     return df


def main():
    pltTS = pltTimestamps(PLT_PATH)

    df = generate_missing_fills()
    # create_maketrack_fills_csv(df)

    # for i in range(df.shape[0]):
    #     print("\nWorking on row", df.index[i])
    #     post_to_slack(message_text=f"Begin bkg calc {df.index[i]}")

    #     run_fit_scripts(df.iloc[[i]])
    #     get_inst_luminosity(df.iloc[[i]])
    #     combineLogs(df.iloc[[i]])

    #     print("\nDone row", df.index[i])
    #     post_to_slack(message_text=f"Done bkg calc {df.index[i]}")


if __name__ == main():
    main()
