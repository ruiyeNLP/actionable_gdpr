#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 09:23:16 2020

@author: yerui
"""
import json

countryCode = 'GB'
epochs = 10

for i in range(1,epochs+1):
    filename_json = './topsites/'+'topsites'+countryCode+str(i)+'.json'
    #load json file
    with open(filename_json,'r') as f_ojb:
        json_data = json.load(f_ojb,)    
    #pock the targeted layer    
    json_fkey = json_data['Ats']['Results']['Result']['Alexa']['TopSites']['Country']['Sites']['Site']['DataUrl']
    filename_filter = './topsites/'+'topsites'+countryCode.lower()+'_filter_'+str(i)+'.json'
    with open(filename_filter, 'w') as outfile: #change 3
        json.dump(json_fkey, outfile)