import pandas as pd

df = pd.read_csv("data/final/final_data.csv")

df["temp_bin"] = (
    df["HourlyDryBulbTemperature"]
    .round(0)
)

count_by_temp = (
    df.groupby("temp_bin")
      .size()
)

print(count_by_temp)
