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

  std::ofstream myfile;
  myfile.open("count.csv");

  int hist[16] = {0};

  // Loop over all events in file
  for (int ientry = 0; Event.GetNextEvent() >= 0; ++ientry)
  {
    if (ientry % 10000 == 0)
    {
      std::cout << "Processing entry: " << ientry << std::endl;
    }

    // Loop over all planes with hits in event
    for (size_t it = 0; it != Event.NTelescopes(); ++it)
    {
      // THIS telescope is
      PLTTelescope *Telescope = Event.Telescope(it);

      myfile << Event.ReadableTime() << "," << Telescope->Channel() << "," << Telescope->NTracks() << "\n";
    }
  }

  myfile.close();
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
