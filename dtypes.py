import pandas as pd
import sdig.erddap.info as info

url = 'https://data.pmel.noaa.gov/socat/erddap/tabledap/socat_v2022_decimated'
info_url = info.get_info_url(url)
info_df = pd.read_csv(info_url)
variables, units, long_names, standard_names, dtypes = info.get_variables(info_df=info_df)
print(dtypes)