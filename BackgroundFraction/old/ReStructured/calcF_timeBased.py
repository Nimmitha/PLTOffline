import time
# import uproot4 as uproot

import mplhep as hep
hep.style.use("CMS")
# import uproot4 as uproot
import uproot
import numpy as np
import pandas as pd
import ROOT
from ROOT import RooFit, RooArgSet, RooArgList, RooGaussian, RooRealVar, RooAddPdf, TCanvas

from plotting import plot_table, plot_box
from utilities import FEDtoReadOut

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

# Fill = "8236"
# FILE_PATH = "/mnt/d/CernBox/data/temp_access/"
# fPath = FILE_PATH + Fill + ".root"

# IMG_PATH = "plots/"
# fLogPath = "logs/" + Fill + "F.csv"

# startTime = 1665152400
# endTime = 1665196200
# # endTime = 1665152400 + 1000
# # step = 300

# channels = [10, 11, 12, 14, 15]    # -1 for all channels

# # open file using uproot
# file = uproot.open(fPath)
# tree = file["T"]


def get_boundary_indices(tree, startTime, endTime):
    print(startTime, endTime)
    # print("Type of startTime", type(startTime))
    # print("Type of endTime", type(endTime))
    """Get indices of the first and last entry in each 5 minute interval"""
    data = tree.arrays(["timesec"], library="pd")
    data.reset_index(inplace=True)
    data.rename(columns={"index": "entry"}, inplace=True)
    data = data[(data.timesec > startTime) & (data.timesec <= endTime)]
    # print(data)
    # return data
    data["timestamp"] = pd.to_datetime(data.timesec.map(str), unit='s') #+ pd.Timedelta(seconds=1) #- pd.Timedelta(seconds=150)
    # print(data)
    # bins = pd.date_range(start=data['timestamp'].min(), end=data['timestamp'].max(), freq='5min')
    bins = pd.date_range(start=pd.to_datetime(startTime, unit='s'), end=pd.to_datetime(endTime, unit='s'), freq='5min')
    # print(bins)
    data['interval'] = pd.cut(data['timestamp'], bins=bins, labels=bins[:-1])
    # print(data)
    boundaries = data.groupby('interval').agg({'entry': ['first', 'last']})
    boundaries.reset_index(inplace=True)
    boundaries.columns = boundaries.columns.droplevel(0)
    df = boundaries.rename(columns={'': 'timestamp', 'first': 'start', 'last': 'end'})
    # print(df)
    return df




    # data['round'] = data.timestamp.dt.round('5min')
    # print(data)
    # indices = np.where(data['round'].diff() != pd.Timedelta(days=0))[0]
    # print(indices)
    # indices = np.append(indices, len(data)-1)

    # print(indices)
    # print(len(indices))
    # time_at_indices = data.iloc[indices]['round']
    # print(time_at_indices.to_list())
    # print(len(time_at_indices))

    return indices


# indices = get_boundary_indices(tree)

# total_data = 0
# for i in range(len(indices)-1):
#     # print(indices[i], indices[i+1])
#     new_data = tree.arrays("timesec", entry_start=indices[i], entry_stop=indices[i+1], library="np")['timesec']
#     total_data += len(new_data)
#     print(new_data[0], new_data[-1])
# print(total_data)

