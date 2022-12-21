// not needed ????

void fix_track_numbers(std::string FileName)
{

    std::string FILE_PATH = "/home/nkarunar/hit_root_files/";

    std::string tNameString = "Hit info for fill " + FileName;
    char *tName = &tNameString[0];

    std::string foldNameString = FILE_PATH + FileName + "_raw.root";
    const char *foldName = &foldNameString[0];

    std::string fnewNameString = FILE_PATH + FileName + ".root";
    const char *fnewName = &fnewNameString[0];

    std::cout << "Opening file : " << foldName << std::endl;

    TFile f_old(foldName);
    TTree *t_old;
    f_old.GetObject("T", t_old);

    // f_old.Close();

    std::cout << t_old->GetEntries() << std::endl;

    uint32_t hits;
    uint32_t event;
    uint32_t event_time;
    // time_t EpochTime;
    uint32_t bx;
    uint32_t channel[KMaxHits];
    uint32_t roc[KMaxHits];
    uint32_t row[KMaxHits];
    uint32_t col[KMaxHits];
    uint32_t pulseHeight[KMaxHits];

    t_old->SetBranchAddress("hits", &hits);
    t_old->SetBranchAddress("event", &event);
    t_old->SetBranchAddress("event_time", &event_time);
    t_old->SetBranchAddress("bx", &bx);

    t_old->SetBranchAddress("channel", channel);
    t_old->SetBranchAddress("roc", roc);
    t_old->SetBranchAddress("roc", row);
    t_old->SetBranchAddress("roc", col);
    t_old->SetBranchAddress("roc", pulseHeight);

    TFile *f_new = new TFile(fnewName, "RECREATE");
    TTree T("T", tName);

    T.Branch("hits", &hits, "hits/I");
    T.Branch("event", &event, "event/I");
    T.Branch("event_time", &event_time, "event_time/I");
    T.Branch("bx", &bx, "bx/I");
    T.Branch("channel", channel, "channel[hits]/I");
    T.Branch("roc", roc, "roc[hits]/I");
    T.Branch("row", row, "row[hits]/I");
    T.Branch("col", col, "col[hits]/I");
    T.Branch("pulseHeight", pulseHeight, "pulseHeight[hits]/I");

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