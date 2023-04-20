import pandas as pd


def pltTimestamps(PLT_PATH):
    # import pltTimestamps.csv file as dataframe (contains slink and workloop timestamps corresponding to all stable beam fills)
    def parseDate(x): return pd.to_datetime(x, format='%Y%m%d.%H%M%S')
    with open(PLT_PATH + 'pltTimestamps.csv', 'r') as tsFile:
        cols = tsFile.readline().strip().split('|')
        tsFile.seek(0)
        dtypes = dict(zip(cols, ['int'] + 9 * ['str']))
        # [https://stackoverflow.com/a/37453925/13019084]
        pltTS = pd.read_csv(
            tsFile, sep='|', dtype=dtypes, parse_dates=cols[1:5], date_parser=parseDate)
    pltTS = pltTS.set_index('fill').fillna('')
    return pltTS