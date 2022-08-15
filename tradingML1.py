# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 20:03:09 2021

@author: Iulian
"""
from loadsp import loadsp
import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np
import time
from datetime import datetime
import os


############
time_start = time.perf_counter()

pricepath = 'E:/Trading/Stock price data'
indpath= 'E:/Trading/Indicators'

fulldata = loadsp(f'{pricepath}/downloadedhistoryclose.csv')
# fulldata = fulldata.replace(0)
# fulldata = fulldata.replace(0, np.nan)
fulldata_lows = loadsp(f'{pricepath}/downloadedhistorylows.csv')
fulldata_open = loadsp(f'{pricepath}/downloadedhistoryopen.csv')
fulldata_ind = loadsp(f'{indpath}/macd.csv')
# fulldata_ind2 = loadsp(f'{indpath}/macd_signal.csv')
# fulldata_ind3 = loadsp(f'{indpath}/macd_divergence.csv')

print(f'Data loading from CSV ended. Time elapsed: {time.perf_counter()-time_start} seconds.')

firstappear = pd.Series([fulldata[s].first_valid_index() for s in fulldata], index = fulldata.columns)

###########setup model parameters
startdate = datetime(2008,1,2).date()
enddate =  fulldata.index[-1] #datetime(2019,12,31).date() #

#simulation parameters
initialportfoliovalue = 1e+5
nstocks = 2
simul_step = 1 #we change the portfolio every simul_step periods
fee = 0.005 #fee in dollars for buying or selling one share
BAS = 0.0004 #bid-ask spread penalty (expressed as relative to price)
maxloss_list = [0, 0.002, 0.01, 0.03, 0.07, 0.5]
SLP = 0.001 #penalty (relative to price) for trigerring stop-loss sales (will sell below the stop-loss price)
outputname = 'bMACD by_stoploss_adj 2008-now SLP0.001 2stocks'
outputpath = 'E:/Trading/Charts'

#auxiliary data
fulldata_returns = (100 * (fulldata / fulldata.shift(1) - 1))
recession = pd.DataFrame(fulldata_returns['^GSPC'])
for k in [5,8,12,20]:
    recession[f'{k}-day mean'] = recession['^GSPC'].rolling(k).mean()
    recession[f'{k}-day std'] = recession['^GSPC'].rolling(k).std()  
recession['in recession'] = (recession['12-day std'] >= 1.5) | (recession['20-day std'] >= 1.5) | (recession['8-day std'] >= 1.5) | (recession['5-day std'] >= 1.5)


############trading simulation
data = fulldata.loc[startdate:enddate, fulldata.columns]
data_lows = fulldata_lows.loc[startdate:enddate, fulldata.columns]
data_open = fulldata_open.loc[startdate:enddate, fulldata.columns]
data['cash'] = 1
data_lows['cash'] = 1
data_open['cash'] = 1

tradeperiods = data.index[:-1:simul_step]
returns_sorted = pd.Series([fulldata_ind.loc[c].sort_values(ascending=True) for c in tradeperiods], index = tradeperiods)
ssum = pd.DataFrame()

plt.figure(dpi=300)
try:
    os.mkdir(f'{outputpath}/{outputname}/')
except:
    pass

for maxloss in maxloss_list:
    #nstocks = 3
    print(f'Simulating trading stradegy for {maxloss} stoploss. Time elapsed: {time.perf_counter()-time_start} seconds.')
    
    simresults = pd.DataFrame('', index=data.index, columns=[
        'beginning holdings','MACD','portfolio value','final holdings','fees'])
    simresults[['portfolio value','fees']] = 0.00
    
    for t in simresults.index:
        
        if t == simresults.index[0]: #initialization
            simresults.at[t, 'portfolio value'] = initialportfoliovalue
            simresults.at[t, 'beginning holdings'] = pd.Series([initialportfoliovalue], index=['cash'])
            
        else:
            #carry over portfolio from end of previous day
            simresults.at[t, 'beginning holdings'] = simresults.shift(1).at[t,'final holdings'].copy()
            
            # #check whether stop-loss was triggered
            keyprices_lows = data_lows.loc[t, simresults.at[t, 'beginning holdings'].index]
            keyprices_open = data_open.loc[t, simresults.at[t, 'beginning holdings'].index]
            to_sell = list(keyprices_lows.lt(stoplossprices).index[keyprices_lows.lt(stoplossprices)])
            sellprices = stoplossprices.combine(keyprices_open, min) * (1-SLP)
            #we reflect the sale in beginning holdings rather than final holdings so as not to be masked up by the next trade
            if len(to_sell)>0:
                if 'cash' in simresults.at[t, 'beginning holdings']:
                    simresults.at[t, 'beginning holdings'].loc['cash'] += (simresults.at[t, 'beginning holdings'].loc[to_sell] * sellprices.loc[to_sell]).sum() 
                else:
                    simresults.at[t, 'beginning holdings'].loc['cash'] = (simresults.at[t, 'beginning holdings'].loc[to_sell] * sellprices.loc[to_sell]).sum()                   
                simresults.at[t, 'fees'] += fee * np.maximum(simresults.at[t, 'beginning holdings'].loc[to_sell], 200).sum() 
                simresults.at[t, 'beginning holdings'].loc['cash'] -= simresults.at[t, 'fees']
                simresults.at[t, 'beginning holdings'].drop(to_sell, inplace=True)
            
            #evaluate portflio with this day's prices
            simresults.at[t, 'portfolio value'] = (simresults.at[t, 'beginning holdings'] * data.loc[t, simresults.at[t, 'beginning holdings'].index]).sum()
               
        if t == simresults.index[-1]: #dispose of portfolio
            simresults.at[t, 'fees'] += fee * np.maximum(simresults.at[t, 'beginning holdings'].drop('cash', errors='ignore'), 200).sum()
            simresults.at[t,'portfolio value'] -= simresults.at[t,'fees']
            simresults.at[t, 'final holdings'] = pd.Series([simresults.at[t, 'portfolio value']], index=['cash'])
       
        elif t in tradeperiods: 
            #trade - choose the n stocks with the best predicted return
            choices = returns_sorted.at[t].iloc[:nstocks]
            #choices = returns.loc[t].sample(n=nstocks)
            choiceprices = data.loc[t, choices.index]
            #maxloss = maxloss_recession if recession.loc[t,'in recession'] else maxloss_normal
            stoplossprices = choiceprices * (1-maxloss)
            simresults.at[t,'final holdings'] = simresults.at[t, 'portfolio value'] * (1-BAS) / nstocks / choiceprices
            simresults.at[t,'MACD'] = choices.round(2) #this will be shifted down to the next trade period later
            simresults.at[t,'fees'] += fee * np.maximum(simresults.at[t,'final holdings'].sub(simresults.at[t, 'beginning holdings'], fill_value=0).drop('cash', errors='ignore'), 200).sum()
            simresults.at[t,'portfolio value'] -= simresults.at[t,'fees']
            #make sure that we do not forget to apply the fees before we carry over the holdings into the next period
            #since we spent all our cash, we pay the fee with the last stock in our portfolio
            simresults.at[t,'final holdings'].iat[-1] -= simresults.at[t,'fees'] / choiceprices.iat[-1]
            
        else:
            #beginning holdings are maintained and become final holdings
            simresults.at[t,'final holdings'] = simresults.at[t, 'beginning holdings'].copy()
        
        if simresults.at[t,'portfolio value'] < 0:
            simresults = simresults.loc[:t]
            break #we're bankrupt. Stop the path so as not to go down into negative numbers where a lot of ratios (e.g. returns) lose meaning

            
    simresults['cumulative fees'] = simresults['fees'].cumsum()   
    #tidy up the holdings columns - keep just the stock names
    simresults.loc[:,'beginning holdings'] = simresults.loc[:,'beginning holdings'].apply(lambda x: list(x.index))
    simresults.loc[:,'final holdings'] = simresults.loc[:,'final holdings'].apply(lambda x: list(x.index))
    simresults.loc[:,'MACD'] = simresults.loc[:,'MACD'].apply(list)
        
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
    plt.plot(list(simresults.index), simresults['portfolio value'], label=f'{maxloss} stoploss', linewidth=0.5)

    #add summary statistics (mean, std, min, max etc.) on top of paths file
    summary = pd.concat([simresults.describe(), simresults.select_dtypes('number').iloc[-1:]], axis=0)
    summary.index.values[-1] = 'last'
    simresults = pd.concat([summary, simresults])
    
    print(f'Writing {maxloss} stoploss path to CSV. Time elapsed: {time.perf_counter()-time_start} seconds.')
    simresults.to_csv(f'{outputpath}/{outputname}/{outputname} {maxloss} stoploss path.csv')

    #stack summaries in preparation for final summary file
    summary = summary.assign(stoploss=f'{maxloss} stoploss').loc[:,['stoploss']+list(summary.columns)]
    ssum = pd.concat([ssum, summary])
    
    
#make the summary sheet more concise
elems = []
elems.append(ssum.loc['count','stoploss'])
elems.append(ssum.loc['last',['return to date','annualised return to date','cumulative fees']])
elems.append(ssum.loc['max',['drawdown', 'drawdown %', 'drawdown duration']].rename(columns=lambda x: 'max '+x))
elems.append(ssum.loc['std',['1-day return','5-day return','21-day return','252-day return']].rename(columns=lambda x: x.replace('return','std')))
elems.append(ssum.loc['mean',['1-day return', '1-day profitable', '5-day return', '5-day profitable',
                            '21-day return', '21-day profitable', '252-day return','252-day profitable',
                            'drawdown', 'drawdown %', 'in drawdown', 'drawdown duration']])
elems = [e.reset_index(drop=True) for e in elems]
ssum_short = pd.concat(elems, axis=1).set_index('stoploss')
ssum_short.to_csv(f'{outputpath}/{outputname}/{outputname} summary.csv')

plt.xticks(rotation=25)
plt.legend(fontsize='x-small')
plt.title(outputname)
plt.yscale("log")
plt.savefig(f'{outputpath}/{outputname} paths.jpg')

print(f'Simulation ended. Time elapsed: {time.perf_counter()-time_start} seconds.')