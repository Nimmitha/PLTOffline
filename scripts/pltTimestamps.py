#!/usr/bin/env python3

# This script will create a csv file containing stable beam fill numbers with their corresponding start and end timestamps.
# It fetches LHC fill info from CMSOMS and requires the CMSOMS Aggregation API python client [https://gitlab.cern.ch/cmsoms/oms-api-client]
# It will find any workloop and slink files with filename timestamps corresponding to each fill (within fill-start and fill-end timestamps)

import os, sys, pandas
import typing as t # [https://docs.python.org/3/library/typing.html]

venvDir      = f'{os.path.expanduser("~")}/.local/venv/plt'
certFilePath = f'{os.path.expanduser("~")}/private/myCertificate'

def printColor( color:str, message:str ):
    # print 'message' in foreground 'color' [http://ascii-table.com/ansi-escape-sequences.php]
    colors = { 'reset':'0', 'bold':'1', 'uline':'4', 'black':'30', 'red':'31', 'green':'32', 'yellow':'33', 'blue':'34', 'magenta':'35', 'cyan':'36', 'white':'37' }
    colors = { key: f'\033[{val}m' for key, val in colors.items() }
    print( f'{colors[color]}{message}{colors["reset"]}' )

def fileTimestamps( year:int, fileType:str ) -> pandas.Series:
    # return all file timestamps a pandas series of sorted timestamps, given a year as an argument
    import re, glob
    if fileType == 'wloop':
        globString = f'/localdata/{year}/WORKLOOP/Data_Scaler*'
        sliceFrom = 2
    elif fileType == 'slink':
        globString = f'/localdata/{year}/SLINK/Slink*'
        sliceFrom = 1
    tsList = list( set( [ str.join( '.', re.split( '_|\.', filename )[sliceFrom:sliceFrom+2] ) for filename in glob.glob( globString ) ] ) )
        # list(set()) will remove duplicate entries, usually from both .gz and uncompressed versions of files
    if not tsList:
        sys.exit( printColor( 'red', f'No {fileType} files found for {year}. Please make sure to run script from pltoffline machine' ) )
    return pandas.to_datetime( pandas.Series( tsList ), format = '%Y%m%d.%H%M%S' ).sort_values()

def lhcTimestamps( year:str ) -> pandas.DataFrame:
    df = pandas.read_csv('https://delannoy.web.cern.ch/fills.csv')
    # df = pandas.read_csv('fills_new.csv')
    lhcTS = df[df.oms_stable_beams & (df.oms_start_time>=f'{year}-01-01') & (df.oms_end_time<=f'{year+1}-01-01')][['oms_fill_number','oms_start_time', 'oms_start_stable_beam', 'oms_end_stable_beam', 'oms_end_time']]
    rename_dict = {'oms_fill_number':'fill', 'oms_start_time':'start_time', 'oms_start_stable_beam':'start_stable_beam', 'oms_end_stable_beam':'end_stable_beam', 'oms_end_time':'end_time'}
    lhcTS.rename(columns=rename_dict, inplace=True)
    lhcTS.set_index('fill', inplace=True)
    return lhcTS.apply( pandas.to_datetime, format = '%Y-%m-%dT%H:%M:%SZ' )


def sortTS( seriesTS:pandas.Series, startTS:pandas.Timestamp, endTS:pandas.Timestamp ) -> str:
    # find all timestamps within fill-start (with 10-second tolerance) and fill-end timestamps and return as a string
    #tsList = seriesTS[ ( seriesTS >= startTS-pandas.Timedelta(seconds=10) ) & ( seriesTS <= endTS ) ].to_list()
    
    # Tried this to fix the issue of having a SLINK file running for several days without restarting
    # Cases where it included previous file: 3819,3833,3850,3851,3855,3962,3971,3974,4851,4961,5659,7652
    # Select the amount of time we neglect from the start of the file
    # This also includes the previous file if x seconds of data is missing in the current file
    tolerance = pandas.Timedelta(seconds=600) 
    
    tsList = seriesTS[ seriesTS.ge(startTS-pandas.Timedelta(seconds=10)) & seriesTS.le(endTS-pandas.Timedelta(seconds=10)) ].to_list()
    
    # pick the previous file that may have data for the current fill
    prevFile = seriesTS[seriesTS.lt(startTS+tolerance)].to_list()
    if len(prevFile) != 0:
        prevFile = prevFile[-1]
        if prevFile not in tsList:
            if len(tsList) == 0:
                tsList.append(prevFile)
            elif prevFile < tsList[0]:
                tsList.insert(0, prevFile)
    
    return str.join( ' ', [ ts.strftime("%Y%m%d.%H%M%S") for ts in tsList ] ) # return a string with timestamps in the list separated by spaces

