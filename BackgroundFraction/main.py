import math
import csv
import os
import sys
import subprocess
from matplotlib.markers import MarkerStyle
from numpy.lib.type_check import imag
import pandas as pd
import matplotlib.pyplot as plt
from pandas.io.parsers import read_csv
from pandas.tseries.offsets import Minute

sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
from nf import post_to_slack

PLT_PATH = "/eos/home-n/nkarunar/workrepos/PLTOffline/"
# FILE_PATH = "/home/nkarunar/root_files/"
FILE_PATH = "/eos/home-n/nkarunar/data/slink_data/slink_tracks/"
FILE_EXT = ".root"


def create_fill_segments_csv(pltTS, df):
    start_stable = []
    end_stable = []
    for index in df.index:
        start_date = pltTS.loc[index, "start_stable_beam"]
        end_date = pltTS.loc[index, "end_stable_beam"]

        if end_date.day - start_date.day == 1:
            print(f"\nFill: {index} - Please fix the time manually.")

        start_stable.append((start_date + pd.Timedelta(minutes=5)).round(freq="5T"))
        end_stable.append((end_date - pd.Timedelta(minutes=5)).round(freq="5T"))
        
    df["start"] = start_stable
    df["end"] = end_stable

    df = df[['start','end','duration']]
    
    print(df)
    df.to_csv("fill_segments.csv", encoding='utf-8', header=True)


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


def getTracks(pltTS):

    def runMakeTrack(arg_MakeTrack):
        cmd_MakeTrack = [PLT_PATH + "MakeTracks_nk"] + arg_MakeTrack

        print("\n"+"*"*150)
        print("Running : ", cmd_MakeTrack)
        print("*"*150)

        x = subprocess.run(cmd_MakeTrack)
        print(x)

    def combine_root_files(fill, StartTime, EndTime, nFiles):
        print("   Combining", nFiles, "root files.")
        rootfName = str(fill) + "_" + StartTime + "_" + EndTime
        cmd_hadd = ["hadd", "-f"] + [rootfName + "_raw" + FILE_EXT]

        for i in range(nFiles):
            cmd_hadd += [str(fill) + "_" + str(i) + "_" +
                         StartTime + "_" + EndTime + FILE_EXT]

        x = subprocess.run(cmd_hadd, cwd=FILE_PATH)
        print(x)
        run_fix_track_numbers(rootfName)

    def run_fix_track_numbers(rootfName):
        print("   Processing track numbers in file", rootfName)
        cmd_fixTrackNo = ["root", "-b", "-l", "-q"] + ["fix_track_numbers.C(\"" + rootfName + "\")"]

        x = subprocess.run(cmd_fixTrackNo)
        print(x)

    print("\nRunning MakeTrack on the list of fills.")
    with open("_maketrack_fills.csv", newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",")

        for row in csvreader:
            fill = int(row[0])
            print(" Working on", fill)

            hh, mm=[int(x) for x in row[1].split(" ")[1].split(":")[0:2]]
            StartTime=str(hh*3600 + mm*60)

            hh, mm=[int(x) for x in row[2].split(" ")[1].split(":")[0:2]]
            EndTime=str(hh*3600 + mm*60)

            rootfName=str(fill) + "_" + StartTime + "_" + EndTime

            print("  Checking for file:", rootfName)
            if os.path.isfile(FILE_PATH + rootfName + FILE_EXT):
                print("  ROOT file", rootfName, "already exists. Skipping..")
                continue
            print("  ROOT file not found. Creating", rootfName)
            
            Slink = pltTS.loc[fill, 'slinkTS'].split()

            if Slink == []:
                print("Could not find slink file name")
                exit(1)

            year = Slink[0][:4]

            gainCal = PLT_PATH + "GainCal/2020/GainCalFits_" + pltTS.loc[fill, 'gainCal'] + ".dat"
            alignment = PLT_PATH + "ALIGNMENT/" + pltTS.loc[fill, 'alignment']

            arg_MakeTrack = ["", gainCal, alignment,
                             str(fill), StartTime, EndTime]

            print("   Slink selected:", Slink)
            nFiles = len(Slink)

            if nFiles >= 2:
                print("   Slink is split into", nFiles, "files.")
                # run for each file
                for i, file_name in enumerate(Slink):
                    arg_MakeTrack[3] = str(fill) + "_" + str(i)
                    arg_MakeTrack[0] = "/localdata/"+year + \
                        "/SLINK/Slink_" + file_name + ".dat"
                    runMakeTrack(arg_MakeTrack)

                combine_root_files(fill, StartTime, EndTime, nFiles)

            else:
                # run once
                arg_MakeTrack[0] = "/localdata/"+year + \
                    "/SLINK/Slink_" + Slink[0] + ".dat"
                runMakeTrack(arg_MakeTrack)


