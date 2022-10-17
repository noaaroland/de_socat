import os
import pandas as pd
from plotly.data import iris
import numpy as np
import sdig.erddap.info as info

import pyarrow as pa
import pyarrow.parquet as pq
import pprint

import datashader as ds

# Parquet file properties
# parquet_path = "./data/socat_2022.parquet"
parquet_path = "./data/socat_2022_decimated.parquet"
url = 'https://data.pmel.noaa.gov/socat/erddap/tabledap/socat_v2022_decimated'
# url = 'https://data.pmel.noaa.gov/socat/erddap/tabledap/socat_v2022_fulldata'

info_url = info.get_info_url(url)
info_df = pd.read_csv(info_url)
variables, units, long_names, standard_names, dtypes, na_values = info.get_variables(info_df=info_df)
variables.remove('geospatial_lon_min')
variables.remove('geospatial_lon_max')
variables.remove('geospatial_lat_min')
variables.remove('geospatial_lat_max')
variables.remove('dataset_name')
variables.remove('depth')
if 'socat_doi' in variables:
  variables.remove('socat_doi')
dnld_variables = ','.join(variables)
pp = pprint.PrettyPrinter(indent=4)
def download_socat():
    """
    Download the socat data set found at the URL. Could either be a decimated or full dataset.
    """
    # Make output directory
    if not os.path.isdir("./data"):
        print('Making data dir')
        os.makedirs('./data')

    # download data one year at a time
    started = False
    for year in range(2000, 2022):
        print('downloading year ' + str(year))
        yurl = url + '.csv?' + dnld_variables + '&year=' + str(year)
        try:
            ydf = pd.read_csv(yurl, skiprows=[1], dtype=dtypes, parse_dates=True)
            ydf = ydf.query('-90.0 <= latitude <= 90')
            ydf = ydf.query('-180.0 <= longitude <= 180')
            ydf['lon_meters'], ydf['lat_meters'] = ds.utils.lnglat_to_meters(ydf.longitude,ydf.latitude)
            ydf['text_time'] = ydf['time'].astype(str)
            ydf.loc[:,'text'] = ydf['text_time'] + '<br>expocode=' + ydf['expocode'] + '<br>platform_name=' + ydf['platform_name'] + '<br>platform_type=' + ydf['platform_type'] + '<br>organization=' + ydf['organization']
            ydf.reset_index(drop=True, inplace=True)
            cols = ydf.columns
            table = pa.Table.from_pandas(ydf)
            if not started:
                pqwriter = pq.ParquetWriter(parquet_path, table.schema)
                started = True                
            pqwriter.write_table(table)   
        except Exception as e:
            print(e)
            print('no data for ' + str(year))
    # close the parquet writer
    if pqwriter:
        pqwriter.close() 


if __name__ == '__main__':
    # Check whether to generate a synthetic parquet dataset
    if not os.path.exists(parquet_path):
        print('Starting download...')
        download_socat()
    else:
        print('Output file exists...')