def gainCal( pltTS:pandas.DataFrame ) -> pandas.DataFrame:
    # insert selected gain calibration file timestamps with "usable" results [https://github.com/cmsplt/PLTOffline/tree/master/GainCal/2020]
        # start with most recent gainCal timestamp and assign to all fills until fill start_stable_beam timestamp < gainCal timestamp. and also constrain to be in the same year
    def gainCalNextFill( gainCalTS:str ):
        return pltTS.iloc[ pandas.Index(pltTS['start_stable_beam']).get_loc( gainCalTS.replace('.', ' '), method='backfill' ) ].name
        # find index (fill number) of the most proximate (but still larger) start_stable_beam timestamp to the input gainCalTS

    gainCalTS = [ '20150811.120552', '20150923.225334', '20151029.220336', \
                '20160819.113115', \
                '20170518.143905', '20170717.224815', '20170731.122306', '20170921.104620', '20171026.164159', \
                '20180419.131317', '20180430.123258', '20180605.124858', '20180621.160623', '20220803.143004']
    for ts in sorted( gainCalTS, reverse=True):
        # print(pltTS)
        pltTS.loc[ ( pltTS.start_time.dt.year == int(ts[0:4]) ) & ( pltTS.index >= gainCalNextFill(ts) ), 'gainCal' ] = ts

    pltTS.gainCal.fillna( method='backfill', inplace=True ) # propagate empty gainCal entries backwards from last valid entry
    return pltTS

def alignment( pltTS:pandas.DataFrame ) -> pandas.DataFrame:
    # populate "standard" alignment files for each year in 'pltTS' [https://github.com/cmsplt/PLTOffline/blob/master/ALIGNMENT/README]
    # def filtYear(year:int): return (f'{year}-01-01'<pltTS.start_time) & (pltTS.end_time<f'{year}-12-31')
    pltTS.loc[ pltTS.start_time.dt.year == 2015, 'alignment' ] = 'Trans_Alignment_4449.dat'
    pltTS.loc[ pltTS.start_time.dt.year == 2016, 'alignment' ] = 'Trans_Alignment_4892.dat'
    pltTS.loc[ pltTS.start_time.dt.year == 2017, 'alignment' ] = 'Trans_Alignment_2017MagnetOn_Prelim.dat'
    pltTS.loc[ pltTS.start_time.dt.year == 2022, 'alignment' ] = 'Trans_Alignment_8033.dat'
    # pltTS.loc[ 6570:6579, 'alignment' ] = 'Trans_Alignment_6666.dat' # (example)
    return pltTS

def trackDist( pltTS:pandas.DataFrame ) -> pandas.DataFrame:
    # populate "standard" track distribution files for each year in 'pltTS' [https://github.com/cmsplt/PLTOffline/blob/master/TrackDistributions/README]
    pltTS.loc[ pltTS.start_time.dt.year == 2015, 'trackDist' ] = 'TrackDistributions_MagnetOn.txt'
    pltTS.loc[ pltTS.start_time.dt.year == 2016, 'trackDist' ] = 'TrackDistributions_MagnetOn2016_4892.txt'
    pltTS.loc[ pltTS.start_time.dt.year == 2017, 'trackDist' ] = 'TrackDistributions_MagnetOn2017_5718.txt'
    return pltTS

