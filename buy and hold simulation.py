# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 22:58:36 2021

@author: Iulian
"""
import pandas as pd 
import time
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import os

time_start = time.perf_counter()

def loadsp(fpath):
    df = pd.read_csv(fpath, index_col=0)
    df.index = [datetime.strptime(u, "%Y-%m-%d").date() for u in df.index]
    df = df.drop(df.index[np.isnan(df).all(axis=1)])
    return df

fulldata = loadsp('E:/Tech/Python/downloadedhistoryclose.csv')
print(f'Data loading from CSV ended. Time elapsed: {time.perf_counter()-time_start} seconds.')

testsize = 3531
indiceslist = ['^GSPC','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLK','XLU']
data = fulldata.drop(indiceslist, axis=1).loc[:,fulldata.count() > testsize+500]

nstocks_list = [1,2,3,4,5,10,20,50,data.shape[1]]
ssum = pd.DataFrame()
fee = 0.005 #fee for buying or selling one share
initialportfoliovalue = 100000.0
outputname = 'buy and hold'

plt.figure(dpi=300)
try:
    os.mkdir(f'E:/Tech/Python/Charts/{outputname}/')
except:
    pass

for nstocks in nstocks_list:
    #nstocks = 3
    print(f'Simulating buy and hold stradegy for {nstocks} stocks. Time elapsed: {time.perf_counter()-time_start} seconds.')

    simresults = pd.DataFrame(np.nan, index=fulldata.index[-testsize:], columns=[
        'portfolio value','holdings','nshares','fees'], dtype='O')
    simresults[['portfolio value','fees']] = 0.00
    
    sample = data.sample(n=nstocks, axis=1, random_state=100).iloc[-testsize:]
    nshares = initialportfoliovalue / nstocks / sample.iloc[0]
    
    simresults.loc[[simresults.index[0],simresults.index[-1]],'fees'] = fee * np.maximum(nshares, 200).sum()
    nshares.iloc[-1] -= simresults.iloc[0].loc['fees'] / sample.iloc[0,-1]

    simresults['holdings'] = [list(sample.columns) for i in simresults.index]
    simresults['nshares'] = [list(nshares) for i in simresults.index]

    simresults['portfolio value'] = (nshares * data.loc[simresults.index, sample.columns]).sum(axis=1) 
    
    simresults.at[simresults.index[-1],'holdings'] = []
    simresults.at[simresults.index[-1],'nshares'] = []
    simresults.at[simresults.index[-1],'portfolio value'] -= simresults.at[simresults.index[-1],'fees']

    simresults['cumulative fees'] = simresults['fees'].cumsum()   
        
    #simulation performance metrics
    for timeunit in [1,5,21,252]:
        simresults[f'{timeunit}-day return'] = 100 * (simresults['portfolio value'] / simresults['portfolio value'].shift(timeunit) - 1)
        simresults[f'{timeunit}-day profitable'] = (simresults[f'{timeunit}-day return'] > 0).astype(int)
        simresults.loc[np.isnan(simresults[f'{timeunit}-day return']), f'{timeunit}-day profitable'] = np.nan

    simresults['return to date'] = 100 * (simresults['portfolio value'] / initialportfoliovalue - 1)
    simresults['annualised return to date'] = 100 * ((simresults['portfolio value'] / initialportfoliovalue) ** (365.25 / (simresults.index - simresults.index[0]).days) - 1)
    simresults.loc[np.isnan(simresults['252-day return']), 'annualised return to date'] = np.nan
    
    simresults['drawdown anchor point'] = simresults['portfolio value'].cummax()
    simresults['drawdown'] = simresults['drawdown anchor point'] - simresults['portfolio value']
    simresults['drawdown %'] = 100 * simresults['drawdown'] / simresults['drawdown anchor point']
    simresults['in drawdown'] = (simresults['drawdown'] > 0).astype(int)
    simresults['drawdown duration'] = simresults['in drawdown'].groupby((simresults['in drawdown'] != simresults['in drawdown'].shift()).cumsum()).transform('size') * simresults['in drawdown']

    print(f'Plotting. Time elapsed: {time.perf_counter()-time_start} seconds.')
    plt.plot(list(simresults.index), simresults['portfolio value'], label=f'{nstocks} stocks', linewidth=0.5)

    #add summary statistics (mean, std, min, max etc.) on top of paths file
    summary = simresults.describe().append(simresults.select_dtypes('number').iloc[-1].rename('last'))   
    simresults = pd.concat([summary, simresults])
    
    print(f'Writing {nstocks} stocks path to CSV. Time elapsed: {time.perf_counter()-time_start} seconds.')
    simresults.to_csv(f'E:/Tech/Python/Charts/{outputname}/{outputname} {nstocks} stocks path.csv')

    #stack summaries in preparation for final summary file
    summary = summary.assign(n_stocks=f'{nstocks} stocks').loc[:,['n_stocks']+list(summary.columns)]
    ssum = ssum.append(summary)

#make the summary sheet more concise
elems = []
elems.append(ssum.loc['count','n_stocks'])
elems.append(ssum.loc['last',['return to date','annualised return to date','cumulative fees']])
elems.append(ssum.loc['max',['drawdown', 'drawdown %', 'drawdown duration']].rename(columns=lambda x: 'max '+x))
elems.append(ssum.loc['std',['1-day return','5-day return','21-day return','252-day return']].rename(columns=lambda x: x.replace('return','std')))
elems.append(ssum.loc['mean',['1-day return', '1-day profitable', '5-day return', '5-day profitable',
                            '21-day return', '21-day profitable', '252-day return','252-day profitable',
                            'drawdown', 'drawdown %', 'in drawdown', 'drawdown duration']])
elems = [e.reset_index(drop=True) for e in elems]
ssum_short = pd.concat(elems, axis=1).set_index('n_stocks')
ssum_short.to_csv(f'E:/Tech/Python/Charts/{outputname}/{outputname} summary.csv')

plt.xticks(rotation=25)
plt.legend(fontsize='x-small')
plt.title(outputname)
plt.yscale("log")
plt.savefig(f'E:/Tech/Python/Charts/{outputname} paths.jpg')

print(f'Simulation ended. Time elapsed: {time.perf_counter()-time_start} seconds.')    