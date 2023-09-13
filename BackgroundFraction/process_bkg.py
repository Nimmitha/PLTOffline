from utilities import pltTimestamps, FEDtoReadOut
from plotting import plot_table, plot_box
from ROOT import RooFit, RooArgSet, RooArgList, RooGaussian, RooRealVar, RooAddPdf, TCanvas
import ROOT
import math
import os
import pathlib
import sys
import argparse
import subprocess
from glob import glob
import pandas as pd
from calcF_timeBased import get_bckg_frac
# import mplhep as hep
# hep.style.use("CMS")


ROOT.gErrorIgnoreLevel = ROOT.kWarning
RooMsgService = ROOT.RooMsgService.instance()
RooMsgService.Print()
# Remove all
# RooMsgService.setGlobalKillBelow(RooFit.ERROR)

# Remove selected topics
RooMsgService.getStream(1).removeTopic(RooFit.DataHandling)
RooMsgService.getStream(1).removeTopic(RooFit.Eval)
RooMsgService.getStream(1).removeTopic(RooFit.Plotting)
RooMsgService.getStream(1).removeTopic(RooFit.Minimization)


HOSTNAME = os.uname()[1]
if HOSTNAME == "DELLNK":
    sys.path.insert(0, '/home/nimmitha/utils')
elif "lxplus" in HOSTNAME or "scx5-c2f06-36" in HOSTNAME:
    sys.path.insert(0, '/afs/cern.ch/user/n/nkarunar/utils')
else:
    print("Hostname not recognized. Exiting.")
    sys.exit()
from nf import post_to_slack

PLT_PATH = os.getcwd().split("PLTOffline")[0] + "PLTOffline/"

# PLT_PATH = "/eos/home-n/nkarunar/workrepos/PLTOffline/"

FILE_PATH = "/home/nkarunar/track_root_files/"
# FILE_PATH = "/mnt/d/Cernbox/data/temp_access/"
# FILE_PATH = "/eos/home-n/nkarunar/data/slink_data/slink_tracks/"

FILE_EXT = ".root"

def create_maketrack_fills_csv(df):
    """Deprecated function"""
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
    fill = str(df_row.name)
    print(f"Running bkg calculation for {fill}")

    StartTime = (int(df_row['start'].strftime("%s")) + 0 * 3600)
    EndTime = (int(df_row['end'].strftime("%s")) + 0 * 3600)
    step = (df_row['duration'])

    get_bckg_frac(fill, StartTime, EndTime, step)


def get_inst_luminosity(df_row):

    def parseDateBrilcalc(x): return pd.to_datetime(x, format='%m/%d/%y %H:%M:%S')

    fill = str(df_row.name)
    fName = str(fill)
    tempLumifPath = "temp/" + fName + "tempLumi.csv"
    print(f"Running brilcalc for {fill}")

    hh, mm = df_row['start'].strftime("%H:%M").split(":")
    StartTime = str(3600 * int(hh) + 60 * int(mm))

    hh, mm = df_row['end'].strftime("%H:%M").split(":")
    EndTime = str(3600 * int(hh) + 60 * int(mm))

    cmd_brilcalc = ["brilcalc", "lumi", "--begin", "mm/dd/yy hh:mm:ss", "--end",
                    "mm/dd/yy hh:mm:ss", "--byls", "-u", "hz/ub", "--type", "PLTZERO", "-o", tempLumifPath]

    cmd_brilcalc[3] = df_row['start'].strftime("%m/%d/%y %H:%M:%S")
    cmd_brilcalc[5] = df_row['end'].strftime("%m/%d/%y %H:%M:%S")

    # print(cmd_brilcalc)
    x = subprocess.run(cmd_brilcalc)
    print(x)

    df_lumi = pd.read_csv(tempLumifPath, comment="#", header=None, names=[
        "fill", "ls", "time", "status", "E", "del", "rec", "avgpu", "source"], parse_dates=["time"], date_parser=parseDateBrilcalc)
    # print(df_lumi.head())

    StartTime = df_row['start']
    EndTime = df_row['end']
    step = pd.Timedelta(seconds=df_row['duration'])

    t1 = StartTime
    h_max = int((EndTime - StartTime) / step)

    lumiLogfPath = "logs/" + fName + "Lumi.csv"
    lumiLogFile = open(lumiLogfPath, 'w')
    lumiLogFile.write("fill,h,t1,t2,mean_lumi,mean_sbil\n")

    collidingBunches = 1

    for i in range(h_max):
        t1 = StartTime + i * step
        t2 = StartTime + (i + 1) * step

        mean_lumi = df_lumi[(df_lumi["time"] > t1) & (
            df_lumi["time"] <= t2)]["del"].mean()
        mean_sbil = mean_lumi / collidingBunches

        t1_save = t1.strftime('%s')
        t2_save = int(t2.strftime('%s')) - 1

        lineToWrite = fill + "," + str(i) + "," + str(t1_save) + "," + str(
            t2_save) + "," + str(mean_lumi) + "," + str(mean_sbil) + "\n"
        lumiLogFile.write(lineToWrite)


