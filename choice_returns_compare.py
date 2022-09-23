# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 22:39:55 2022

@author: Iulian
"""

########
#short snippet to compare how the choices from the bottom MACD algorithm
#compare to other S&P500 stocks in terms of their actual daily returns.
########
#Run gen_indicators and MLpredict_returns first to get the necessary inputs
########

actual_returns_sorted_full = pd.Series([fulldata_returns.loc[c].sort_values(ascending=False) 
                                        for c in fulldata.index[::-1]], 
                                       index=fulldata.index[::-1])
choice_bmacd_full = pd.Series([macd.loc[c].sort_values(ascending=True) 
                               for c in fulldata.index[::-1]], 
                              index=fulldata.index[::-1])

choice_bmacd_returns_ranking = [[actual_returns_sorted_full.iloc[i].index.
                                 get_loc(choice_bmacd_full.iloc[i+1].index[a])+1 
                                 for a in range(10)] 
                                for i in range(fulldata.shape[0]-1)]
choice_bmacd_returns_ranking = pd.DataFrame(choice_bmacd_returns_ranking, 
                                            index = choice_bmacd_full.index[:-1], 
                                            columns = [f'{j+1}th stock' 
                                                       for j in range(10)])

choice_bmacd_names = pd.DataFrame([choice_bmacd_full.iloc[i+1].index 
                                   for i in range(choice_bmacd_full.shape[0]-1)], 
                                  index = choice_bmacd_full.index[:-1], 
                                  columns = [f'{j+1}th stock' 
                                             for j in range(fulldata.shape[1])])

choice_bmacd_returns_cumrank = choice_bmacd_returns_ranking.cumsum(axis=1) / range(1,11)
choice_bmacd_returns_cumrank.columns = [f'top {j} stocks' for j in range(1,11)]


startdate = datetime(2015, 1, 1).date()
                                          
choice_bmacd_returns_ranking_summary = choice_bmacd_returns_ranking.loc[
    :startdate].describe()
choice_bmacd_returns_cumrank_summary = choice_bmacd_returns_cumrank.loc[
    :startdate].describe()


fulldata_logreturns_tmrw = (100*np.log(1 + fulldata_returns.shift(-1)/100)).round(2)
choice_bmacd_returns = pd.DataFrame([list(fulldata_logreturns_tmrw.
                             loc[day, choice_bmacd_full.loc[day].index]) 
                        for day in fulldata_returns.index[:-1]],
                                    index = fulldata.index[1:],
                                     columns = [f'{j+1}th stock' 
                                                for j in range(504)]).iloc[::-1]

choice_bmacd_returns_cum = (choice_bmacd_returns.cumsum(axis=1) / range(1,505)).round(2)
choice_bmacd_returns_cum.columns = [f'top {j} stocks' for j in range(1,505)]

choice_bmacd_returns_summary = choice_bmacd_returns.loc[
    :startdate].describe()
choice_bmacd_returns_cum_summary = choice_bmacd_returns_cum.loc[
    :startdate].describe()

fulldata_logreturns_tmrw.loc[startdate:].describe().loc['mean'].describe()
fulldata_logreturns_tmrw.loc[startdate:].describe().loc['50%'].describe()