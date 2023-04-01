import ROOT
from ROOT import RooFit, RooArgSet, RooArgList, RooDataSet, RooGaussian, RooRealVar, RooAddPdf, TCanvas

FillNumber = '8178'
Lumi = "2.5e30"

track_init = 5001
step = 50000

fName = "Fill_" + FillNumber + ".root"
fTitle = "SlopeY distribution of Fill " + FillNumber

ntrack = 0

SlopeY = RooRealVar("SlopeY", "SlopeY", 0, -0.08, 0.1)
track = RooRealVar("track", "track", track_init, track_init + step - 1)
timesec = RooRealVar("timesec", "timesec", 0)

f1 = ROOT.TFile.Open("/mnt/d/Cernbox/data/temp_access/8178.root")
t = f1.Get('T')

arg_set = RooArgSet(track, timesec, SlopeY)

dataRead = RooDataSet("dataRead", "dataset with SlopeY", t, arg_set)

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
dataRead.plotOn(frame1, RooFit.Name("dataSet"))

# Fit data
model.fitTo(dataRead, RooFit.Save())

model.plotOn(frame1, RooFit.Components(RooArgSet(g0)), RooFit.LineColor(ROOT.kRed))
model.plotOn(frame1, RooFit.Components(RooArgSet(g1)), RooFit.LineColor(ROOT.kGreen))
model.plotOn(frame1, RooFit.Components(RooArgSet(g2)), RooFit.LineColor(ROOT.kBlue), RooFit.LineStyle(ROOT.kDashed))


model.plotOn(frame1, RooFit.Name("model"))

# Calculate chi2
chi2 = frame1.chiSquare("model", "dataSet", 8)

# ParamBox
model.paramOn(frame1, RooFit.Layout(0.7), RooFit.Format(("NEU"), RooFit.AutoPrecision(1)))
frame1.getAttText().SetTextSize(0.02)
pt = frame1.findObject("model_paramBox")
pt.AddText(ROOT.Form(f"Chi2/ndof =  {chi2:.2f}"))
ntracks = int(dataRead.sumEntries())
pt.AddText(ROOT.Form(f"Tracks = {ntracks}"))


c1 = TCanvas("c1", "c1", 800, 800)
c1.SetLogy(True)
frame1.Draw()
c1.Draw()

# Int_t t_seg1 = ((RooRealVar *)(dataRead.get(0)->find("timesec")))->getVal();
# Int_t t_seg2 = ((RooRealVar *)(dataRead.get(dataRead.sumEntries() - 1)->find("timesec")))->getVal();
# pt->AddText(Form("time =  %s - %s", &getTime(t_seg1)[0], &getTime(t_seg2)[0]));

# Plot residual distribution
hresid = frame1.residHist("dataSet")
c2 = TCanvas("c2", "c2", 800, 800)
frame2 = SlopeY.frame(RooFit.Range(-0.02, 0.08), RooFit.Title("Residual Distribution"))
frame2.addPlotable(hresid, "P")
frame2.Draw()
c2.Draw()

# Plot pull distribution
hpull = frame1.pullHist()
c3 = TCanvas("c3", "c3", 800, 800)
frame3 = SlopeY.frame(RooFit.Range(-0.02, 0.08), RooFit.Title("Pull Distribution"))
frame3.addPlotable(hpull, "P")
frame3.Draw()
c3.Draw()

c1.SaveAs("sample.png")