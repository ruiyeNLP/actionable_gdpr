#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  6 14:12:38 2020

@author: yerui
"""

#
# Copyright 2019 Amazon.com, Inc. and its affiliates. All Rights Reserved.
#
# Licensed under the MIT License. See the LICENSE accompanying this file
# for the specific language governing permissions and limitations under
# the License.
#
#------------------------------------------------------------------------
#         Python Code Sample for Alexa Top Sites Service          -
#------------------------------------------------------------------------
#
# This sample will make a request to Alexa Top Sites in
# AWS Marketplace using the API user credentials and API plan key. This
# sample demonstrates how to make a SigV4 signed request and refresh
# crdentials from the Cognito pool.
#

import sys, os, base64, hashlib, hmac
import logging, getopt
import boto3
import getpass
#from botocore.vendored import requests
import requests
from datetime import datetime
import time
from configparser import ConfigParser # pip install configparser
from future.standard_library import install_aliases
install_aliases()
from urllib.parse import parse_qs, quote_plus
import json

# ************* REQUEST VALUES *************
host = 'ats.api.alexa.com'
endpoint = 'https://' + host
method = 'GET'
logging.basicConfig()
log = logging.getLogger( "ats" )
content_type = 'application/xml'
local_tz = "America/Los_Angeles"

###############################################################################
# usage                                                                       #
###############################################################################
def usage( ):
    sys.stderr.write ( """
Usage: topsites.py [options]
  Make a signed request to Alexa Top Sites API service
  Options:
     -a, --action            Service Action
     -k, --key               API Key
     -c, --country           2-letter Country Code (ie. US, CN, BR)
     -o, --options           Service Options
     -?, --help       Print this help message and exit.
  Examples:
     TopSites by country: topsites.py -k 98hu7.... --action TopSites --country=US --options "&Count=100&Output=json"
""" )

###############################################################################
# parse_options                                                               #
###############################################################################
def parse_options( argv, epoch, step):
    """Parse command line options."""

    opts = {}

    urlargs = {}

    try:
        user_opts, user_args = getopt.getopt( \
            argv, \
            'k:a:c:o:?', \
            [ 'key=', 'action=', 'country=', 'options=', 'help=' ] )
    except Exception as e:
        print('Command parse error:', e)
        log.error( "Unable to parse command line" )
        return None

    if ( '-?', '' ) in user_opts or ( '--help', '' ) in user_opts:
        opts['help'] = True
        return opts

    #
    # Convert command line options to dictionary elements
    #
    for opt in user_opts:
        if  opt[0] == '-k' or opt[0] == '--key':
            opts['key'] = 'BGPZ81d00x6KE6CyHnNRS16BUAqi0jbta0rgqbqd'
        elif opt[0] == '-a' or opt[0] == '--action':
            opts['action'] = opt[1]
        elif opt[0] == '-c' or opt[0] == '--country':
#            opts['country'] = 'DE'
            opts['country'] = opt[1]
 #          opts['country'] = 'DE,FI'
        elif opt[0] == '-o' or opt[0] == '--options':
            opts['options'] = '&Count='+step+'&Start='+str((int(epoch)-1)*int(step)+1)+'&Output=json&ResponseGroup=Country'
        elif opt[0] == '-a' or opt[0] == '--action':
            opts['action'] = opt[1]
        elif opt[0] == '-v' or opt[0] == '--verbose':
            log.verbose()

    if 'key' not in opts or \
       'action' not in opts or \
       'country' not in opts:
        return None

    #
    # Return a dictionary of settings
    #
    success = True
    return opts

###############################################################################
# sortQueryString                                                             #
###############################################################################
def sortQueryString(queryString):
    queryTuples = parse_qs(queryString)
    sortedQueryString = ""
    sep=""
    for key in sorted(queryTuples.keys()):
        sortedQueryString = sortedQueryString + sep + key + "=" + quote_plus(queryTuples[key][0])
        sep="&"
    return sortedQueryString

###############################################################################
# main                                                                        #
###############################################################################
def makeQuery(epoch,  step):

    opts = parse_options( sys.argv[1:], epoch, step)

    if not opts:
        usage( )
        sys.exit( -1 )

    if 'help' in opts:
        usage( )
        sys.exit( 0 )

    canonical_uri = '/api'

    canonical_querystring = 'Action=' + opts['action']
    canonical_querystring += "&" + 'CountryCode=' + opts['country']
    canonical_querystring += "&" + 'ResponseGroup=Country'
    if 'options' in opts:
        canonical_querystring += "&" +  opts[ 'options']
    canonical_querystring = sortQueryString(canonical_querystring)

    headers = {'Accept':'application/xml',
               'Content-Type': content_type,
               'x-api-key': opts['key']
              }

    # ************* SEND THE REQUEST *************
    request_url = endpoint + canonical_uri + "?" + canonical_querystring

    print('\nBEGIN REQUEST++++++++++++++++++++++++++++++++++++')
    print('Request URL = ' + request_url)
    r = requests.get(request_url, headers=headers)

    print('\nRESPONSE++++++++++++++++++++++++++++++++++++')
    print('Response code: %d\n' % r.status_code)
#    print(r.text)
#    data = r.json()
#    filename = './combine_'+countryCode+'/topsites_'+countryCode+'_'+epoch+'.json'
    filename = './topsites/'+'topsites'+opts['country']+epoch+'.json'

    with open(filename, 'w') as outfile: #change 1
        json.dump(r.json(), outfile)

if __name__ == "__main__":
    #countryCode = 'BE'
    epoches = 5
    step = 100
#    for i in range(1,5+1):
    for i in range(1,epoches+1):
        makeQuery(str(i), str(step))
    