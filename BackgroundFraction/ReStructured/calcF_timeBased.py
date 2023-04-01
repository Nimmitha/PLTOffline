import ROOT
from ROOT import RooFit, RooArgSet, RooArgList, RooDataSet, RooGaussian, RooRealVar, RooAddPdf, TCanvas

FillNumber = "8236"
StartTime = 1665152400
# EndTime = 1665196200
EndTime = 1665152400 + 500
step = 300


# def calcF_timeBased(FillNumber, StartTime, EndTime, step):
ROOT.gErrorIgnoreLevel = ROOT.kWarning
RooMsgService = ROOT.RooMsgService.instance()
RooMsgService.Print()

# Remove all
# RooMsgService.setGlobalKillBelow(RooFit.ERROR)

# Remove selected topics
# RooMsgService.getStream(1).removeTopic(RooFit.DataHandling)
# RooMsgService.getStream(1).removeTopic(RooFit.Eval)
# RooMsgService.getStream(1).removeTopic(RooFit.Plotting)
# RooMsgService.getStream(1).removeTopic(RooFit.Minimization)


FILE_PATH = "/mnt/d/CernBox/data/temp_access/"
IMG_PATH = "plots/"
fName = FillNumber
fPath = FILE_PATH + fName + ".root"
fLogPath = "logs/" + fName + "F.csv"
ntracks_resi = 0
ntracks_time = 0
f1 = ROOT.TFile.Open(fPath)
t = f1.Get("T")
SlopeY = ROOT.RooRealVar("SlopeY", "SlopeY", 0)
ResidualX_ROC0 = ROOT.RooRealVar("ResidualX_ROC0", "ResidualX_ROC0", -1, 1)
ResidualX_ROC1 = ROOT.RooRealVar("ResidualX_ROC1", "ResidualX_ROC1", -1, 1)
ResidualX_ROC2 = ROOT.RooRealVar("ResidualX_ROC2", "ResidualX_ROC2", -1, 1)
ResidualY_ROC0 = ROOT.RooRealVar("ResidualY_ROC0", "ResidualY_ROC0", -1, 1)
ResidualY_ROC1 = ROOT.RooRealVar("ResidualY_ROC1", "ResidualY_ROC1", -1, 1)
ResidualY_ROC2 = ROOT.RooRealVar("ResidualY_ROC2", "ResidualY_ROC2", -1, 1)
BeamSpotZ_x = ROOT.RooRealVar("BeamSpotZ_x", "BeamSpotZ_x", -20, 20)
BeamSpotZ_y = ROOT.RooRealVar("BeamSpotZ_y", "BeamSpotZ_y", -20, 20)
timesec = ROOT.RooRealVar("timesec", "timesec", StartTime, EndTime - 1)
variables = ROOT.RooArgSet(timesec, SlopeY, ResidualX_ROC0, ResidualX_ROC1, ResidualX_ROC2, ResidualY_ROC0, ResidualY_ROC1, ResidualY_ROC2)
variables.add(BeamSpotZ_x)
variables.add(BeamSpotZ_y)
dataRead = ROOT.RooDataSet("dataRead", "Main dataset", t, variables)
print("Entries read: ", dataRead.sumEntries())
h_max = int((EndTime - StartTime) / step)
print("Starting loop. h_max = ", h_max)
RcutVal = ROOT.RooRealVar("RcutVal", "RcutVal", 0.09)
var_Rcut = ROOT.RooFormulaVar("var_Rcut", "sqrt(@0 * @0 + @3 * @3) + sqrt(@1 * @1 + @4 * @4) + sqrt(@2 * @2 + @5 * @5) < @6",
                              ROOT.RooArgList(ResidualX_ROC0, ResidualX_ROC1, ResidualX_ROC2, ResidualY_ROC0, ResidualY_ROC1, ResidualY_ROC2, RcutVal))

with open("test.txt", 'w') as myfile:
    myfile.write("fill,h,t1,t2,ntracks_time,ntracks_resi,bkg_frac,bkg_frac_e,bkg_m0,bkg_m0_e,bkg_s0,bkg_s0_e,BS_X,BS_X_std,BS_Y,BS_Y_std,chi2\n")

