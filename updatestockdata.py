# -*- coding: utf-8 -*-
"""
Created on Wed Nov 17 22:14:26 2021

@author: Iulian
"""
import pandas as pd 
import yfinance as yf
from yahoo_fin.stock_info import tickers_sp500
import time

#time_start = time.perf_counter()

#sp500 = pd.read_excel('E:/Trading/S&P500.xlsx')
indiceslist = ['^GSPC','XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU']
tickerslist = tickers_sp500() + indiceslist

yahoodata = yf.download(tickers=tickerslist, start = '1986-01-01')
yahoodata.index = yahoodata.index.date
print(f'Initial data reading ended. Time elapsed: {time.perf_counter()-time_start} seconds.')

yc = yahoodata['Close']
spotnans = yc.isna().apply(sum, axis=1)
spotnans2 = pd.Series([list(yc.columns[yc.loc[j].isna()]) for j in yc.index], index=yc.index)
print(f'There are {spotnans[-1]} missing values in the last period')

line = -1
retries = 0
while spotnans[line] > 0:
    print(f'Updating data. Time elapsed: {time.perf_counter()-time_start} seconds.')
    
    oldspotnans = spotnans2[line].copy()
    if spotnans[line] == 1:
        spotnans2[line].append('AAPL') #to prevent errors when only one stock is left
        
    yd1 = yf.download(tickers=spotnans2[line], start = spotnans.index[line])
    #check for date format mismatch
    try:
        yd1.index = yd1.index.date
    except:
        yd1.index = yahoodata.index[-yd1.shape[0]:]
    
    backup = yahoodata.loc[yd1.index, yd1.columns]  
    yahoodata.loc[yd1.index, yd1.columns] = yd1
    yc = yahoodata['Close']
    spotnans = yc.isna().apply(sum, axis=1)
    spotnans2 = pd.Series([list(yc.columns[yc.loc[j].isna()]) for j in yc.index], index=yc.index)
    print(f'There are now {spotnans[-1]} missing values in the last period')

    if spotnans2[line] != oldspotnans:   #wait a while if no new data is returned
        pass
    elif retries < 2:
        print(f'No new data obtained - waiting 300 seconds. Total time elapsed: {time.perf_counter()-time_start} seconds.')
        time.sleep(300)
        retries += 1 
    else:
        print(f'No new data obtained 3 times in a row. Terminating download. Total time elapsed: {time.perf_counter()-time_start} seconds.')   
        break


pricepath = 'E:/Trading/Stock price data'
print(f'Writing data to disk. Time elapsed: {time.perf_counter()-time_start} seconds.')
yahoodata['Close'].to_csv(f'{pricepath}/downloadedhistoryclose.csv')
yahoodata['Open'].to_csv(f'{pricepath}/downloadedhistoryopen.csv')
yahoodata['Low'].to_csv(f'{pricepath}/downloadedhistorylows.csv')
yahoodata['High'].to_csv(f'{pricepath}/downloadedhistoryhighs.csv')
print(f'Data writing ended. Time elapsed: {time.perf_counter()-time_start} seconds.')