def run_fit_scripts(df_row):
    print("\n Running fit script ", end='')
    fill = str(df_row.index[0])

    StartTime = str( int(df_row.iat[0, 0].strftime("%s")) + 0*3600 )
    EndTime = str( int(df_row.iat[0, 1].strftime("%s")) + 0*3600 )
    # hh, mm=df_row.iat[0, 0].strftime("%H:%M").split(":")
    # StartTime=str(3600*int(hh) + 60*int(mm))

    # hh, mm=df_row.iat[0, 1].strftime("%H:%M").split(":")
    # EndTime=str(3600*int(hh) + 60*int(mm))

    step=str(df_row.iat[0, 2])

    print("for Fill", fill)
    cmd_runScript=["root", "-b", "-l", "-q"] + [
        "calcF_timeBased.C(\"" + fill + "\"," + StartTime + "," + EndTime + "," + step + ")"]
    print(cmd_runScript)

    x=subprocess.run(cmd_runScript)
    print(x)


def get_inst_luminosity(df_row):

    def parseDateBrilcalc(x): return pd.to_datetime(
        x, format='%m/%d/%y %H:%M:%S')

    print("\n Running brilcalc ", end='')
    fill = str(df_row.index[0])

    hh, mm=df_row.iat[0, 0].strftime("%H:%M").split(":")
    StartTime=str(3600*int(hh) + 60*int(mm))

    hh, mm=df_row.iat[0, 1].strftime("%H:%M").split(":")
    EndTime=str(3600*int(hh) + 60*int(mm))

    # fName=str(fill) + "_" + StartTime + "_" + EndTime
    fName=str(fill)

    print("for Fill", fill)

    tempLumifPath="temp/" + fName + "tempLumi.csv"

    cmd_brilcalc=["brilcalc", "lumi", "--begin", "mm/dd/yy hh:mm:ss", "--end",
                    "mm/dd/yy hh:mm:ss", "--byls", "-u", "hz/ub", "--type", "PLTZERO", "-o", tempLumifPath]

    cmd_brilcalc[3]=df_row.iat[0, 0].strftime("%m/%d/%y %H:%M:%S")
    cmd_brilcalc[5]=df_row.iat[0, 1].strftime("%m/%d/%y %H:%M:%S")

    print(cmd_brilcalc)
    x=subprocess.run(cmd_brilcalc)
    print(x)

    df_lumi=pd.read_csv(tempLumifPath, comment="#", header=None, names=[
        "fill", "ls", "time", "status", "E", "del", "rec", "avgpu", "source"], parse_dates=["time"], date_parser=parseDateBrilcalc)
    # print(df_lumi.head())

    StartTime=df_row.iat[0, 0]
    EndTime=df_row.iat[0, 1]
    step=pd.Timedelta(seconds=df_row.iat[0, 2])

    t1=StartTime
    h_max=int((EndTime - StartTime)/step)

    lumiLogfPath="logs/" + fName + "Lumi.csv"
    lumiLogFile=open(lumiLogfPath, 'w')
    lumiLogFile.write("fill,h,t1,t2,mean_lumi,mean_sbil\n")

    collidingBunches=1

    for i in range(h_max):
        t1 = StartTime + i*step
        t2 = StartTime + (i+1)*step

        mean_lumi = df_lumi[(df_lumi["time"] >= t1) & (
            df_lumi["time"] < t2)]["del"].mean()
        mean_sbil = mean_lumi/collidingBunches

        t1_save = t1.strftime('%s')
        # int(t1.strftime("%H"))*3600 + int(t1.strftime("%M"))*60

        t2_save = int(t2.strftime('%s')) - 1
        # int(t2.strftime("%H"))*3600 + int(t2.strftime("%M"))*60 - 1

        lineToWrite = fill + "," + str(i) + "," + str(t1_save) + "," + str(
            t2_save) + "," + str(mean_lumi) + "," + str(mean_sbil) + "\n"
        lumiLogFile.write(lineToWrite)


