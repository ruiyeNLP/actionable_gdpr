#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 09:24:33 2020

@author: yerui
"""

import pandas as pd
import json 
import csv

countryCode = 'GB'
epochs = 10

for i in range(1,epochs+1):

    filename_filter = './topsites/'+'topsites'+countryCode.lower()+'_filter_'+str(i)+'.json'
    df = pd.read_json (filename_filter) #change 4
    filename_output = './topsites/'+'topsites'+countryCode+str(i)+'.csv'
    export_csv = df.to_csv (filename_output, index = None, header=True)

