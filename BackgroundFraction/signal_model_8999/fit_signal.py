import time
import uproot4 as uproot
import numpy as np
import pandas as pd
import ROOT
from ROOT import RooFit, RooArgSet, RooArgList, RooDataSet, RooGaussian, RooRealVar, RooAddPdf, TCanvas

from utilities import FEDtoReadOut


Fill = '8999'
Lumi = "10e30"

FILE_PATH = "/home/nkarunar/track_root_files/"
fPath = FILE_PATH + Fill + ".root"

channels = [10, 11, 12, 14, 15]
# channels = [10]

fTitle = "SlopeY distribution of Fill " + Fill

# open file using uproot
file = uproot.open(fPath)
tree = file["T"]

SlopeY = RooRealVar("SlopeY", "SlopeY", 0)

variables = ["timesec", "Channel",
                 "SlopeX", "SlopeY",
                 'ResidualX_ROC0', 'ResidualX_ROC1', 'ResidualX_ROC2',
                 'ResidualY_ROC0', 'ResidualY_ROC1', 'ResidualY_ROC2',
                 'BeamspotX_y', 'BeamspotX_z',
                 'BeamspotY_x', 'BeamspotY_z',
                 'BeamSpotZ_x', 'BeamSpotZ_y']

subselection = tree.arrays(variables,  library="np")
table = pd.DataFrame(subselection)

pd.to_datetime(table.timesec, unit='s')
table['Channel'] = table['Channel'].map(FEDtoReadOut())

# Region A
# 2023-06-29 01:37
# 2023-06-29 05:12
regA_1 = int((pd.Timestamp("2023-06-29 12:53") - pd.Timedelta(hours=2)).timestamp())
regA_2 = int((pd.Timestamp("2023-06-29 13:10") - pd.Timedelta(hours=2)).timestamp())
table = table[(table.timesec > regA_1) & (table.timesec < regA_2)]

table = table[table["Channel"].isin(channels)]
subselection = table.to_dict('list')

dataRead = ROOT.RooDataSet.from_numpy({"SlopeY": np.array(subselection["SlopeY"])}, [SlopeY])
ntracks_time = int(dataRead.sumEntries())
print("Entries read: ", ntracks_time)

t1 = table['timesec'].iat[0]
t2 = table["timesec"].iat[-1]
t1_string = time.strftime('%H:%M:%S', time.localtime(t1))
t2_string = time.strftime('%H:%M:%S', time.localtime(t2))

print(f"Processing {t1_string}-{t2_string}")

# Define Gaussian
m0 = RooRealVar("m0", "mean 0", 0.027, 0.01, 0.05)
m1 = RooRealVar("m1", "mean 1", 0.026, 0.01, 0.05)
m2 = RooRealVar("m2", "mean 2", 0.030, 0.01, 0.05)

s0 = RooRealVar("s0", "sigma 0", 0.001, 0., 0.01)
s1 = RooRealVar("s1", "sigma 1", 0.001, 0., 0.01)
s2 = RooRealVar("s2", "sigma 2", 0.02, 0., 0.1)

g0 = RooGaussian("g0", "gaussian PDF 0", SlopeY, m0, s0)
g1 = RooGaussian("g1", "gaussian PDF 1", SlopeY, m1, s1)
g2 = RooGaussian("g2", "gaussian PDF 2", SlopeY, m2, s2)

# Define model
frac0 = RooRealVar("frac0", "fraction 0", 0.8, 0.5, 1.0)
frac1 = RooRealVar("frac1", "fraction 1", 0.1, 0.0, 0.5)
model = RooAddPdf("model", "g0+g1+g2", RooArgList(g0, g1, g2), RooArgList(frac0, frac1))

# model = RooAddPdf("model", "g0+g1+g2", RooArgList(g0, g1), RooArgList(frac0))

# Construct a plot frame
frame1 = SlopeY.frame(RooFit.Range(-0.02, 0.08), RooFit.Title(fTitle))

#Plot data in frame
tbins = ROOT.RooBinning(-0.02, 0.08)
tbins.addUniform(30, -0.02, 0.08)
dataRead.plotOn(frame1, RooFit.Name("dataSet"), Binning=tbins)# ROOT.RooBinning(-0.02, 0.08))

# Fit data
model.fitTo(dataRead, RooFit.Save())

model.plotOn(frame1, RooFit.Components(RooArgSet(g0)), RooFit.LineColor(ROOT.kRed))
model.plotOn(frame1, RooFit.Components(RooArgSet(g1)), RooFit.LineColor(ROOT.kGreen))
model.plotOn(frame1, RooFit.Components(RooArgSet(g2)), RooFit.LineColor(ROOT.kBlue), RooFit.LineStyle(ROOT.kDashed))

model.plotOn(frame1, RooFit.Name("model"))

# Calculate chi2
chi2 = frame1.chiSquare("model", "dataSet", 8)

# ParamBox
model.paramOn(frame1, RooFit.Layout(0.7), RooFit.Format("NEU", RooFit.AutoPrecision(1)))
frame1.getAttText().SetTextSize(0.02)
pt = frame1.findObject("model_paramBox")
pt.AddText(ROOT.Form(f"Chi2/ndof =  {chi2:.2f}"))
ntracks = int(dataRead.sumEntries())
pt.AddText(ROOT.Form(f"Tracks = {ntracks}"))
pt.AddText(f'timesec = {t1_string} - {t2_string}')

# This is weird. Fill color also covers the boarder so the line is not visible.
frame1.getAttFill('model_paramBox').SetFillStyle(1001)
# frame1.getAttFill('model_paramBox').SetFillStyle(1001)
# frame1.getAttFill('model_paramBox').SetFillColor(19)
# frame1.getAttLine('model_paramBox').SetLineColor(ROOT.kBlack)
# https://root-forum.cern.ch/t/remove-box-in-paramon/19781/2

c1 = TCanvas("c1", "c1", 800, 800)
c1.SetLogy(True)
frame1.Draw()
c1.Draw()
c1.SaveAs("siganal_ggg.png")

# Plot residual distribution
hresid = frame1.residHist("dataSet")
c2 = TCanvas("c2", "c2", 800, 800)
frame2 = SlopeY.frame(RooFit.Range(-0.02, 0.08), RooFit.Title("Residual Distribution"))
frame2.addPlotable(hresid, "P")
frame2.Draw()
c2.Draw()
c2.SaveAs("signal_residual.png")

# Plot pull distribution
hpull = frame1.pullHist()
c3 = TCanvas("c3", "c3", 800, 800)
frame3 = SlopeY.frame(RooFit.Range(-0.02, 0.08), RooFit.Title("Pull Distribution"))
frame3.addPlotable(hpull, "P")
frame3.Draw()
c3.Draw()
c3.SaveAs("signal_pull.png")
