from scripts.utilities import FEDtoReadOut
from scripts.plotting import plot_table, plot_box
from ROOT import RooFit, RooArgSet, RooArgList, RooGaussian, RooRealVar, RooAddPdf, TCanvas
from tqdm import tqdm
import ROOT
import pandas as pd
import numpy as np
import uproot
import time

import mplhep as hep
hep.style.use("CMS")


ROOT.gErrorIgnoreLevel = ROOT.kWarning
RooMsgService = ROOT.RooMsgService.instance()
# RooMsgService.Print()
# Remove all
# RooMsgService.setGlobalKillBelow(RooFit.ERROR)

# Remove selected topics
RooMsgService.getStream(1).removeTopic(RooFit.DataHandling)
RooMsgService.getStream(1).removeTopic(RooFit.Eval)
RooMsgService.getStream(1).removeTopic(RooFit.Plotting)
RooMsgService.getStream(1).removeTopic(RooFit.Minimization)


def get_boundary_indices(tree, startTime, endTime):
    """Get indices of the first and last entry in each 5 minute interval"""
    data = tree.arrays(["timesec"], library="pd")
    data.reset_index(inplace=True)
    data.rename(columns={"index": "entry"}, inplace=True)
    data = data[(data.timesec > startTime) & (data.timesec <= endTime)]
    data["timestamp"] = pd.to_datetime(data.timesec.map(str), unit='s')
    bins = pd.date_range(start=pd.to_datetime(startTime, unit='s'), end=pd.to_datetime(endTime, unit='s'), freq='5min')
    data['interval'] = pd.cut(data['timestamp'], bins=bins, labels=bins[:-1])
    boundaries = data.groupby('interval').agg({'entry': ['first', 'last']})
    boundaries.reset_index(inplace=True)
    boundaries.columns = boundaries.columns.droplevel(0)
    df = boundaries.rename(columns={'': 'timestamp', 'first': 'start', 'last': 'end'})
    # print(df)
    return df


def calculate_sigma(table):
    """Calculate absolute sigma for each variable and add to table"""
    var_list = ["SlopeX", "SlopeY", 'ResidualX_ROC0', 'ResidualX_ROC1', 'ResidualX_ROC2',
                'ResidualY_ROC0', 'ResidualY_ROC1', 'ResidualY_ROC2']
    for var in var_list:
        table[f"{var}_sigma"] = abs((table[var] - table[var].mean()) / table[var].std())

    table_filtered = table.copy()
    for var in var_list:
        cut = table_filtered[f"{var}_sigma"] < 5
        table_filtered = table_filtered[cut]

    ntrack_resi = len(table_filtered)

    return table, ntrack_resi


