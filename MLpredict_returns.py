# -*- coding: utf-8 -*-
"""
Created on Wed Nov 17 22:29:41 2021

@author: Iulian
"""
import pandas as pd 
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression
from loadsp import loadsp


#time_start = time.perf_counter()

fulldata = loadsp('E:/Trading/Stock price data/downloadedhistoryclose.csv')
print(f'Data loading from CSV ended. Time elapsed: {time.perf_counter()-time_start} seconds.')


#parameters
nlags = 12
step = 1
npfore = 1
startdate = datetime(1991,1,1).date()
linesrequired = 100
per = 5 #number of periods to show in the recommend variable, descending from t+1


#auxiliary data
fulldata_returns = (100 * (fulldata / fulldata.shift(npfore) - 1))
actual_returns_sorted = pd.Series([fulldata_returns.iloc[-i-1].sort_values(ascending=False) for i in range(50)], index=fulldata.index[:-51:-1])

print(f'Calculating recession indicators. Time elapsed: {time.perf_counter()-time_start} seconds.')
recession = pd.DataFrame(fulldata_returns['^GSPC'])
for k in [5,8,12,20]:
    recession[f'{k}-day mean'] = recession['^GSPC'].rolling(k).mean()
    recession[f'{k}-day std'] = recession['^GSPC'].rolling(k).std()  
recession['in recession'] = recession['12-day std'] >= 2


indiceslist = ['^GSPC']
data = fulldata_returns.loc[startdate:, (fulldata.count() > linesrequired) & ~(fulldata.iloc[-1].isna())].drop(indiceslist, axis=1)
returns=pd.DataFrame()
i=0

returns = pd.DataFrame(index = [f't+{npfore-j+1}' for j in range(1,npfore+per)], columns = data.columns)

for s in data:
    #s = 'AAPL'
    i+=1
    if i % 100 == 1:
        print(f'Building model for stock {s} (number {i}). Time elapsed: {time.perf_counter()-time_start} seconds.')
    y = data[s]
    
    x = pd.concat([data[[s]].shift(i*step+npfore).add_prefix(f't-{i*step+npfore} ') 
                   for i in range(nlags)], axis=1)
    x = x.dropna()
    y = y.loc[x.index]
    y = y.dropna()
    x = x.loc[y.index]
    
    lr = LinearRegression()
    lr.fit(x,y)

    x_to_predict = pd.DataFrame([data[s].iloc[-j:-j-nlags*step:-step].values 
                   for j in range(1,npfore+per)], columns = x.columns, 
                                index=returns.index)
    returns.loc[:,s] = lr.predict(x_to_predict)

recommend = pd.Series([i[1].sort_values(ascending=False) for i in returns.iterrows()], index = returns.index)

print(f'Program ended. Time elapsed: {time.perf_counter()-time_start} seconds.')