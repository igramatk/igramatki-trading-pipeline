# -*- coding: utf-8 -*-
"""
Created on Fri Nov 26 21:46:48 2021

@author: Iulian
"""
recession = pd.DataFrame(fulldata_returns['^GSPC'])
for k in [5,8,12,20,40,80]:
    recession[f'{k}-day mean'] = recession['^GSPC'].rolling(k).mean()
    recession[f'{k}-day std'] = recession['^GSPC'].rolling(k).std()  

for k in [5,8,12,20,40,80]:
    plt.figure(dpi=300)
    plt.plot(recession[f'{k}-day mean'], label=f'{k}-day mean', linewidth=0.5)
    plt.plot(recession[f'{k}-day std'], label=f'{k}-day std', linewidth=0.5)
    plt.xticks(rotation=25)
    plt.legend(fontsize='x-small')
    plt.savefig(f'E:/Tech/Python/Charts/recession detect {k}-day.jpg')