def combineLogs(df_row):
    
    def getCB(fill):
        df = pd.read_csv('https://delannoy.web.cern.ch/fills.csv')
        CB = int(df[(df['oms_fill_number'] == fill) & (df['oms_stable_beams']==True)]['oms_bunches_colliding'])
        return CB


    fill = str(df_row.name)
    fName = str(fill)
    lumiLogPath = "logs/" + fName + "Lumi.csv"
    fLogPath = "logs/" + fName + "F.csv"
    resultPath = "results/" + fName + ".csv"
    print(f"Combining logs for {fill}")

    # Read luminosity and Background Fraction logs
    lumi_df = pd.read_csv(lumiLogPath, index_col="h")
    f_df = pd.read_csv(fLogPath, index_col="h")

    if lumi_df.shape[0] != f_df.shape[0]:
        print("Lengths do not match")
        return

    result = pd.merge(lumi_df, f_df)
    result["fSlopeY(%)"] = result.apply(lambda x: x.bkg_frac * 100, axis=1)
    result["fSlopeY_e(%)"] = result.apply(lambda x: x.bkg_frac_e * 100, axis=1)
    result["fR(%)"] = result.apply(lambda x: 100 * (x.ntracks_time - x.ntracks_resi) / x.ntracks_time, axis=1)
    result["fR_e(%)"] = result.apply(lambda x: 100 * math.sqrt(x.ntracks_time - x.ntracks_resi) / x.ntracks_time, axis=1)
    result["mean_sbil"] = result.apply(lambda x: x.mean_sbil / getCB(x.fill), axis=1)
    result.to_csv(resultPath, encoding='utf-8', index=False)


def add_timestamps_to_fills(pltTS, df):
    start_stable = []
    end_stable = []
    for index in df.index:
        start_date = pltTS.loc[index, "start_stable_beam"]
        end_date = pltTS.loc[index, "end_stable_beam"]

        start_stable.append((start_date + pd.Timedelta(minutes=5)).round(freq="5T"))
        end_stable.append((end_date - pd.Timedelta(minutes=5)).round(freq="5T"))

    df["start"] = start_stable
    df["end"] = end_stable

    df = df[['start', 'end', 'duration']]

    return df


def generate_missing_fills(pltTS):
    """
    Check the results folder and compare it with the decoded fills
    If there are newly decoded fills, create a list of them.
    This can also exclude some fills from the list
    """
    result_files = glob(os.path.join(PLT_PATH, 'BackgroundFraction/results', '????.csv'))
    result_files = [int(pathlib.Path(file).stem) for file in result_files]
    # print(result_files)
    decoded_files = glob(os.path.join(FILE_PATH, '????.root'))
    decoded_files = [int(pathlib.Path(file).stem) for file in decoded_files]
    # print(decoded_files)

    # Excluded fills
    excluded = [8178, 8225, 8381, 8385, 8999, 8957]
    missing_results = [fill for fill in decoded_files if fill not in result_files and fill not in excluded]

    return missing_results


def get_fill_df(args):
    pltTS = pltTimestamps(PLT_PATH)

    if args.list:
        fills_to_run = args.list
    else:
        fills_to_run = generate_missing_fills(pltTS)

    # print(fills_to_run)
    post_to_slack(message_text=f'Bkg will work on: {fills_to_run}')

    # Create a csv file with flls to run
    df = pd.DataFrame(columns=['start', 'end', 'duration'], index=fills_to_run)
    df.index.name = 'fill'

    df.duration = 300
    df = add_timestamps_to_fills(pltTS, df)

    df.to_csv("input_fills.csv", encoding='utf-8', header=True)
    return df


def main(args):
    pltTS = pltTimestamps(PLT_PATH)

    fills_to_run = get_fill_df(args)
    print(fills_to_run)

    for fill, row in fills_to_run.iterrows():
        print(f"Begin bkg calc {fill}")
        post_to_slack(message_text=f"Begin bkg calc {fill}")

        run_fit_scripts(row)
        get_inst_luminosity(row)
        combineLogs(row)

        print(f"Done bkg calc {fill}")
        post_to_slack(message_text=f"Done bkg calc {fill}")


if __name__ == "__main__":
    # Define the command-line arguments
    parser = argparse.ArgumentParser(description='Calculate background fraction')

    # Run on specific fills
    parser.add_argument('--list', nargs='+', type=int, help='List of fills to run on')
    args = parser.parse_args()

    main(args)
    