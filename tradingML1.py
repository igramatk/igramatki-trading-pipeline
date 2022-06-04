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
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from statsmodels.tsa.arima.model import ARIMA

############
time_start = time.perf_counter()

pricepath = 'E:/Trading/Stock price data'
indpath= 'E:/Trading/Indicators'

fulldata = loadsp(f'{pricepath}/downloadedhistoryclose.csv')
# fulldata = fulldata.replace(0)
# fulldata = fulldata.replace(0, np.nan)
fulldata_lows = loadsp(f'{pricepath}/downloadedhistorylows.csv')
fulldata_ind = loadsp(f'{indpath}/macd.csv')
# fulldata_ind2 = loadsp(f'{indpath}/macd_signal.csv')
# fulldata_ind3 = loadsp(f'{indpath}/macd_divergence.csv')

print(f'Data loading from CSV ended. Time elapsed: {time.perf_counter()-time_start} seconds.')

firstappear = pd.Series([fulldata[s].first_valid_index() for s in fulldata], index = fulldata.columns)

###########setup model parameters
nlags = 12 #number of AR lags
step = 1 #the step of each lag (every k periods)
npfore = 1 #how many periods ahead to forecast
# nma = 3 #number of moving average lags for ARIMA
# d = 1 #level of differencing for ARIMA 
testsize = 3600
linesrequired = 4100
shift = 0
startdate = datetime(1991,1,1).date()
enddate = fulldata.index[-1] #datetime(2022,1,11).date()

#simulation parameters
initialportfoliovalue = 1e+5
nstocks_list = [1,2,3,4,5,10,20]
simul_step = 1 #we change the portfolio every simul_step periods
fee = 0.005 #fee in dollars for buying or selling one share
BAS = 0.0004 #bid-ask spread penalty (expressed as relative to price)
maxloss_normal = 0.99 #maximum relative drop in stock price (daily low) before stop loss sale is triggered
maxloss_recession = 0.01
SLP = 0.001 #penalty (relative to price) for trigerring stop-loss sales (will sell below the stop-loss price)
outputname = f'test bottom macd newest recession any 1.5 none-1% stoploss {simul_step}-day-trade'
outputpath = 'E:/Trading/Charts'

#auxiliary data
fulldata_returns = (100 * (fulldata / fulldata.shift(npfore) - 1))
#fulldata_daily_returns = (100 * (fulldata / fulldata.shift(1) - 1))
recession = pd.DataFrame(fulldata_returns['^GSPC'])
for k in [5,8,12,20]:
    recession[f'{k}-day mean'] = recession['^GSPC'].rolling(k).mean()
    recession[f'{k}-day std'] = recession['^GSPC'].rolling(k).std()  
recession['in recession'] = (recession['12-day std'] >= 1.5) | (recession['20-day std'] >= 1.5) | (recession['8-day std'] >= 1.5) | (recession['5-day std'] >= 1.5)

################training the model    
indiceslist = ['^GSPC','XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU']
valid_stocks = fulldata.drop(indiceslist, axis=1).loc[:,fulldata.count() > linesrequired].columns
data = fulldata_returns.loc[startdate:enddate, fulldata.count() > linesrequired]
# data_ind = fulldata_ind.loc[data.index, data.columns]
# data_ind2 = fulldata_ind2.loc[data.index, data.columns]
# data_ind3 = fulldata_ind3.loc[data.index, data.columns]
valid_indices = [i for i in indiceslist if i in data.columns]
returns_raw=pd.DataFrame(index = data.index)
psum=[]
predictions=[]
i=0

