////////////////////////////////////////////////////////////////////
//
// Nimmitha Karunarathna
//
// Created on: Fri May  8 18:26:18 UTC 2015
//
////////////////////////////////////////////////////////////////////

#include <iostream>
#include <string>

#include "PLTEvent.h"
#include "PLTU.h"
#include "TFile.h"

// FUNCTION DEFINITIONS HERE
int TrackCount(std::string const, std::string const, std::string const);

int TrackCount(std::string const DataFileName, std::string const GainCalFileName, std::string const AlignmentFileName)
{
  std::cout << "DataFileName:      " << DataFileName << std::endl;
  std::cout << "GainCalFileName:   " << GainCalFileName << std::endl;
  std::cout << "AlignmentFileName: " << AlignmentFileName << std::endl;

  // Set some basic style for plots
  PLTU::SetStyle();
  gStyle->SetOptStat(1111);

  // Grab the plt event reader
  PLTEvent Event(DataFileName, GainCalFileName, AlignmentFileName);

  PLTPlane::FiducialRegion FidRegionHits = PLTPlane::kFiducialRegion_All;
  Event.SetPlaneFiducialRegion(FidRegionHits);
  Event.SetPlaneClustering(PLTPlane::kClustering_AllTouching, FidRegionHits);

  PLTAlignment Alignment;
  Alignment.ReadAlignmentFile(AlignmentFileName);

  std::string dateToken = DataFileName.substr(28, 8);
  std::string fileName = "/eos/home-n/nkarunar/data/slink_data/outputs/" + dateToken + "_TrackCount.csv"; 

  std::cout << "\n Output file: " << fileName << std::endl;

  std::ofstream myfile;
  myfile.open(fileName);

  std::map<int, int> TrkCount;
  bool TFlag;
  const Int_t nValid = 16;
  const Int_t validChannels[nValid] = {1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17, 19, 20, 22, 23};

  myfile << "EvenTime";

  for (int ch = 0; ch < nValid; ch++)
  {
    myfile << "," << validChannels[ch];
    TrkCount[validChannels[ch]] = 0;
  }
  myfile << "\n";

  // Loop over all events in file
  for (int ientry = 0; Event.GetNextEvent() >= 0; ++ientry)
  {
    //if (ientry >= 10)
      //break;

    if (ientry % 10000 == 0)
    {
      std::cout << "Processing entry: " << ientry << std::endl;
    }
    TFlag = false;

    // Loop over all planes with hits in event
    for (size_t it = 0; it != Event.NTelescopes(); ++it)
    {
      TFlag = true;
      // THIS telescope is
      PLTTelescope *Telescope = Event.Telescope(it);

      TrkCount[Telescope->Channel()] = Telescope->NTracks();
    }

    if (TFlag)
    {
      myfile << Event.ReadableTime();

      for (int ch = 0; ch < nValid; ch++)
      {
        myfile << "," << TrkCount[validChannels[ch]];
      }
      myfile << "\n";

      TrkCount.clear();
    }
  }

  myfile.close();
  std::cout << "\n Output saved to: " << fileName << std::endl;
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

  TrackCount(DataFileName, GainCalFileName, AlignmentFileName);

  return 0;
}