for h in range(h_max):
    print(h)
    # continue
    fFile_box = IMG_PATH + "fit_slopeY" + FillNumber + "_" + str(h) + "_box.png"
    t1 = StartTime + h * step
    t2 = t1 + step - 1
    print(f"Processing {t1}-{t2}")
    timesec.setRange("time_range", t1, t2)
    data_timeReduced = dataRead.reduce(RooFit.CutRange("time_range"), RooFit.Name("data_timeReduced"))
    ntracks_time = data_timeReduced.sumEntries()
    print(f"Tracks in the selected range: {ntracks_time}")
    data_ResiReduced = data_timeReduced.reduce(var_Rcut)
    ntracks_resi = data_ResiReduced.sumEntries()
    print(f"Tracks after the residual cut: {ntracks_resi}")
    if ntracks_time == 0:
        with open("test.txt", 'a') as myfile:
            myfile.print(f"{FillNumber},{h},{t1},{t2},{ntracks_time},{ntracks_resi},0,0,0,0,0,0,0,0,0,0,0")
        continue

    # Define Gaussian
    m0 = RooRealVar("m0", "mean 0", 0.026965, 0.02, 0.03)
    m1 = RooRealVar("m1", "mean 1", 0.02618)
    m2 = RooRealVar("m2", "mean 2", 0.0295)
    s0 = RooRealVar("s0", "sigma 0", 0.001275, 0.0005, 0.0017)
    s1 = RooRealVar("s1", "sigma 1", 0.0036)
    s2 = RooRealVar("s2", "sigma 2", 0.0151)
    g0 = RooGaussian("g0", "gaussian PDF 0", SlopeY, m0, s0)
    g1 = RooGaussian("g1", "gaussian PDF 1", SlopeY, m1, s1)
    g2 = RooGaussian("g2", "gaussian PDF 2", SlopeY, m2, s2)
    histZ_x = data_timeReduced.createHistogram("BeamSpot X", BeamSpotZ_x, RooFit.Binning(50, -10, 10))
    histZ_y = data_timeReduced.createHistogram("BeamSpot Y", BeamSpotZ_y, RooFit.Binning(50, -10, 10))
    # Define Signal
    frac0 = RooRealVar("frac0", "fraction 0", 0.804)
    frac1 = RooRealVar("frac1", "fraction 1", 0.124)
    sig = RooAddPdf("sig", "g0+g1+g2", RooArgList(g0, g1, g2), RooArgList(frac0, frac1))
    # Define background
    bkg_m0 = RooRealVar("bkg_m0", "bkg_m0", 0.026, 0.01, 0.04)
    bkg_s0 = RooRealVar("bkg_s0", "bkg_s0", 0.018, 0.01, 0.1)
    bkg_frac = RooRealVar("bkg_frac", "bkg_frac", 0.011, 0., 0.5)
    bkg = RooGaussian("bkg", "bkg", SlopeY, bkg_m0, bkg_s0)
    # Define Model
    model = RooAddPdf("model", "model (fggg + g)", RooArgList(bkg, sig), bkg_frac)
    frame1 = SlopeY.frame(RooFit.Range(-0.08, 0.12), RooFit.Title(""))
    data_timeReduced.plotOn(frame1, RooFit.Name("dataSet"))
    # Fit data
    model.fitTo(data_timeReduced, RooFit.Verbose(False), RooFit.PrintLevel(-1), RooFit.Save())
    model.plotOn(frame1, RooFit.Components(RooArgSet(sig)), RooFit.LineColor(ROOT.kGreen))
    model.plotOn(frame1, RooFit.Components(RooArgSet(bkg)), RooFit.LineColor(ROOT.kRed))
    model.plotOn(frame1, RooFit.Name("model"))
    # Calculate chi2
    chi2 = frame1.chiSquare("model", "dataSet", 5)
    rh = frame1.findObject("dataSet")
    N = rh.GetN()
    for i in range(N):
        x = rh.GetPointX(i)
        y = rh.GetPointY(i)
        # rh.GetPoint(i, x, y)
        if y == 0.0:
            rh.SetPointError(i, 0., 0., 0., 0.)
    # StartTime new canvas (box)
    c_box = TCanvas("c_box", "c_box", 800, 700)
    c_box.GetPad(0).SetLogy()
    frame1.SetMaximum(1e6)
    frame1.SetMinimum(0.2)
    frame1.GetYaxis().SetTitleOffset(1.2)
    frame1.GetYaxis().SetTitleSize(0.04)
    # ParamBox
    model.paramOn(frame1, RooFit.Layout(0.7), RooFit.Format(("NEU"), RooFit.AutoPrecision(1)))
    frame1.getAttText().SetTextSize(0.02)
    pt = frame1.findObject("model_paramBox")
    pt.AddText(ROOT.Form(f"Chi2/ndof =  {chi2:.2f}"))
    pt.AddText(ROOT.Form(f"Tracks =  {ntracks_time}"))
    t1_data = t1

    hr = int(t1_data / 3600)
    min = int((t1_data - (hr * 3600)) / 60)
    sec = int(t1_data % 60)
    t1_data_s = "{:02d}:{:02d}:{:02d}".format(hr, min, sec)

    t2_data = t2
    hr = int(t2_data / 3600)
    min = int((t2_data - (hr * 3600)) / 60)
    sec = int(t2_data % 60)
    t2_data_s = "{:02d}:{:02d}:{:02d}".format(hr, min, sec)

    pt.AddText('timesec = {} - {}'.format(t1_data_s, t2_data_s))
    frame1.Draw()
    c_box.SaveAs(fFile_box)

    with open('output.csv', 'a') as myfile:
        myfile.write(f'{FillNumber},{h},{t1_data},{t2_data},{ntracks_time},{ntracks_resi},{bkg_frac.getVal()},{bkg_frac.getError()},{bkg_m0.getVal()},{bkg_m0.getError()},{bkg_s0.getVal()},{bkg_s0.getError()},{histZ_x.GetMean()},{histZ_x.GetStdDev()},{histZ_y.GetMean()},{histZ_y.GetStdDev()},{chi2}')

    break
