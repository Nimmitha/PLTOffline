void fix_track_numbers(std::string FileName){

    // std::string FILE_PATH = "/home/nkarunar/root_files/";
    std::string FILE_PATH = "/eos/home-n/nkarunar/data/slink_data/slink_tracks/";

    std::string tNameString = "Track parameters for fill " + FileName;
    char *tName = &tNameString[0];
    
    std::string foldNameString = FILE_PATH + FileName + "_raw.root";
    const char *foldName = &foldNameString[0];

    std::string fnewNameString = FILE_PATH + FileName + ".root";
    const char *fnewName = &fnewNameString[0];

    std::cout << "Opening file : " << foldName << std::endl;

    TFile f_old(foldName);
    TTree *t_old;
    f_old.GetObject("T", t_old);

    //f_old.Close();

    std::cout << t_old->GetEntries() << std::endl;

    Int_t track;
    Int_t event;
    Int_t Channel;
    // std::string event_time;
    Int_t timesec;
    Int_t timemsec;
    float_t SlopeX, SlopeY;
    float_t ResidualX_ROC0, ResidualX_ROC1, ResidualX_ROC2, ResidualY_ROC0, ResidualY_ROC1, ResidualY_ROC2;
    float_t BeamspotX_y, BeamspotX_z, BeamspotY_x, BeamspotY_z,BeamSpotZ_x, BeamSpotZ_y;

    t_old->SetBranchAddress("event", &event);
    t_old->SetBranchAddress("track", &track);
    // t_old->SetBranchAddress("event_time", &event_time);
    t_old->SetBranchAddress("timesec", &timesec);
    t_old->SetBranchAddress("timemsec", &timemsec);
    t_old->SetBranchAddress("Channel", &Channel);
    t_old->SetBranchAddress("SlopeX", &SlopeX);
    t_old->SetBranchAddress("SlopeY", &SlopeY);

    t_old->SetBranchAddress("ResidualX_ROC0", &ResidualX_ROC0);
    t_old->SetBranchAddress("ResidualX_ROC1", &ResidualX_ROC1);
    t_old->SetBranchAddress("ResidualX_ROC2", &ResidualX_ROC2);
    t_old->SetBranchAddress("ResidualY_ROC0", &ResidualY_ROC0);
    t_old->SetBranchAddress("ResidualY_ROC1", &ResidualY_ROC1);
    t_old->SetBranchAddress("ResidualY_ROC2", &ResidualY_ROC2);

    t_old->SetBranchAddress("BeamspotX_y", &BeamspotX_y);
    t_old->SetBranchAddress("BeamspotX_z", &BeamspotX_z);

    t_old->SetBranchAddress("BeamspotY_x", &BeamspotY_x);
    t_old->SetBranchAddress("BeamspotY_z", &BeamspotY_z);

    t_old->SetBranchAddress("BeamSpotZ_x", &BeamSpotZ_x);
    t_old->SetBranchAddress("BeamSpotZ_y", &BeamSpotZ_y);

    TFile *f_new = new TFile(fnewName, "RECREATE");
    TTree T("T", tName);

    T.Branch("event", &event, "event/I");
    T.Branch("track", &track, "track/I");
    // T.Branch("event_time", &event_time);
    T.Branch("timesec", &timesec, "timesec/I");
    T.Branch("timemsec", &timemsec, "timemsec/I");
    T.Branch("Channel", &Channel, "Channel/I");
    T.Branch("SlopeX", &SlopeX, "SlopeX/F");
    T.Branch("SlopeY", &SlopeY, "SlopeY/F");

    T.Branch("ResidualX_ROC0", &ResidualX_ROC0, "ResidualX_ROC0/F");
    T.Branch("ResidualX_ROC1", &ResidualX_ROC1, "ResidualX_ROC1/F");
    T.Branch("ResidualX_ROC2", &ResidualX_ROC2, "ResidualX_ROC2/F");
    T.Branch("ResidualY_ROC0", &ResidualY_ROC0, "ResidualY_ROC0/F");
    T.Branch("ResidualY_ROC1", &ResidualY_ROC1, "ResidualY_ROC1/F");
    T.Branch("ResidualY_ROC2", &ResidualY_ROC2, "ResidualY_ROC2/F");

    T.Branch("BeamspotX_y", &BeamspotX_y, "BeamspotX_y/F");
    T.Branch("BeamspotX_z", &BeamspotX_z, "BeamspotX_z/F");

    T.Branch("BeamspotY_x", &BeamspotY_x, "BeamspotY_x/F");
    T.Branch("BeamspotY_z", &BeamspotY_z, "BeamspotY_z/F");

    T.Branch("BeamSpotZ_x", &BeamSpotZ_x, "BeamSpotZ_x/F");
    T.Branch("BeamSpotZ_y", &BeamSpotZ_y, "BeamSpotZ_y/F");

    Int_t nn = t_old->GetEntries();

    for (Int_t i = 0; i < nn; i++)
    {
        t_old->GetEntry(i);
        track = i;
        T.Fill();
    }

    f_new->Write();
    f_new->Close();
}