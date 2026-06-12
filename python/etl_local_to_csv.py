import requests
import pandas as pd
from google.colab import userdata

# get api key
# note: if running this script in VS Code locally, use python-dotenv instead
eia_key = userdata.get('EIA_KEY')

# 1. extract data from APIs
weather_url = "https://archive-api.open-meteo.com/v1/archive?latitude=29.76&longitude=-95.36&start_date=2024-01-01&end_date=2026-06-08&hourly=temperature_2m"
df_weather = pd.DataFrame(requests.get(weather_url).json()['hourly'])

demand_url = f"https://api.eia.gov/v2/electricity/rto/region-data/data/?frequency=hourly&data[0]=value&facets[respondent][]=ERCO&start=2024-01-01T00&end=2026-06-10T00&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000&api_key={eia_key}"
df_demand = pd.DataFrame(requests.get(demand_url).json()['response']['data'])

gen_url = f"https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/?frequency=hourly&data[0]=value&facets[respondent][]=ERCO&start=2024-01-01T00&end=2026-06-10T00&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000&api_key={eia_key}"
df_gen = pd.DataFrame(requests.get(gen_url).json()['response']['data'])

# 2. transform & merge
# fix datetime columns
df_weather = df_weather.rename(columns={"time": "period"})
df_weather['period'] = pd.to_datetime(df_weather['period'])
df_demand['period'] = pd.to_datetime(df_demand['period'])
df_gen['period'] = pd.to_datetime(df_gen['period'])

# join tables (inner to drop missing hours)
df_merged = pd.merge(df_demand, df_weather, on='period', how='inner')
df_merged = pd.merge(df_merged, df_gen, on='period', how='inner')

# 3. cleanup
drop_cols = ['respondent_x', 'respondent-name_x', 'type', 'value-units_x', 'respondent_y', 'respondent-name_y', 'value-units_y']
df_merged = df_merged.drop(columns=drop_cols, errors='ignore')

df_merged = df_merged.rename(columns={"value_x": "demand_mwh", "value_y": "generation_mwh", "type-name_x": "demand_type"})

df_merged['demand_mwh'] = pd.to_numeric(df_merged['demand_mwh'], errors='coerce')
df_merged['generation_mwh'] = pd.to_numeric(df_merged['generation_mwh'], errors='coerce')

# 4. export to csv
df_merged.to_csv('texas_grid_data.csv', index=False)
print("Data saved to texas_grid_data.csv")