def pltTimestamps( year:int ) -> pandas.DataFrame:
    wloopTS = fileTimestamps( year, 'wloop' )
    slinkTS = fileTimestamps( year, 'slink' )
    yearTS  = lhcTimestamps( year )
    printColor( 'green', f'processing timestamps. beep boop...' )
    yearTS['wloopTS'] = [ sortTS( wloopTS, startTS, endTS ) for startTS,endTS in zip(yearTS['start_time'], yearTS['end_time']) ]
        # note that workloop timestamps are included from fill-declared to fill-end
    yearTS['slinkTS'] = [ sortTS( slinkTS, startTS, endTS ) for startTS,endTS in zip(yearTS['start_stable_beam'], yearTS['end_stable_beam']) ]
        # whereas, slink timestamps are included from stableBeam-declared to stableBeam-end
    return yearTS

def main():
    #omsapi = cmsomsAuth()
    pltTS = pandas.DataFrame()
    for year in 2015, 2016, 2017, 2018, 2022:
        yearTS = pltTimestamps( year )
        pltTS = pltTS.append( yearTS )

    pltTS = pltTS[~pltTS.index.duplicated(keep='first')]
    pltTS = gainCal( pltTS )
    pltTS = alignment( pltTS )
    pltTS = trackDist( pltTS )
    pltTS[ pltTS.columns[0:4] ] = pltTS[ pltTS.columns[0:4] ].apply( lambda col: col.dt.strftime("%Y%m%d.%H%M%S") )
    with open( f'pltTimestamps.csv', 'w' ) as outFile:
        pltTS.to_csv( outFile, sep = '|' )

if __name__ == "__main__":
    main()

# #import datetime
# import numpy as np
# import os, sys
#
# file = open('PLT-timestamps.txt','w')
# fills, declaredTS, beginTS, endTS = np.loadtxt('TimeStamps.StableBeams', unpack = True, delimiter = ' ') # https://docs.scipy.org/doc/numpy/reference/generated/numpy.loadtxt.html
# # list( *map(int, fills) )                                                                               # https://stackoverflow.com/a/7368801
# slinkTS                           = np.loadtxt('TimeStamps.Slink',       unpack = True, delimiter = ' ')
# workloopTS                        = np.loadtxt('TimeStamps.Workloop',    unpack = True, delimiter = ' ')
#
# file.write( 'fill|fillDeclared|fillEnd|slinkTS|workloopTS\n' )
# #for i in range(len(fills)):
# for i,fill in enumerate(fills, start=0):                                                                 # http://treyhunner.com/2016/04/how-to-loop-with-indexes-in-python/
#     # https://stackoverflow.com/a/13871987
#     # https://stackoverflow.com/a/43141552
#     slinkIndex    = np.where( (slinkTS    >= beginTS[i])    & (slinkTS    <= endTS[i]) )
#     workloopIndex = np.where( (workloopTS >= declaredTS[i]) & (workloopTS <= endTS[i]) )
#     print(str.format(  "Fill {:.0f} ( fillDeclared={:.6f} | fillEnd={:.6f} )", fill, declaredTS[i], endTS[i] ) )
#     fill = str.format( "{:.0f}|{:.6f}|{:.6f}",                                 fill, declaredTS[i], endTS[i] )
#     file.write( fill + '|')
#     # https://stackoverflow.com/questions/25315816/numpy-number-array-to-strings-with-trailing-zeros-removed#comment39461514_25315816
#     # https://stackoverflow.com/a/35119046
#     # https://stackoverflow.com/a/255172
#     print( "\tslink timestamps: ",    *np.char.mod('%0.6f', slinkTS[slinkIndex]),       sep='\n\t\t' )
#     print( "\tworkloop timestamps: ", *np.char.mod('%0.6f', workloopTS[workloopIndex]), sep='\n\t\t' )
#     # https://stackoverflow.com/a/9360197
#     slink    = ' '.join( map( str, np.char.mod( '%0.6f', slinkTS[slinkIndex]       ) ) )
#     workloop = ' '.join( map( str, np.char.mod( '%0.6f', workloopTS[workloopIndex] ) ) )
#     file.write( str( slink    ) + '|' )
#     file.write( str( workloop ) + '\n' )
#
# file.close()
