# -*- coding: utf-8 -*-
"""
Created on Mon Nov 15 18:26:07 2021

@author: Iulian
"""
import mechanicalsoup
import pandas as pd
import time
import numpy as np
import yfinance as yf

time_start = time.perf_counter()

sp500 = pd.read_excel('E:/Trading/S&P500.xlsx')

br = mechanicalsoup.Browser()

j=0
for s in sp500.iloc[457:504,0]:
    #s = 'AAP'
    j += 1
    url = f'https://roic.ai/company/{s}?fs=full'
    
    print(f'Webscraping financial statements for stock {s} (number {j}). Time elapsed : {time.perf_counter()-time_start} seconds.')
    response = br.get(url)
    
    if response.status_code == 200:  
        print(f'Request succeeded - code {response.status_code}. Time elapsed : {time.perf_counter()-time_start} seconds.')
        soup = response.soup
        
        years_loc = soup.find(class_ = "col-start-6")
        columns = pd.Index([y.string for y in years_loc])
        
        items_loc = soup.find(string = "INCOME STATEMENT").parent.parent
        index = pd.Index([l.string for l in items_loc])
        
        while index.duplicated().any():
            index.values[index.duplicated()] = index.values[index.duplicated()] + '1' 
        
        index_s = index.drop(["INCOME STATEMENT","BALANCE SHEET", "CASH FLOW STATEMENT"])
        
        contents_loc = soup.find_all(class_ = "col-start-6")[1]
        finstat = pd.concat([pd.Series(contents_loc.contents[i].strings, index = index_s, 
                         name=columns[i]) for i in range(len(columns))], axis = 1)
        finstat = pd.DataFrame(finstat, index=index, columns=columns)
        finstat = finstat.drop(['SEC Link','SEC Link1','SEC Link11'])
        finstat = finstat.replace('- -', np.nan)
        finstat = finstat.dropna(axis=1, how='all')        

        #include the dates when the reports were released
        print(f'Downloading dates of financial statements. Time elapsed : {time.perf_counter()-time_start} seconds.''')
        fdates = yf.Ticker(s).financials.columns
        if 'Open' in fdates:
            time.sleep(3)
            fdates = yf.Ticker(s).financials.columns
        fdates1 = list(fdates) + [fdates[-1].replace(year = fdates[-1].year-i-1) for i in range(len(finstat.columns)-len(fdates))]
        finstat.columns = fdates1[0:len(finstat.columns)]
        
        finstat.to_csv(f'E:/Trading/Financial data/{s}.csv')
        
    else:
        print(f'''Request failed for stock {s} (number {j}) with error code {response.status_code}.
              Time elapsed : {time.perf_counter()-time_start} seconds.''')

print(f'Finished reading all financial statements. Time elapsed : {time.perf_counter()-time_start} seconds.')        

# aux = pd.read_csv('E:/Tech/Financial data/AAPL.csv', index_col=0)
# aux = aux.replace('[,%]', '', regex=True)
# aux1 = aux.apply(pd.to_numeric)