# -*- coding: utf-8 -*-
"""
Created on Mon Nov 22 21:01:48 2021

@author: Iulian
"""
import pandas as pd
import numpy as np 
from datetime import datetime
def loadsp(fpath):
    df = pd.read_csv(fpath, index_col=0)
    df.index = [datetime.strptime(u, "%Y-%m-%d").date() for u in df.index]
    df = df.drop(df.index[np.isnan(df).all(axis=1)])
    return df

