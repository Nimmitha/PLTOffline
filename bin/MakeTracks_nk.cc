////////////////////////////////////////////////////////////////////
//
// Dean Andrew Hidas <Dean.Andrew.Hidas@cern.ch>
//
// Created on: Thu Mar  8 18:26:18 UTC 2012
//
// Modified by Nimmitha : all the time
////////////////////////////////////////////////////////////////////

#include <iostream>
#include <fstream>
#include <string>
#include "PLTEvent.h"
#include "PLTU.h"
#include "TFile.h"
#include "TTree.h"
#include <ctime>

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

  time_t EpochTime;
  u_int32_t msecs;
  char buffer[24];
  bool haveTime;

  // Grab the plt event reader
  PLTEvent Event(DataFileName, GainCalFileName, AlignmentFileName);

  PLTPlane::FiducialRegion FidRegionHits = PLTPlane::kFiducialRegion_All;
  Event.SetPlaneFiducialRegion(FidRegionHits);
  Event.SetPlaneClustering(PLTPlane::kClustering_AllTouching, FidRegionHits);

  PLTAlignment Alignment;
  Alignment.ReadAlignmentFile(AlignmentFileName);

  // Define file name, file path and Title of the TTree
  std::string fName = FillNumber; //+ "_" + std::to_string(StartTime) + "_" + std::to_string(EndTime);
  // std::string fPathString = "/home/nkarunar/root_files/" + fName + ".root";
  std::string fPathString = "/eos/home-n/nkarunar/data/slink_data/slink_tracks/" + fName + ".root";


  std::string tNameString = "Track parameters for fill " + fName;

  uint32_t event;
  uint32_t Channel;
  uint32_t timemsec;
  uint32_t timesec;
  // float_t event_time;
  // std::string event_time; // https://root-forum.cern.ch/t/saving-an-array-of-character-strings-in-a-root-tree/1522/4
  float_t SlopeX, SlopeY;
  float_t ResidualX_ROC0, ResidualX_ROC1, ResidualX_ROC2, ResidualY_ROC0, ResidualY_ROC1, ResidualY_ROC2;
  float_t BeamspotX_y, BeamspotX_z, BeamspotY_x, BeamspotY_z, BeamSpotZ_x, BeamSpotZ_y;

  uint32_t track = 0;

  char *fPath = &fPathString[0];
  char *tName = &tNameString[0];

  // Create new ROOT file, open TTree
  TFile *f = new TFile(fPath, "RECREATE");
  TTree *T = new TTree("T", tName);

  // Define branch variables
  T->Branch("event", &event, "event/I");
  T->Branch("track", &track, "track/I");
  T->Branch("timesec", &timesec, "timesec/I");
  T->Branch("timemsec", &timemsec, "timemsec/I");
  // T->Branch("event_time", &event_time, "event_time/F");
  // T->Branch("event_time", &event_time);
  T->Branch("Channel", &Channel, "Channel/I");
  T->Branch("SlopeX", &SlopeX, "SlopeX/F");
  T->Branch("SlopeY", &SlopeY, "SlopeY/F");

  T->Branch("ResidualX_ROC0", &ResidualX_ROC0, "ResidualX_ROC0/F");
  T->Branch("ResidualX_ROC1", &ResidualX_ROC1, "ResidualX_ROC1/F");
  T->Branch("ResidualX_ROC2", &ResidualX_ROC2, "ResidualX_ROC2/F");
  T->Branch("ResidualY_ROC0", &ResidualY_ROC0, "ResidualY_ROC0/F");
  T->Branch("ResidualY_ROC1", &ResidualY_ROC1, "ResidualY_ROC1/F");
  T->Branch("ResidualY_ROC2", &ResidualY_ROC2, "ResidualY_ROC2/F");

  T->Branch("BeamspotX_y", &BeamspotX_y, "BeamspotX_y/F");
  T->Branch("BeamspotX_z", &BeamspotX_z, "BeamspotX_z/F");

  T->Branch("BeamspotY_x", &BeamspotY_x, "BeamspotY_x/F");
  T->Branch("BeamspotY_z", &BeamspotY_z, "BeamspotY_z/F");

  T->Branch("BeamSpotZ_x", &BeamSpotZ_x, "BeamSpotZ_x/F");
  T->Branch("BeamSpotZ_y", &BeamSpotZ_y, "BeamSpotZ_y/F");

  /*
    float_t GlobalVX, GlobalVY, GlobalVZ;
  float_t LocalVX, LocalVY, LocalVZ;
  T->Branch("GlobalVX", &GlobalVX, "GlobalVX/F");
  T->Branch("GlobalVY", &GlobalVY, "GlobalVY/F");
  T->Branch("GlobalVZ", &GlobalVZ, "GlobalVZ/F");
  T->Branch("LocalVX", &LocalVX, "LocalVX/F");
  T->Branch("LocalVY", &LocalVY, "LocalVY/F");
  T->Branch("LocalVZ", &LocalVZ, "LocalVZ/F");
  GlobalVX = Track->fGVX;
  GlobalVY = Track->fGVY;
  GlobalVZ = Track->fGVZ;
  LocalVX = Track->fTVX;
  LocalVY = Track->fTVY;
  LocalVZ = Track->fTVZ;
*/

  std::string prev_time;

  // Loop over all events in file
  std::cout << "\nLooping through events.\n\n";
  for (int ientry = 0; Event.GetNextEvent() >= 0; ++ientry)
  {
    if (ientry % 5000000 == 0)
    {
      std::cout << "Entry: " << ientry << "\t" << Event.ReadableTime() << std::endl;
      
      // if (ientry > 1) break;
    }

    if (Event.Time() < StartTime * 1000)
      continue;

    if (track >= UINT32_MAX - 1 || Event.Time() >= EndTime * 1000)
    {
      break;
    }

    prev_time = Event.ReadableTime();
    // timemsec = Event.Time() % 1000;
    // timesec = EpochDate + Event.Time() / 1000;

    // msecs = Event.Time()%1000;
    // EpochTime = EpochDate + Event.Time()/1000;
    // tm *ltm = localtime(&EpochTime);

    // strftime(buffer, 24, "%F %T", ltm);
    // event_time = buffer;
    // event_time = event_time + "." + std::to_string(msecs);

    // std::cout<< "THIS IS NEW " << event_time << std::endl;

    haveTime = false;

    // Loop over all planes with hits in event
    for (size_t it = 0; it != Event.NTelescopes(); ++it)
    {
      // THIS telescope is
      PLTTelescope *Telescope = Event.Telescope(it);

      if (Telescope->NClusters() > 3)
        continue;

      Channel = Telescope->Channel();

      for (size_t itrack = 0; itrack != Telescope->NTracks(); ++itrack)
      {
        PLTTrack *Track = Telescope->Track(itrack);

        if (track % 1000000 == 0)
        {
          std::cout << "Processing entry: " << ientry << " - ";
          std::cout << Event.ReadableTime() << " - Track Index :" << track << std::endl;
        }

        if (haveTime == false)
        {
          // https://www.tutorialspoint.com/cplusplus/cpp_date_time.htm
          // msecs = Event.Time() % 1000;
          // EpochTime = EpochDate + Event.Time() / 1000;
          // tm *ltm = localtime(&EpochTime);

          // https://cplusplus.com/reference/ctime/strftime/
          // strftime(buffer, 24, "%F %T", ltm);
          // event_time = buffer;
          // event_time = event_time + "." + std::to_string(msecs);

          // prev_time = Event.ReadableTime();
          timemsec = Event.Time() % 1000;
          timesec = EpochDate + Event.Time() / 1000;
          // std::cout << "Processing entry: " << event_time << std::endl;
          haveTime = true;
        }

        event = ientry;
        // track = itrack;
        SlopeX = Track->fTVX / Track->fTVZ;
        SlopeY = Track->fTVY / Track->fTVZ;
        ResidualX_ROC0 = Track->LResidualX(0);
        ResidualX_ROC1 = Track->LResidualX(1);
        ResidualX_ROC2 = Track->LResidualX(2);
        ResidualY_ROC0 = Track->LResidualY(0);
        ResidualY_ROC1 = Track->LResidualY(1);
        ResidualY_ROC2 = Track->LResidualY(2);
        BeamspotX_y = Track->fPlaner[0][1];
        BeamspotX_z = Track->fPlaner[0][2];
        BeamspotY_x = Track->fPlaner[1][0];
        BeamspotY_z = Track->fPlaner[1][2];
        BeamSpotZ_x = Track->fPlaner[2][0];
        BeamSpotZ_y = Track->fPlaner[2][1];
        T->Fill();

        track++;
      }
    }
  }

  // Writing Log file
  std::ofstream myfile;
  myfile.open("logs/MakeTracksLog.txt", std::ios::app);
  myfile << FillNumber << " " << track << " " << getTime(StartTime * 1000) << " " << prev_time << "\n";

  myfile.close();

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
  // std::string const EpochDate = argv[7];

  MakeTracks(DataFileName, GainCalFileName, AlignmentFileName, FillNumber, StartTime, EndTime, EpochDate);

  return 0;
}
