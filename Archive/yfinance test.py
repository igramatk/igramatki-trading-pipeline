# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 15:06:59 2021

@author: Iulian
"""
import yfinance as yf
import pandas as pd

msft = yf.Ticker("MSFT")

# get stock info
info = msft.info

# get historical market data
hist = msft.history(period="max")

# show actions (dividends, splits)
actions = msft.actions

# show dividends
div = msft.dividends

# show splits
splits = msft.splits

# show financials
fundam = msft.financials
fundam_q = msft.quarterly_financials

# show major holders
mh = msft.major_holders

# show institutional holders
ih = msft.institutional_holders

# show balance sheet
bs = msft.balance_sheet
bs_q = msft.quarterly_balance_sheet

# show cashflow
cf = msft.cashflow
cf_q = msft.quarterly_cashflow

# show earnings
inc = msft.earnings
inc_q = msft.quarterly_earnings

# show sustainability
sus = msft.sustainability

# show analysts recommendations
recom = msft.recommendations

# show next event (earnings, etc)
events = msft.calendar

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
isin = msft.isin

# show options expirations
optsum = msft.options

# get option chain for specific expiration
opt = msft.option_chain('2021-12-10')
# data available via: opt.calls, opt.puts

sp500 = pd.read_excel('E:/Tech/Python/S&P500.xlsx')
yahoodata = yf.download(tickers=list(sp500['Symbol']), period='max')
yahoodata1 = yahoodata['Close']
yahoodata1.to_csv('E:/Tech/Python/downloadedhistoryfull.csv')