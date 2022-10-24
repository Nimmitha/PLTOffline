////////////////////////////////////////////////////////////////////
//
// Dean Andrew Hidas <Dean.Andrew.Hidas@cern.ch>
//
// Created on: Thu Mar  8 18:26:18 UTC 2012
//
////////////////////////////////////////////////////////////////////

#include <iostream>
#include <string>

#include "PLTEvent.h"
#include "PLTU.h"
#include "TFile.h"
#include "TTree.h"

// FUNCTION DEFINITIONS HERE
int MakeTracks(std::string const, std::string const, std::string const);

int MakeTracks(std::string const DataFileName, std::string const GainCalFileName, std::string const AlignmentFileName)
{
  std::cout << "DataFileName:      " << DataFileName << std::endl;
  std::cout << "GainCalFileName:   " << GainCalFileName << std::endl;
  std::cout << "AlignmentFileName: " << AlignmentFileName << std::endl;

  // Grab the plt event reader
  PLTEvent Event(DataFileName, GainCalFileName, AlignmentFileName);

  PLTPlane::FiducialRegion FidRegionHits = PLTPlane::kFiducialRegion_All;
  Event.SetPlaneFiducialRegion(FidRegionHits);
  Event.SetPlaneClustering(PLTPlane::kClustering_AllTouching, FidRegionHits);

  PLTAlignment Alignment;
  Alignment.ReadAlignmentFile(AlignmentFileName);

  const Int_t KMaxHits = 100;

  uint32_t hits;
  uint32_t event;
  uint32_t event_time;
  uint32_t bx;
  uint32_t channel[KMaxHits];
  uint32_t roc[KMaxHits];
  uint32_t row[KMaxHits];
  uint32_t col[KMaxHits];
  uint32_t pulseHeight[KMaxHits];

  std::string fName = "TEST";
  // std::string fPathString = "/home/nkarunar/root_files/" + fName + ".root";
  std::string fPathString = fName + ".root";
  std::string tNameString = "Track parameters for fill " + fName;

  char *fPath = &fPathString[0];
  char *tName = &tNameString[0];

  // Create new ROOT file, open TTree
  TFile *f = new TFile(fPath, "RECREATE");
  TTree *T = new TTree("T", tName);

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
    hits = Event.NHits();
    event = Event.EventNumber();
    event_time = Event.Time();
    bx = Event.BX();

    if (Event.fHits.size() != hits)
    {
      std::cout << "Size does not matche!!!" << std::endl;
      exit(1);
    }

    // for (std::vector<PLTHit *>::iterator it = Event.fHits.begin(); it != Event.fHits.end(); ++it)
    for (unsigned int i = 0; i < hits; i++)
    {
      channel[i] = Event.fHits.at(i)->Channel();
      roc[i] = Event.fHits.at(i)->ROC();
      row[i] = Event.fHits.at(i)->Row();
      col[i] = Event.fHits.at(i)->Column();
      pulseHeight[i] = Event.fHits.at(i)->ADC();

      // std::cout
      //     << Event.EventNumber() << "\n"
      //     << Event.Time() << "\n"
      //     << Event.BX() << "\n"
      //     << Event.NHits() << "\n"
      //     << (*it)->Channel() << "\n"
      //     << (*it)->ROC() << "\n"
      //     << (*it)->Row() << "\n"
      //     << (*it)->Column() << "\n"
      //     << (*it)->ADC() << "\n"
      //     << std::endl;
    }
    T->Fill();

    if (ientry % 10000 == 0)
    {
      std::cout << "Processing entry: " << ientry << std::endl;
    }
    if (ientry >= 20000)
    {
      break;
    }
  }
  f->Write();
  f->Close();
  return 0;
}

int main(int argc, char *argv[])
{
  if (argc != 4)
  {
    std::cerr << "Usage: " << argv[0] << " [DataFile.dat] [GainCal.dat] [AlignmentFile.dat]" << std::endl;
    return 1;
  }

  std::string const DataFileName = argv[1];
  std::string const GainCalFileName = argv[2];
  std::string const AlignmentFileName = argv[3];

  MakeTracks(DataFileName, GainCalFileName, AlignmentFileName);

  return 0;
}