for s in valid_stocks:
 #   try:
        #s = 'AAPL'
        i+=1
        print(f'Building model for stock {s} (number {i}). Time elapsed: {time.perf_counter()-time_start} seconds.')
        y = data[s]
        
        # #pull financial data
        # f = pd.read_csv(f'E:/Trading/Financial data/{s}.csv', index_col=0)
        # f1 = f.replace('[,%]', '', regex=True).apply(pd.to_numeric)
        # #calculate key financial metrics
        # fd = pd.DataFrame(100 * f1.loc['Net Income'] / f1.loc['Total Assets'], columns=['ROA'])
        # fd['ROE'] = 100 * f1.loc['Net Income'] / f1.loc['Total Stockholders Equity']
        # fd['EPS'] = f1.loc['EPS']
        # fd['OCFPS'] = f1.loc['Cash Provided by Operating Activities'] / f1.loc['Weighted Average Shares Outstanding']
        # #expand index to prepare for joining
        # fd.index = [datetime.strptime(u, "%Y-%m-%d").date() for u in fd.index]
        # fd = fd.reindex(index = pd.date_range(datetime(1985,1,1), datetime.now())).ffill().loc[data.index]
        # fd.index = [u.date() for u in fd.index]
        # fd['inverse PE'] = 100 * fd['EPS'] / fulldata[s]
        # fd['% OCFPS'] = 100 * fd['OCFPS'] / fulldata[s]
        
        x = pd.concat([data[[s]].shift(i*step+npfore).add_prefix(f't-{i*step+npfore} ') 
                        for i in range(nlags)] #+
                      #[fd[['inverse PE']].shift(npfore).add_prefix(f't-{npfore} ')]
                      #[data_ind[[s]].shift(i*step+npfore).add_prefix(f'IND1 t-{i*step+npfore} ') 
                      # for i in range(1)] +
                      # [data_ind2[[s]].shift(i*step+npfore).add_prefix(f'IND2 t-{i*step+npfore} ') 
                      #  for i in range(1)] +
                      #[data_ind3[[s]].shift(i*step+npfore).add_prefix(f'IND3 t-{i*step+npfore} ') 
                      #  for i in range(1)]
                        , axis=1)
        x = x.dropna()
        y = y.loc[x.index]
        
        xtrain, xtest, ytrain, ytest = train_test_split(x, y, test_size=testsize, shuffle=False)
        
        lr = LinearRegression()
        lr.fit(xtrain,ytrain)
        
        ytest = y
        xtest = x
        ypred = pd.Series(lr.predict(xtest), index=ytest.index, name='prediction')

        # #for time series models from statsmodels
        # y = y.dropna()
        # yindex = y.index
        # y = y.reset_index(drop=True)
        # ytrain = y[:-testsize]
        # ytest = y[-testsize:]
        
        # lr = ARIMA(ytrain, order=(nlags,d,nma))
        # model_fit = lr.fit()
        # model_ypred = model_fit.append(ytest)
        # ypred = pd.Series(model_ypred.predict(ytest.index[0], ytest.index[-1]), index=ytest.index, name='prediction')
           
        ###model performance metrics
        ycomp = pd.concat([ytest, ypred], axis=1)
        #ycomp.index = data[-testsize:].index
        ycomp['error'] = ycomp['prediction'] - ycomp[s]
        # ycomp['actual price change'] = ycomp[s] - y.shift(npfore).loc[ytest.index]
        # ycomp['predicted price change'] = ycomp['prediction'] - y.shift(npfore).loc[ytest.index]
        # ycomp['actual return'] = 100 * ycomp['actual price change'] / y.shift(npfore).loc[ytest.index]
        # ycomp['predicted return'] = 100 * ycomp['predicted price change'] / y.shift(npfore).loc[ytest.index]
        # ycomp['return error'] = ycomp['predicted return'] - ycomp['actual return']
        # rmse = np.sqrt((ycomp['error'] ** 2).mean())
        # returnmeanerror = ycomp['return error'].mean()
        # returnrmse = np.sqrt((ycomp['return error'] ** 2).mean())
        
        ycomp['guessed direction'] = (np.sign(ycomp['prediction']) == np.sign(ycomp[s])).astype(int)
        ycomp['overstated return'] = (ycomp['prediction'] > ycomp[s]).astype(int)
        # guessdir = 100 * ycomp['guessed direction'].mean()
        # overstate = 100 * ycomp['overstated return'].mean()
        psum.append(ycomp.describe())
        predictions.append(ycomp)
        
        #final model output
        returns_raw = pd.concat([returns_raw, ycomp['prediction'].rename(s)], axis=1)
        
    # except:
    #     print(f'Building model for stock {s} failed. Time elapsed: {time.perf_counter()-time_start} seconds.')

    
