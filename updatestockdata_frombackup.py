# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 21:52:43 2022

@author: Iulian
"""
for c in backup.columns:
    if 'LRCX' in c:
        print(c)
        print(yahoodata[c].iloc[-1])
        yahoodata[c].iloc[-1] = backup2[c].iloc[-1]
        print(yahoodata[c])
