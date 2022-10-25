#include <iostream>
#include <string>
#include "PLTEvent.h"
#include "PLTU.h"
#include "TFile.h"
#include "TTree.h"

// FUNCTION DEFINITIONS HERE
int MakeTracks(std::string const, std::string const, std::string const, std::string const FillNumber, const uint32_t StartTime, const uint32_t EndTime, const time_t EpochDate);

// Retruns time as PLT time
uint32_t tofTime(uint32_t hh, uint32_t mm, uint32_t ss)
{
  return (hh * 3600 + mm * 60 + ss) * 1000;
}

std::string getTime(uint32_t milisec)
{
  // A utility function which returns the time in readable format.
  std::stringstream buf;

  int seconds = milisec / 1000;
  int hr = seconds / 3600;
  int min = (seconds - (hr * 3600)) / 60;
  int sec = seconds % 60;
  buf << std::setfill('0') << std::setw(2)
      << hr << ":" << std::setw(2) << min << ":" << std::setw(2) << sec << "."
      << std::setw(3) << milisec % 1000;
  return buf.str();
}

int MakeTracks(std::string const DataFileName, std::string const GainCalFileName, std::string const AlignmentFileName, std::string const FillNumber, uint32_t StartTime, uint32_t EndTime, const time_t EpochDate)
{
  std::cout << "DataFileName:      " << DataFileName << std::endl;
  std::cout << "GainCalFileName:   " << GainCalFileName << std::endl;
  std::cout << "AlignmentFileName: " << AlignmentFileName << std::endl;
  std::cout << "FillNumber: " << FillNumber << std::endl;
  std::cout << "StartTime: " << getTime(StartTime * 1000) << std::endl;
  std::cout << "EndTime: " << getTime(EndTime * 1000) << std::endl;
  std::cout << "EpochDate: " << EpochDate << std::endl;

  // Grab the plt event reader
  PLTEvent Event(DataFileName, GainCalFileName, AlignmentFileName);

  PLTPlane::FiducialRegion FidRegionHits = PLTPlane::kFiducialRegion_All;
  Event.SetPlaneFiducialRegion(FidRegionHits);
  Event.SetPlaneClustering(PLTPlane::kClustering_AllTouching, FidRegionHits);

  PLTAlignment Alignment;
  Alignment.ReadAlignmentFile(AlignmentFileName);

  // Define file name, file path and Title of the TTree
  std::string fName = FillNumber; //+ "_" + std::to_string(StartTime) + "_" + std::to_string(EndTime);
  std::string fPathString = "/home/nkarunar/hit_root_files/" + fName + ".root";
  std::string tNameString = "Hit info for fill " + fName;

  const Int_t KMaxHits = 1000;

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

  char *fPath = &fPathString[0];
  char *tName = &tNameString[0];

  // Create new ROOT file, open TTree
  TFile *f = new TFile(fPath, "RECREATE");
  TTree *T = new TTree("T", tName);

  // Define branch variables
  T->Branch("hits", &hits, "hits/I");
  T->Branch("event", &event, "event/I");
  T->Branch("event_time", &event_time, "event_time/I");
  T->Branch("bx", &bx, "bx/I");
  T->Branch("channel", channel, "channel[hits]/I");
  T->Branch("roc", roc, "roc[hits]/I");
  T->Branch("row", row, "row[hits]/I");
  T->Branch("col", col, "col[hits]/I");
  T->Branch("pulseHeight", pulseHeight, "pulseHeight[hits]/I");

  // Loop over all events in file
  for (int ientry = 0; Event.GetNextRawEvent(nullptr, 0) >= 0; ++ientry)
  {
    if (ientry % 1000000 == 0)
    {
      std::cout << "Entry: " << ientry << "\t" << Event.ReadableTime() << std::endl;
    }

    if (Event.Time() < StartTime * 1000)
      continue;

    if (Event.Time() >= EndTime * 1000)
      break;

    hits = Event.NHits();
    event = Event.EventNumber();
    event_time = EpochDate + Event.Time();
    bx = Event.BX();

    if (hits > KMaxHits)
    {
      std::cout << "Array size not enough. Increase KMaxHits to: " << hits << std::endl;
      exit(1);
    }

    if (hits == 0)
      continue;

    // for (std::vector<PLTHit *>::iterator it = Event.fHits.begin(); it != Event.fHits.end(); ++it)
    for (unsigned int i = 0; i < hits; i++)
    {
      channel[i] = Event.fHits.at(i)->Channel();
      roc[i] = Event.fHits.at(i)->ROC();
      row[i] = Event.fHits.at(i)->Row();
      col[i] = Event.fHits.at(i)->Column();
      pulseHeight[i] = Event.fHits.at(i)->ADC();
    }
    T->Fill();
  }

  f->Write();
  f->Close();
  return 0;
}

int main(int argc, char *argv[])
{
  if (argc != 8)
  {
    std::cerr << "Usage: " << argv[0] << " [DataFile.dat] [GainCal.dat] [AlignmentFile.dat] [FillNumber] [StartTime] [EndTime] [EpochDate]" << std::endl;
    return 1;
  }

  std::string const DataFileName = argv[1];
  std::string const GainCalFileName = argv[2];
  std::string const AlignmentFileName = argv[3];
  std::string const FillNumber = argv[4];
  uint32_t StartTime = std::stoi(argv[5]);
  uint32_t EndTime = std::stoi(argv[6]);
  time_t EpochDate = std::stoi(argv[7]);

  MakeTracks(DataFileName, GainCalFileName, AlignmentFileName, FillNumber, StartTime, EndTime, EpochDate);

  return 0;
}