def get_bckg_frac(Fill, startTime, endTime, step):
    """Get background fraction for a given fill and time range"""
    print(f"Processing {Fill} from {startTime} to {endTime}")
    channels = [10, 11, 12, 14, 15]
    FILE_PATH = "/home/nkarunar/track_root_files/"
    # FILE_PATH = "/mnt/d/Cernbox/data/temp_access/"
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

    log_dfs = []
    # print("Total loops", len(indices))
    for h in tqdm(indices.index):
        # print("Loop", h)
        fFile_box = IMG_PATH + "fit_slopeY" + Fill + "_" + str(h) + "_box.png"

        variables = ["timesec", "Channel",
                     "SlopeX", "SlopeY",
                     'ResidualX_ROC0', 'ResidualX_ROC1', 'ResidualX_ROC2',
                     'ResidualY_ROC0', 'ResidualY_ROC1', 'ResidualY_ROC2',
                     'BeamSpotZ_x', 'BeamSpotZ_y']

        subselection = tree.arrays(variables, entry_start=indices.iloc[h]['start'], entry_stop=indices.iloc[h]['end'], library="np")
        table = pd.DataFrame(subselection)

        table['Channel'] = table['Channel'].map(FEDtoReadOut())
        table = table[table["Channel"].isin(channels)]
        # print(table)

        table, ntracks_resi = calculate_sigma(table)

        subselection = table.to_dict('list')

        dataRead = ROOT.RooDataSet.from_numpy({"SlopeY": np.array(subselection["SlopeY"])}, [SlopeY])
        ntracks_time = int(dataRead.sumEntries())
        # print("Entries read: ", ntracks_time)

        t1 = int(indices.iloc[h]['timestamp'].timestamp())
        t2 = int((indices.iloc[h]['timestamp'] + pd.Timedelta(minutes=5)).timestamp()) - 1
        t1_string = time.strftime('%H:%M:%S', time.localtime(t1))
        t2_string = time.strftime('%H:%M:%S', time.localtime(t2))

        # print(f"Processing {t1_string}-{t2_string}")

        log_df = pd.DataFrame()
        if ntracks_time == 0:
            log_df.loc[h, 'fill'] = Fill
            log_df.loc[h, 'channel'] = str(-1)
            log_df.loc[h, 'h'] = str(h)
            log_df.loc[h, 't1'] = str(t1)
            log_df.loc[h, 't2'] = str(t2)
            log_df.loc[h, 'ntracks_time'] = str(ntracks_time)
            log_df.loc[h, 'ntracks_resi'] = str(ntracks_resi)
            log_dfs.append(log_df)
            continue

        frame1 = SlopeY.frame(RooFit.Range(-0.08, 0.12), RooFit.Title(""))
        dataRead.plotOn(frame1, RooFit.Name("dataSet"))

        # Fit data
        model.fitTo(dataRead, RooFit.Verbose(False), RooFit.PrintLevel(-1), RooFit.Save())
        model.plotOn(frame1, RooFit.Components(RooArgSet(sig)), RooFit.LineColor(ROOT.kGreen))
        model.plotOn(frame1, RooFit.Components(RooArgSet(bkg)), RooFit.LineColor(ROOT.kRed))
        model.plotOn(frame1, RooFit.Name("model"))

        # Calculate chi2
        chi2 = frame1.chiSquare("model", "dataSet", 5)

        log_df.loc[h, 'fill'] = Fill
        log_df.loc[h, 'channel'] = str(-1)
        log_df.loc[h, 'h'] = str(h)
        log_df.loc[h, 't1'] = str(t1)
        log_df.loc[h, 't2'] = str(t2)
        log_df.loc[h, 'ntracks_time'] = str(ntracks_time)
        log_df.loc[h, 'ntracks_resi'] = str(ntracks_resi)
        log_df.loc[h, 'bkg_frac'] = bkg_frac.getVal()
        log_df.loc[h, 'bkg_frac_e'] = bkg_frac.getError()
        log_df.loc[h, 'bkg_m0'] = bkg_m0.getVal()
        log_df.loc[h, 'bkg_m0_e'] = bkg_m0.getError()
        log_df.loc[h, 'bkg_s0'] = bkg_s0.getVal()
        log_df.loc[h, 'bkg_s0_e'] = bkg_s0.getError()
        log_df.loc[h, 'BSZ_x'] = table.BeamSpotZ_x.mean()
        log_df.loc[h, 'BSZ_x_std'] = table.BeamSpotZ_x.std()
        # log_df.loc[h, 'BSZ_x'], log_df.loc[h, 'BSZ_x_std'] = getFittedValues(table.BeamSpotZ_x.to_numpy())
        log_df.loc[h, 'BSZ_y'] = table.BeamSpotZ_y.mean()
        log_df.loc[h, 'BSZ_y_std'] = table.BeamSpotZ_y.std()
        # log_df.loc[h, 'BSZ_y'], log_df.loc[h, 'BSZ_y_std'] = getFittedValues(table.BeamSpotZ_y.to_numpy())
        log_df.loc[h, 'chi2'] = chi2

        log_dfs.append(log_df)

        plot_box(model, frame1, chi2, ntracks_time, t1_string, t2_string, h, Fill)
        plot_table(table, h, Fill)

    pd.concat(log_dfs).to_csv(fLogPath, index=False, header=True, mode='w')