def combineLogs(df_row):
    def getCB(fill):
        BC = {4958: 1453, 4979: 2028, 5038: 1884,
              5106: 2064, 5401: 2208, 5406: 2208, 5424: 2208, 8033: 974, 8057: 974, 8078: 1538,
              8210: 140, 8211: 146, 8212: 578, 8214: 1154, 8216: 1154, 8220: 2448, 8221: 2448,
              8222: 2448, 8223: 2448, 8225: 2448, 8226: 8, 8228: 2448, 8230: 2448, 8232: 8, 8233: 205,
              8236: 2448, 8238: 2448, 8245: 2448}
        return BC[fill]

    print("\n Combining Log files ", end='')
    fill = str(df_row.index[0])

    hh, mm=df_row.iat[0, 0].strftime("%H:%M").split(":")
    StartTime=str(3600*int(hh) + 60*int(mm))

    hh, mm=df_row.iat[0, 1].strftime("%H:%M").split(":")
    EndTime=str(3600*int(hh) + 60*int(mm))

    # fName=str(fill) + "_" + StartTime + "_" + EndTime
    fName=str(fill)
    lumiLogPath="logs/" + fName + "Lumi.csv"
    fLogPath="logs/" + fName + "F.csv"
    resultPath="results/" + fName + ".csv"

    print("of Fill", fill)

    lumi_df=pd.read_csv(lumiLogPath, index_col="h")
    f_df=pd.read_csv(fLogPath, index_col="h")

    # print(lumi_df)
    # print(f_df)

    if lumi_df.shape[0] != f_df.shape[0]:
        print("Lengths does not match")
        return

    result = pd.merge(lumi_df, f_df)
    # print(result)
    # return
    result["fSlopeY(%)"] = result.apply(lambda x: x.bkg_frac*100, axis=1)
    result["fSlopeY_e(%)"] = result.apply(
        lambda x: x.bkg_frac_e*100, axis=1)
    result["fR(%)"] = result.apply(lambda x: 100 *
                                   (x.ntracks_time-x.ntracks_resi)/x.ntracks_time, axis=1)
    result["fR_e(%)"] = result.apply(
        lambda x: 100 * math.sqrt(x.ntracks_time-x.ntracks_resi)/x.ntracks_time, axis=1)
    result["mean_sbil"] = result.apply(
        lambda x: x.mean_sbil/getCB(x.fill), axis=1)
    result.to_csv(resultPath, encoding='utf-8', index=False)


def pltTimestamps():
    # import pltTimestamps.csv file as dataframe (contains slink and workloop timestamps corresponding to all stable beam fills)
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

def parseDate_fillSeg(x):
    return pd.to_datetime(x, format='%Y-%m-%d %H:%M')


def main():
    pltTS = pltTimestamps()
    # print(pltTS)

    df = pd.read_csv('fill_segments.csv', index_col="fill")
    create_fill_segments_csv(pltTS, df)
    df = pd.read_csv('fill_segments.csv', index_col="fill", parse_dates=["start", "end"], date_parser=parseDate_fillSeg)
    create_maketrack_fills_csv(df)
    
    # getTracks(pltTS)
    # print(df)
    for i in range(df.shape[0]):
        print("\nWorking on row", i)
        post_to_slack(message_text=f"Begin bkg calc {df.index[i]}")

        run_fit_scripts(df.iloc[[i]])
        get_inst_luminosity(df.iloc[[i]])
        combineLogs(df.iloc[[i]])
        
        print("\nDone row", i)
        post_to_slack(message_text=f"Done bkg calc {df.index[i]}")


if __name__ == main():
    main()
    
