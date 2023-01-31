#include <iostream>
#include <fstream>

void calcF_timeBased(std::string FillNumber, Int_t StartTime, Int_t EndTime, Int_t step)
{
    using namespace RooFit;
    //gErrorIgnoreLevel = kWarning;
    RooMsgService::instance().getStream(1).removeTopic(DataHandling);
    RooMsgService::instance().getStream(1).removeTopic(Eval);
    RooMsgService::instance().getStream(1).removeTopic(Plotting);
    RooMsgService::instance().getStream(1).removeTopic(Minimization);
    //RooMsgService::instance().setStreamStatus(1, false);

    Double_t t1, t2;

    Int_t t1_data, t2_data;
    Int_t hr, min, sec;
    std::stringstream string_buffer;
    std::string t1_data_s, t2_data_s;
    
    std::string FILE_PATH = "/home/nkarunar/root_files/";
    std::string IMG_PATH = "plots/";

    // std::string fName = FillNumber + "_" + std::to_string(StartTime) + "_" + std::to_string(EndTime);
    std::string fName = FillNumber;
    std::string fPathString = FILE_PATH  + fName + ".root";
    const char *fPath = &fPathString[0];

    std::string fLogPathString = "logs/" + fName + "F.csv";
    const char *fLogPath = &fLogPathString[0];

    Int_t ntracks_resi, ntracks_time;
    TFile f1(fPath);
    TTree *t;
    f1.GetObject("T", t);

    RooRealVar SlopeY("SlopeY", "SlopeY", 0);
    RooRealVar ResidualX_ROC0("ResidualX_ROC0", "ResidualX_ROC0", -1, 1);
    RooRealVar ResidualX_ROC1("ResidualX_ROC1", "ResidualX_ROC1", -1, 1);
    RooRealVar ResidualX_ROC2("ResidualX_ROC2", "ResidualX_ROC2", -1, 1);
    RooRealVar ResidualY_ROC0("ResidualY_ROC0", "ResidualY_ROC0", -1, 1);
    RooRealVar ResidualY_ROC1("ResidualY_ROC1", "ResidualY_ROC1", -1, 1);
    RooRealVar ResidualY_ROC2("ResidualY_ROC2", "ResidualY_ROC2", -1, 1);
    RooRealVar BeamSpotZ_x("BeamSpotZ_x", "BeamSpotZ_x", -20, 20);
    RooRealVar BeamSpotZ_y("BeamSpotZ_y", "BeamSpotZ_y", -20, 20);
    RooRealVar timesec("timesec", "timesec", StartTime, EndTime - 1);
    //RooRealVar Channel("Channel", "Channel", 12, 21);

    std::cout << "Reading range [" << StartTime << ", " << EndTime << ")" << std::endl;

    auto variables = new RooArgSet(timesec, SlopeY, ResidualX_ROC0, ResidualX_ROC1, ResidualX_ROC2, ResidualY_ROC0, ResidualY_ROC1, ResidualY_ROC2);
    variables->add(BeamSpotZ_x);
    variables->add(BeamSpotZ_y);

    RooDataSet dataRead("dataRead", "Main dataset", t, *variables);
    std::cout << "Entries read: " << dataRead.sumEntries() << std::endl;

    Int_t h_max = (Int_t)(EndTime - StartTime) / step;
    std::cout << "Starting loop. h_max = " << h_max << std::endl;

    RooRealVar RcutVal("RcutVal", "RcutVal", 0.09);
    RooFormulaVar *var_Rcut = new RooFormulaVar("var_Rcut", "sqrt(@0 * @0 + @3 * @3) + sqrt(@1 * @1 + @4 * @4) + sqrt(@2 * @2 + @5 * @5) < @6",
                                                RooArgList(ResidualX_ROC0, ResidualX_ROC1, ResidualX_ROC2, ResidualY_ROC0, ResidualY_ROC1, ResidualY_ROC2, RcutVal));

    std::ofstream myfile;
    //myfile << "Whats going on in this line\n";
    myfile.open(fLogPath);
    myfile << "fill" << "," << "h" << "," 
        << "t1" << "," << "t2" << "," 
        << "ntracks_time" << "," << "ntracks_resi" << ","
        << "bkg_frac" << "," << "bkg_frac_e" << "," 
        << "bkg_m0" << "," << "bkg_m0_e" << "," 
        << "bkg_s0" << "," << "bkg_s0_e" << "," 
        << "BS_X" << "," << "BS_X_std" << ","
        << "BS_Y" << "," << "BS_Y_std" << ","
        << "chi2\n";
    myfile.close();

    for (int h = 0; h < h_max; h++)
    {
        myfile.open(fLogPath, std::ios::app);

        std::string fFileString_box = IMG_PATH + "fit_slopeY" + FillNumber + "_" + std::to_string(h) + "_box.png";
        const char *fFile_box = &fFileString_box[0];

        t1 = StartTime + h * step;
        //t2 = t1 + step;
        t2 = t1 + step - 1;
        std::cout << "Processing " << t1 << "-" << t2 << std::endl;

        timesec.setRange("time_range", t1, t2);
        RooAbsData *data_timeReduced = dataRead.reduce(CutRange("time_range"), Name("data_timeReduced"));
        ntracks_time = data_timeReduced->sumEntries();
        std::cout << "Tracks in the selected range: " << ntracks_time << std::endl;

        RooAbsData *data_ResiReduced = data_timeReduced->reduce(*var_Rcut);
        ntracks_resi = data_ResiReduced->sumEntries();
        std::cout << "Tracks after the residual cut: " << ntracks_resi << std::endl;

        if(ntracks_time == 0){
            myfile << FillNumber << "," << h << "," 
        << t1 << "," << t2 << "," 
        << ntracks_time << "," << ntracks_resi << ","
        << "0,0,0,0,0,0,0,0,0,0,0" << std::endl;
        myfile.close();
            continue;
        }

        //Define Gaussian
        RooRealVar m0("m0", "mean 0", 0.026965, 0.02, 0.03);
        RooRealVar m1("m1", "mean 1", 0.02618);
        RooRealVar m2("m2", "mean 2", 0.0295);

        RooRealVar s0("s0", "sigma 0", 0.001275, 0.0005, 0.0017);
        RooRealVar s1("s1", "sigma 1", 0.0036);
        RooRealVar s2("s2", "sigma 2", 0.0151);

        RooGaussian g0("g0", "gaussian PDF 0", SlopeY, m0, s0);
        RooGaussian g1("g1", "gaussian PDF 1", SlopeY, m1, s1);
        RooGaussian g2("g2", "gaussian PDF 2", SlopeY, m2, s2);

        TH1 *histZ_x = data_timeReduced->createHistogram("BeamSpot X", BeamSpotZ_x, Binning(50, -10, 10));
        TH1 *histZ_y = data_timeReduced->createHistogram("BeamSpot Y", BeamSpotZ_y, Binning(50, -10, 10));

        // Define Signal
        RooRealVar frac0("frac0", "fraction 0", 0.804);
        RooRealVar frac1("frac1", "fraction 1", 0.124);
        RooAddPdf sig("sig", "g0+g1+g2", RooArgList(g0, g1, g2), RooArgList(frac0, frac1));

        // Define background
        RooRealVar bkg_m0("bkg_m0", "bkg_m0", 0.026, 0.01, 0.04);
        RooRealVar bkg_s0("bkg_s0", "bkg_s0", 0.018, 0.01, 0.1);
        RooRealVar bkg_frac("bkg_frac", "bkg_frac", 0.011, 0., 0.5);

        RooGaussian bkg("bkg", "bkg", SlopeY, bkg_m0, bkg_s0);

        //Define Model
        RooAddPdf model("model", "model (fggg + g)", RooArgList(bkg, sig), bkg_frac);

        RooPlot *frame1 = SlopeY.frame(Range(-0.08, 0.12), Title(""));

        data_timeReduced->plotOn(frame1, Name("dataSet"));

        // Fit data
        model.fitTo(*data_timeReduced, Verbose(false), PrintLevel(-1), Save());

        model.plotOn(frame1, Components(RooArgSet(sig)), LineColor(kGreen));
        model.plotOn(frame1, Components(RooArgSet(bkg)), LineColor(kRed));

        model.plotOn(frame1, Name("model"));

        // Calculate chi2
        Double_t chi2 = frame1->chiSquare("model", "dataSet", 5);

        RooHist *rh = (RooHist *)frame1->findObject("dataSet");
        int N = rh->GetN();
        Double_t x, y;

        for (int i = 0; i < N; i++)
        {
            rh->GetPoint(i, x, y);
            if (y == 0.0)
            {
                rh->SetPointError(i, 0., 0., 0., 0.);
            }
        }

        // StartTime new canvas (box)
        TCanvas *c_box = new TCanvas("c_box", "c_box", 800, 700);
        c_box->GetPad(0)->SetLogy();
        frame1->SetMaximum(1e6);
        frame1->SetMinimum(0.2);
        frame1->GetYaxis()->SetTitleOffset(1.2);
        frame1->GetYaxis()->SetTitleSize(0.04);

        // ParamBox
        model.paramOn(frame1, Layout(0.7), Format(("NEU"), AutoPrecision(1)));
        frame1->getAttText()->SetTextSize(0.02);
        TPaveText *pt = (TPaveText *)frame1->findObject("model_paramBox");
        pt->AddText(Form("#chi^{2} /ndof =  %f", chi2));

        pt->AddText(Form("Tracks = %i", ntracks_time));
        
        // t1_data = ((RooRealVar *)(data_timeReduced->get(0)->find("timesec")))->getVal();
        // t2_data = ((RooRealVar *)(data_timeReduced->get(ntracks_time - 1)->find("timesec")))->getVal();

/*
#include <iostream>
#include <ctime>

int main() {
    time_t epoch_time = 1610612800; // Example epoch time
    struct tm *time_info;
    time_info = gmtime(&epoch_time);
    std::cout << "Hours: " << time_info->tm_hour << std::endl;
    return 0;
}
*/

        t1_data = t1;
        t2_data = t2;

        string_buffer.str(std::string());
        hr = t1_data / 3600;
        min = (t1_data - (hr * 3600)) / 60;
        sec = t1_data % 60;
        string_buffer << std::setfill('0') << std::setw(2) << hr << ":" << std::setw(2) << min << ":" << std::setw(2) << sec;

        t1_data_s = string_buffer.str();
        string_buffer.str(std::string());

        hr = t2_data / 3600;
        min = (t2_data - (hr * 3600)) / 60;
        sec = t2_data % 60;
        string_buffer << std::setfill('0') << std::setw(2) << hr << ":" << std::setw(2) << min << ":" << std::setw(2) << sec;

        t2_data_s = string_buffer.str();

        pt->AddText(Form("timesec =  %s - %s", &t1_data_s[0], &t2_data_s[0]));

        frame1->Draw();
        c_box->SaveAs(fFile_box);

        myfile << FillNumber << "," << h << "," 
        << t1_data << "," << t2_data << "," 
        << ntracks_time << "," << ntracks_resi << ","
        << bkg_frac.getVal() << "," << bkg_frac.getError() << "," 
        << bkg_m0.getVal() << "," << bkg_m0.getError() << "," 
        << bkg_s0.getVal() << "," << bkg_s0.getError() << "," 
        << histZ_x->GetMean() << "," << histZ_x->GetStdDev() << "," 
        << histZ_y->GetMean() << "," << histZ_y->GetStdDev() << "," 
        << chi2 << std::endl;
        myfile.close();
    }
}
