import csv
import subprocess
import pandas

path = "/afs/cern.ch/user/n/nkarunar/old_plt/PLTOffline/"
command = [path + 'MakeTracks']


def runMakeTrack(row):
    print("\n"+"*"*150)
    print("Running : ", command+row)
    print("*"*150)
    
    x = subprocess.run(command+row)
    print(x)


def pltTimestamps():
    # import pltTimestamps.csv file as dataframe (contains slink and workloop timestamps corresponding to all stable beam fills)

    def parseDate(x): return pandas.to_datetime(x, format='%Y%m%d.%H%M%S')
    with open('/localdata/pltTimestamps.csv', 'r') as tsFile:
        cols = tsFile.readline().strip().split('|')
        tsFile.seek(0)
        dtypes = dict(zip(cols, ['int']+9*['str']))
        # [https://stackoverflow.com/a/37453925/13019084]
        pltTS = pandas.read_csv(
            tsFile, sep='|', dtype=dtypes, parse_dates=cols[1:5], date_parser=parseDate)
    pltTS = pltTS.set_index('fill').fillna('')
    return pltTS


def unzipFiles(Slink):
    for file in Slink:
        cmd_exist = ["ls", "/home/nkarunar/dat_files/Slink_" + file + ".dat"]
        v = subprocess.run(cmd_exist, capture_output = True)

        if v.returncode != 0:
            cmd_copy = ["cp", "-i", "", "/home/nkarunar/dat_files/"]
            cmd_copy[2] = "/localdata/2015/SLINK/Slink_" + file + ".dat.gz"

            print(cmd_copy)
            x = subprocess.run(cmd_copy)
            print(x)

            cmd_unzip = ["gzip", "-d", "Slink_" + file + ".dat.gz"]
            print(cmd_unzip)
            y = subprocess.run(cmd_unzip, cwd="/home/nkarunar/dat_files")
            print(y)
        else:
            print("File already exists..")
        


def getTracks():
    with open("run_info.csv", newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",")

        pltTS = pltTimestamps()

        for row in csvreader:
            fill = int(row[3])

            Slink = pltTS.loc[fill, 'slinkTS'].split()
            year = Slink[0][:4]

            if year == "2015":
                unzipFiles(Slink)

            gainCal = path + "GainCal/2020/GainCalFits_" + pltTS.loc[fill, 'gainCal'] + ".dat"
            alignment = path + "ALIGNMENT/" + pltTS.loc[fill, 'alignment']

            row[1] = gainCal
            row[2] = alignment

            hh, mm = [int(x) for x in row[4].split(":")]
            row[4] = str((hh*3600 + mm*60) * 1000)

            hh, mm = [int(x) for x in row[5].split(":")]
            row[5] = str((hh*3600 + mm*60) * 1000)

            if row[0] != "":
                Slink = [row[0]]
                #row[0] = "/localdata/2016/SLINK/Slink_" + row[0] + ".dat"
                row[0] = "/home/nkarunar/dat_files/Slink_" + row[0] + ".dat"

            print(Slink)
            
            if len(Slink) >= 2:
                print("Slink is split into", len(Slink), "files")
                # run for each file
                for i, file_name in enumerate(Slink):
                    row[3] = str(fill) + "_" + str(i)
                    row[0] = "/localdata/2016/SLINK/Slink_" + file_name + ".dat"
                    #row[0] = "/home/nkarunar/dat_files/Slink_" + file_name + ".dat"
                    runMakeTrack(row)
            else:
                # run once
                #row[0] = "/localdata/2016/SLINK/Slink_" + Slink[0] + ".dat"
                row[0] = "/home/nkarunar/dat_files/Slink_" + Slink[0] + ".dat"
                runMakeTrack(row)


getTracks()

