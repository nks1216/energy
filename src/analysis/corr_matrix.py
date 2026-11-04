import pandas as pd

df = pd.read_csv("data/final/final_data.csv")

cols = [
    "ERCOT",
    "price_rt_hubavg",
    "HourlyDryBulbTemperature",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
]

corr = df[cols].corr()

print(corr.round(3))