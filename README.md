# Igramatki Trading Pipeline

This is my own first algorithmic trading project! It evolved organically as I took an interest in trading and decided to hone my quantitative analysis and programming skills.

## Description

The main algorithm does the following:
1)	Downloads the historical daily stock price for the S&P 500 stocks
2)	Generates a few indicators such as MACD, RSI, stochastic oscillator
3)	Picks the n stocks (currently n=3) with the lowest value of the indicator (currently MACD)
4)	Connects to the TWS API and instructs it to switch position to these n stocks 

It can be automated to fire off every day by using Windows Task Scheduler and the 'start trading apps.bat' file.

## File components and what they do

-FILE DESCRIPTIONS TO BE ADDED SOON

### Main algorithm

main.py
updatestockdata.py
gen_indicators.py
MLpredict_returns.py

### Auxiliary code

choice_returns_compare.py
backtesting.py
buy and hold simulation.py
finstatements webscraping.py
loadsp.py
process Flex Queries.do
recession detect.py
recession overlays.py
start_trading_apps.bat

## Required software

Python (version 3.10 or above)
Stata (version 14 or above) - only for the "process flex queries.do" file

## Authors

Iulian Gramatki
https://www.linkedin.com/in/iulian-gramatki-582b77145/

