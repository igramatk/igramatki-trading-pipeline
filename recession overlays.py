# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 18:35:18 2022

@author: Iulian
"""
plt.figure(dpi=300)
outputpath = 'E:/Trading/Charts'

recession['recession 5d 3'] = (recession['5-day std'] >= 3)
recession['recession 5d 4'] = (recession['5-day std'] >= 4)
recession['recession 8d 2.5'] = (recession['8-day std'] >= 2.5)
recession['recession 8d 3'] = (recession['8-day std'] >= 3)
recession['recession 8d 3.5'] = (recession['8-day std'] >= 3.6)
recession['recession 12d 2'] = (recession['12-day std'] >= 2) 
recession['recession 12d 2.5'] = (recession['12-day std'] >= 2.5) 
recession['recession 12d 3'] = (recession['12-day std'] >= 3) 
recession['recession 20d 2'] = (recession['20-day std'] >= 2)
recession['recession 20d 2.5'] = (recession['20-day std'] >= 2.5)
recession['recession 20d 3'] = (recession['20-day std'] >= 3)

for recess_type in recession.select_dtypes(include='bool'):
    plt.vlines(data.index,0,1, colors='#ffffff')
    plt.vlines(data.loc[recession[recess_type]==True].index,0,1, colors='#ff0000')
    plt.title(recess_type)
    plt.savefig(f'{outputpath}/{recess_type} overlay.jpg')