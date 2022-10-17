import pandas as pd

# Load Parquet file as vaex DataFrame
parquet_path = "./data/socat_2022_decimated.parquet"
vdf = pd.read_parquet(parquet_path)
lon_min= -109.86971880899262 
lon_max= 152.80996327074104 
lat_min= -77.82317492531277 
lat_max= 70.3380427998548
deci_df = vdf.loc[(vdf['latitude']<=lat_max)  & (vdf['latitude']>=lat_min) & (vdf['longitude']>=lon_min) & (vdf['longitude']>=lon_min) & (vdf['longitude']<=lon_max)] 
print(deci_df)