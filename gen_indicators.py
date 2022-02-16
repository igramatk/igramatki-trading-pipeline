# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 21:03:56 2021

@author: Iulian
"""
import pandas as pd 
import numpy as np
from loadsp import loadsp 
import time

############
time_start = time.perf_counter()

pricepath = 'E:/Trading/Stock price data'
indpath= 'E:/Trading/Indicators'

fulldata = loadsp(f'{pricepath}/downloadedhistoryclose.csv')
fulldata_lows = loadsp(f'{pricepath}/downloadedhistorylows.csv')
fulldata_highs = loadsp(f'{pricepath}/downloadedhistoryhighs.csv')


#RSI
N = 12
alpha = 1/N
minp = 4

U = np.maximum(fulldata - fulldata.shift(1), 0)
D = -np.minimum(fulldata - fulldata.shift(1), 0)

Usmma = U.ewm(alpha = alpha, min_periods=0).mean()
Dsmma = D.ewm(alpha = alpha, min_periods=0).mean()

rs = Usmma / Dsmma
rsi = 100 * (rs/(1+rs))

rsi.to_csv(f'{indpath}/rsi.csv')


#MACD
a = 12
b = 26
c = 9

ema1 = fulldata.ewm(span=a).mean() 
ema2 = fulldata.ewm(span=b).mean()
macd = 100 * (ema1 - ema2) / ema2
macd_signal = macd.ewm(span=c).mean()
macd_divergence = macd - macd_signal

macd.to_csv(f'{indpath}/macd.csv')
macd_signal.to_csv(f'{indpath}/macd_signal.csv')
macd_divergence.to_csv(f'{indpath}/macd_divergence.csv')


#Stochastic Oscillator
k = 12 

high = fulldata_highs.rolling(k).max()
low = fulldata_lows.rolling(k).min()
so = 100 * (fulldata - low) / (high - low)

so.to_csv(f'{indpath}/so.csv')