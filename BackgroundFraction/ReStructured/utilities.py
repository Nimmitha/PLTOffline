import pandas as pd

def pltChannelMap() -> pd.DataFrame:
    quadrants = pd.Series(['-zNear','-zFar','+zNear','+zFar']).repeat(12)
    flavor = pd.Series(['Calabrese','Diavola','Capricciosa','Margherita']).repeat(12)
    mFec = pd.Series(['8-1','8-2','7-1','7-2']).repeat(12)
    anaLV = pd.Series(f'PLT_1.8_H{q}' for q in ['mN','mF','pN','pF']).repeat(12)
    digLV = pd.Series(f'PLT_2.5_H{q}' for q in ['mN','mF','pN','pF']).repeat(12)
    HV = pd.Series(f'PLTHV_H{q}T{ch}' for q in ['mN','mF','pN','pF'] for ch in [*range(4)]).repeat(3)
    hub = pd.Series(4*['H05','H13','H21','H29']).repeat(3)
    roc = pd.Series(16*[0,1,2])
    roCh = pd.Series([*range(16)]).repeat(3)
    pixCh = pd.Series(sorted([*range(1,24)][::3] + [*range(1,24)][1::3])).repeat(3)
    fOrCh = pd.Series(f'{fed}-{fo}' for fed in [0,1] for i in [1,4,10,13,19,22,28,31] for fo in [*range(i,i+3)])
    data = zip(quadrants, flavor, mFec, anaLV, digLV, HV, hub, roCh, pixCh, roc, fOrCh)
    cols = ['quadrant','flavor','mFecCh','analogLV','digitalLV','HV','hub','readoutCh','pixFEDCh','roc','forFEDCh']
    return pd.DataFrame(data=data, columns=cols)

def FEDtoReadOut():
    return dict (zip( pltChannelMap()['pixFEDCh'], pltChannelMap()['readoutCh'] ))