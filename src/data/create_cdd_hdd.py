import pandas as pd

# Load data
df = pd.read_csv("data/final/final_data.csv")

# Base temperature (18°C)
base_temp = 18

# Cooling Degree Days (hours)
df["CDD"] = (df["HourlyDryBulbTemperature"] - base_temp).clip(lower=0)

# Heating Degree Days (hours)
df["HDD"] = (base_temp - df["HourlyDryBulbTemperature"]).clip(lower=0)

# Save new file
df.to_csv(
    "data/final/final_data_cdd_hdd.csv",
    index=False
)

print("Saved: final_data_cdd_hdd.csv")

print("\nCDD Summary")
print(df["CDD"].describe())

print("\nHDD Summary")
print(df["HDD"].describe())

corr = df[
    [
        "ERCOT",
        "price_rt_hubavg",
        "CDD",
        "HDD"
    ]
].corr()

print(corr.round(3))