def get_bckg_frac(Fill, startTime, endTime, step):
    # Fill = "8236"
    channels = [10, 11, 12, 14, 15] 
    # FILE_PATH = "/home/nkarunar/track_root_files/"
    FILE_PATH = "/mnt/d/Cernbox/data/temp_access/"
    fPath = FILE_PATH + Fill + ".root"

    IMG_PATH = "plots/"
    fLogPath = "logs/" + Fill + "F.csv"
    file = uproot.open(fPath)
    tree = file["T"]
    indices = get_boundary_indices(tree, startTime, endTime)
    


    SlopeY = ROOT.RooRealVar("SlopeY", "SlopeY", 0)
    m0 = RooRealVar("m0", "mean 0", 0.026817, 0.02, 0.03)
    m1 = RooRealVar("m1", "mean 1", 0.02604)
    m2 = RooRealVar("m2", "mean 2", 0.0297)
    s0 = RooRealVar("s0", "sigma 0", 0.001268, 0.0005, 0.0017)
    s1 = RooRealVar("s1", "sigma 1", 0.0038)
    s2 = RooRealVar("s2", "sigma 2", 0.0153)
    g0 = RooGaussian("g0", "gaussian PDF 0", SlopeY, m0, s0)
    g1 = RooGaussian("g1", "gaussian PDF 1", SlopeY, m1, s1)
    g2 = RooGaussian("g2", "gaussian PDF 2", SlopeY, m2, s2)

    # Define Signal
    frac0 = RooRealVar("frac0", "fraction 0", 0.822)
    frac1 = RooRealVar("frac1", "fraction 1", 0.111)
    sig = RooAddPdf("sig", "g0+g1+g2", RooArgList(g0, g1, g2), RooArgList(frac0, frac1))

    # Define background
    bkg_m0 = RooRealVar("bkg_m0", "bkg_m0", 0.026, 0.01, 0.04)
    bkg_s0 = RooRealVar("bkg_s0", "bkg_s0", 0.018, 0.01, 0.1)
    bkg_frac = RooRealVar("bkg_frac", "bkg_frac", 0.011, 0., 0.5)
    bkg = RooGaussian("bkg", "bkg", SlopeY, bkg_m0, bkg_s0)

    # Define Model
    model = RooAddPdf("model", "model (fggg + g)", RooArgList(bkg, sig), bkg_frac)


    log_cols = ["fill", "channel", "h", "t1", "t2",
                "ntracks_time", "ntracks_resi",
                "bkg_frac", "bkg_frac_e", "bkg_m0", "bkg_m0_e", "bkg_s0", "bkg_s0_e",
                "BSX_y", "BSX_y_std", "BSX_z", "BSX_z_std",
                "BSY_x", "BSY_x_std", "BSY_z", "BSY_z_std",
                "BSZ_x", "BSZ_x_std", "BSZ_y", "BSZ_y_std",
                "chi2"]
    log_dict = {key: [] for key in log_cols}

    log_df = pd.DataFrame(log_dict)
    log_df.to_csv(fLogPath, index=False, header=True, mode='w')

    # with open(fLogPath, 'w', encoding='utf-8') as myfile:
    #     myfile.write("fill,h,t1,t2,ntracks_time,ntracks_resi,bkg_frac,bkg_frac_e,bkg_m0,bkg_m0_e,bkg_s0,bkg_s0_e,BS_X,BS_X_std,BS_Y,BS_Y_std,chi2\n")

    print("Total loops", len(indices))

    for h in indices.index:
        print("Loop", h)
        fFile_box = IMG_PATH + "fit_slopeY" + Fill + "_" + str(h) + "_box.png"

        variables = ["timesec", "Channel",
                    "SlopeX", "SlopeY",
                    'ResidualX_ROC0', 'ResidualX_ROC1', 'ResidualX_ROC2',
                    'ResidualY_ROC0', 'ResidualY_ROC1', 'ResidualY_ROC2',
                    'BeamspotX_y', 'BeamspotX_z',
                    'BeamspotY_x', 'BeamspotY_z',
                    'BeamSpotZ_x', 'BeamSpotZ_y']

        subselection = tree.arrays(variables, entry_start=indices.iloc[h]['start'], entry_stop=indices.iloc[h]['end'], library="np")
        table = pd.DataFrame(subselection)

        table['Channel'] = table['Channel'].map(FEDtoReadOut())
        table = table[table["Channel"].isin(channels)]
        print(table)

        subselection = table.to_dict('list')
        # print(subselection["SlopeY"])
        

        # print("Number of entries in this:", len(subselection['SlopeY']))
        dataRead = ROOT.RooDataSet.from_numpy({"SlopeY": np.array(subselection["SlopeY"])}, [SlopeY])
        ntracks_time = int(dataRead.sumEntries())
        print("Entries read: ", ntracks_time)

        t1 = int(indices.iloc[h]['timestamp'].timestamp())
        t2 = int((indices.iloc[h]['timestamp'] + pd.Timedelta(minutes=5)).timestamp()) - 1

        # t1_string = indices.iloc[h]['timeestamp']
        # t2_string = indices.iloc[h]['timeestamp'] + pd.Timedelta(minutes=5)

        # t1 = table['timesec'].iat[0]
        # t2 =  table["timesec"].iat[-1]
        t1_string = time.strftime('%H:%M:%S', time.localtime(t1))
        t2_string = time.strftime('%H:%M:%S', time.localtime(t2))

        print(f"Processing {t1_string}-{t2_string}")

        if ntracks_time == 0:
            new_row = [Fill, -1, h, t1, t2, ntracks_time] + [0] * 20
            log_df.loc[len(log_df)] = new_row

        frame1 = SlopeY.frame(RooFit.Range(-0.08, 0.12), RooFit.Title(""))
        dataRead.plotOn(frame1, RooFit.Name("dataSet"))

        # Fit data
        model.fitTo(dataRead, RooFit.Verbose(False), RooFit.PrintLevel(-1), RooFit.Save())
        model.plotOn(frame1, RooFit.Components(RooArgSet(sig)), RooFit.LineColor(ROOT.kGreen))
        model.plotOn(frame1, RooFit.Components(RooArgSet(bkg)), RooFit.LineColor(ROOT.kRed))
        model.plotOn(frame1, RooFit.Name("model"))
        
        # Calculate chi2
        chi2 = frame1.chiSquare("model", "dataSet", 5)

        ntracks_resi = 0

        new_row = [Fill, str(-1), h, t1, t2,
                ntracks_time, ntracks_resi,
                bkg_frac.getVal(), bkg_frac.getError(),
                bkg_m0.getVal(), bkg_m0.getError(),
                bkg_s0.getVal(), bkg_s0.getError(),
                table.BeamspotX_y.mean(), table.BeamspotX_y.std(),
                table.BeamspotX_z.mean(), table.BeamspotX_z.std(),
                table.BeamspotY_x.mean(), table.BeamspotY_x.std(),
                table.BeamspotY_z.mean(), table.BeamspotY_z.std(),
                table.BeamSpotZ_x.mean(), table.BeamSpotZ_x.std(),
                table.BeamSpotZ_y.mean(), table.BeamSpotZ_y.std(),
                chi2]
        
        print(new_row)
        log_df.loc[len(log_df)] = new_row
        plot_box(model, frame1, chi2, ntracks_time, t1_string, t2_string, h, Fill)
        plot_table(table, h, Fill)

    log_df.to_csv(fLogPath, index=False, header=False, mode='a')
