
{
  using namespace RooFit;

  std::string FillNumber = "8178";
  std::string Lumi = "2.5E30";

  uint32_t track_init = 5001;
  uint32_t step = 50000;

  std::string fNameString = "Fill_" + FillNumber + ".root";
  const char *fName = &fNameString[0];

  Int_t ntracks;
  TFile f1(fName);
  TTree *t;
  f1.GetObject("T", t);

  // Define file names
  std::string fTitleString = "SlopeY distribution of Fill " + FillNumber;
  const char *fTitle = &fTitleString[0];

  std::string fFileString = "rp_ggg_" + FillNumber + ".png";
  const char *fFile = &fFileString[0];

  std::string fsFileString = "ggg_" + FillNumber + ".png";
  const char *fsFile = &fsFileString[0];

  // Declare variables x,mean,sigma with associated name, title, initial value and allowed range
  RooRealVar SlopeY("SlopeY", "SlopeY", 0, -0.08, 0.1);
  RooRealVar track("track", "track", track_init, track_init + step - 1);
  RooRealVar timesec("timesec", "timesec", 0);

  // Read tree
  RooDataSet dataRead("dataRead", "dataset with SlopeY", t, RooArgSet(track, timesec, SlopeY));
  dataRead.Print("V");

  // Define Gaussian
  RooRealVar m0("m0", "mean 0", 0.027, 0.01, 0.05);
  RooRealVar m1("m1", "mean 1", 0.026, 0.01, 0.05);
  RooRealVar m2("m2", "mean 2", 0.030, 0.01, 0.05);

  RooRealVar s0("s0", "sigma 0", 0.001, 0., 0.01);
  RooRealVar s1("s1", "sigma 1", 0.004, 0., 0.01);
  RooRealVar s2("s2", "sigma 2", 0.020, 0., 0.1);

  RooGaussian g0("g0", "gaussian PDF 0", SlopeY, m0, s0);
  RooGaussian g1("g1", "gaussian PDF 1", SlopeY, m1, s1);
  RooGaussian g2("g2", "gaussian PDF 2", SlopeY, m2, s2);

  // Define Model
  RooRealVar frac0("frac0", "fraction 0", 0.8, 0.5, 1.0);
  RooRealVar frac1("frac1", "fraction 1", 0.1, 0.0, 0.5);
  RooAddPdf model("model", "g0+g1+g2", RooArgList(g0, g1, g2), RooArgList(frac0, frac1));

  // Construct plot frame
  RooPlot *frame1 = SlopeY.frame(Range(-0.02, 0.08), Title(fTitle));

  // Plot data in frame
  dataRead.plotOn(frame1, Name("dataSet"));

  // Fit data
  model.fitTo(dataRead, Save());

  model.plotOn(frame1, Components(RooArgSet(g0)), LineColor(kRed));
  model.plotOn(frame1, Components(RooArgSet(g1)), LineColor(kGreen));
  model.plotOn(frame1, Components(RooArgSet(g2)), LineColor(kBlue), LineStyle(kDashed));

  model.plotOn(frame1, Name("model"));

  //Show residual and pull
  RooHist *hresid = frame1->residHist("dataSet");
  RooPlot *frame2 = SlopeY.frame(Range(-0.02, 0.08), Title("Residual Distribution"));
  frame2->addPlotable(hresid, "P");

  RooHist *hpull = frame1->pullHist();
  RooPlot *frame3 = SlopeY.frame(Range(-0.02, 0.08), Title("Pull Distribution"));
  frame3->addPlotable(hpull, "P");

  //Start new Canvas
  TCanvas *c1 = new TCanvas("c1", "c1", 1280, 720);
  c1->Divide(3, 1);

  c1->cd(1);
  gPad->SetLeftMargin(0.15);
  frame1->GetYaxis()->SetTitleOffset(1.6);
  c1->GetPad(1)->SetLogy();
  frame1->Draw();

  c1->cd(2);
  gPad->SetLeftMargin(0.15);
  frame2->GetYaxis()->SetTitleOffset(1.6);
  frame2->Draw();

  c1->cd(3);
  gPad->SetLeftMargin(0.15);
  frame3->GetYaxis()->SetTitleOffset(1.6);
  frame3->Draw();

  c1->SaveAs(fFile);

  // Second canvas
  TCanvas *c2 = new TCanvas("c2", "c2", 1000, 900);
  c2->GetPad(0)->SetLogy();

  // Calculate chi2
  Double_t chi2 = frame1->chiSquare("model", "dataSet", 8);

  //frame1->GetXaxis()->SetLabelSize(0.05);
  frame1->GetXaxis()->SetTitleOffset(1.25);

  //frame1->GetYaxis()->SetLabelSize(0.05);
  frame1->GetYaxis()->SetTitleOffset(1.2);

  //frame1->SetMaximum(16000);
  //frame1->SetMinimum(0);

  // ParamBox
  model.paramOn(frame1, Layout(0.7), Format(("NEU"), AutoPrecision(1)));
  frame1->getAttText()->SetTextSize(0.02);
  TPaveText *pt = (TPaveText *)frame1->findObject("model_paramBox");
  pt->AddText(Form("#chi^{2} /ndof =  %f", chi2));
  ntracks = dataRead.sumEntries();
  pt->AddText(Form("Tracks = %i", ntracks));
  Int_t t_seg1 = ((RooRealVar *)(dataRead.get(0)->find("timesec")))->getVal();
  Int_t t_seg2 = ((RooRealVar *)(dataRead.get(dataRead.sumEntries() - 1)->find("timesec")))->getVal();
  pt->AddText(Form("time =  %s - %s", &getTime(t_seg1)[0], &getTime(t_seg2)[0]));

  frame1->Draw();
  c2->SaveAs(fsFile);
}

Int_t tofTime(uint32_t hh, uint32_t mm, uint32_t ss)
{
  return (hh * 3600 + mm * 60 + ss);
}

std::string getTime(uint32_t seconds)
{
  // A utility function which returns the time in readable format.
  std::stringstream buf;

  int hr = seconds / 3600;
  int min = (seconds - (hr * 3600)) / 60;
  int sec = seconds % 60;
  buf << std::setfill('0') << std::setw(2)
      << hr << ":" << std::setw(2) << min << ":" << std::setw(2) << sec;
  return buf.str();
}
