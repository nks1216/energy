import pandas as pd

m = pd.read_csv("data/clean/ercot_price_noaa.csv")
m["Hour Ending"] = pd.to_datetime(m["Hour Ending"])
pairs = m[m["Hour Ending"].duplicated(keep=False)]
print(pairs[["Hour Ending", "has_dst_marker",
             "HourlyDryBulbTemperature_n_cities"]].to_string(index=False))

d = pd.read_csv("data/final/final_data_cdd_hdd.csv")
d["date"] = pd.to_datetime(d["date"])

miss = d[d["HourlyDryBulbTemperature"].isna()
         | d["HourlyRelativeHumidity"].isna()
         | d["HourlyWindSpeed"].isna()]
print("missing hours:", len(miss))
print(miss.groupby([miss["date"].dt.year, miss["date"].dt.month])
          .size().sort_values(ascending=False).head(10))