returns_toshift = returns_raw.iloc[-testsize-shift:]
returns = returns_toshift.shift(shift).dropna()

rsum = returns.describe()
print(f'Model training ended. Time elapsed: {time.perf_counter()-time_start} seconds.')



############trading simulation
data = fulldata.loc[returns.index, fulldata.columns]
data_lows = fulldata_lows.loc[returns.index, fulldata.columns]
data['cash'] = 1
data_lows['cash'] = 1

tradeperiods = returns.index[:-1:simul_step]
returns_sorted = pd.Series([fulldata_ind.loc[c].sort_values(ascending=True) for c in tradeperiods], index = tradeperiods)
ssum = pd.DataFrame()

plt.figure(dpi=300)
try:
    os.mkdir(f'{outputpath}/{outputname}/')
except:
    pass

for nstocks in nstocks_list:
    #nstocks = 3
    print(f'Simulating trading stradegy for top {nstocks} stocks. Time elapsed: {time.perf_counter()-time_start} seconds.')
    
    simresults = pd.DataFrame('', index=returns.index, columns=[
        'beginning holdings','expected return','portfolio value','final holdings','fees'])
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
            to_sell = list(keyprices_lows.lt(stoplossprices).index[keyprices_lows.lt(stoplossprices)])
            #we reflect the sale in beginning holdings rather than final holdings so as not to be masked up by the next trade
            if len(to_sell)>0:
                if 'cash' in simresults.at[t, 'beginning holdings']:
                    simresults.at[t, 'beginning holdings'].loc['cash'] += (simresults.at[t, 'beginning holdings'].loc[to_sell] * stoplossprices.loc[to_sell]).sum() * (1-SLP)
                else:
                    simresults.at[t, 'beginning holdings'].loc['cash'] = (simresults.at[t, 'beginning holdings'].loc[to_sell] * stoplossprices.loc[to_sell]).sum() * (1-SLP)                    
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
            maxloss = maxloss_recession if recession.loc[t,'in recession'] else maxloss_normal
            stoplossprices = choiceprices * (1-maxloss)
            simresults.at[t,'final holdings'] = simresults.at[t, 'portfolio value'] * (1-BAS) / nstocks / choiceprices
            simresults.at[t,'expected return'] = choices.round(2) #this will be shifted down to the next trade period later
            simresults.at[t,'fees'] += fee * np.maximum(simresults.at[t,'final holdings'].sub(simresults.at[t, 'beginning holdings'], fill_value=0).drop('cash', errors='ignore'), 200).sum()
            simresults.at[t,'portfolio value'] -= simresults.at[t,'fees']
            #make sure that we do not forget to apply the fees before we carry over the holdings into the next period
            #since we spent all our cash, we pay the fee with the stock with the worst predicted returns in our portfolio
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
    simresults.loc[:,'expected return'] = simresults.loc[:,'expected return'].apply(list).shift(simul_step)
        
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
    summary = pd.concat([simresults.describe(), simresults.select_dtypes('number').iloc[-1:]], axis=0)
    summary.index.values[-1] = 'last'
    simresults = pd.concat([summary, simresults])
    
    print(f'Writing {nstocks} stocks path to CSV. Time elapsed: {time.perf_counter()-time_start} seconds.')
    simresults.to_csv(f'{outputpath}/{outputname}/{outputname} {nstocks} stocks path.csv')

    #stack summaries in preparation for final summary file
    summary = summary.assign(n_stocks=f'{nstocks} stocks').loc[:,['n_stocks']+list(summary.columns)]
    ssum = pd.concat([ssum, summary])
    
    
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
ssum_short.to_csv(f'{outputpath}/{outputname}/{outputname} summary.csv')

plt.xticks(rotation=25)
plt.legend(fontsize='x-small')
plt.title(outputname)
plt.yscale("log")
plt.savefig(f'{outputpath}/{outputname} paths.jpg')

print(f'Simulation ended. Time elapsed: {time.perf_counter()-time_start} seconds.')