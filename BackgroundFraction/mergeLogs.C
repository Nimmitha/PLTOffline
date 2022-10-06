{
    TTree* TLumi = new TTree("TreeLumi", "Lumi data");
    TTree* TF = new TTree("TreeF", "F data");

    TLumi->ReadFile("logs/4979_77400_86340Lumi.csv");
    TF->ReadFile("logs/4979_77400_86340F.csv");

    TLumi->AddFriend(TF, "TF");
}