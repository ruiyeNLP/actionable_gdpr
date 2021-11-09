This sample will make a request to Alexa Top Sites using the API user credentials and API plan key.

Tested with Python v3.8.2

1. Subscribe to Alexa Top Sites in AWS Marketplace  [https://aws.amazon.com/marketplace/pp/prodview-xv7kf2ukjktzc?ref_=srh_res_product_title](https://aws.amazon.com/marketplace/pp/prodview-xv7kf2ukjktzc?ref_=srh_res_product_title)
2. Retrieve the API Key assigned to your account in the Alexa API Portal ([https://ats.alexa.com/](https://ats.alexa.com/)).
3. Install requirements `pip install -r requirements.txt`
4. Run:

`python topsites.py --key=<API_KEY> --action=TopSites --country=GB --options="&Output=json&ResponseGroup=Country"`

`python [topsites.py] --key=--key=<API_KEY> --action=TopSites --country=DE --options="&Output=json&ResponseGroup=Country"`

`python [topsites.py] --key=--key=<API_KEY> --action=TopSites --country=FR --options="&Output=json&ResponseGroup=Country"`

5. post-processing 

convert json to csv

`combine './topsites'+countrycode+epoch+'.json' into countrycode.json`

`cat ./topsites/*GB*.csv >./topsites/GB.csv`

`cat ./topsites/*DE*.csv >./topsites/DE.csv`

`cat ./topsites/*FR*.csv >./topsites/FR.csv`

6. result 

top 1000 from UK: ./topsites/GB.csv

top 500 from Germany: ./topsites/DE.csv

top 500 from France: ./topsites/FR.csv
