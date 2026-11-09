from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "clean" / "ercot_price_noaa.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "final" / "final_data_cdd_hdd.csv"

# Load data (output of merge_all.py)
df = pd.read_csv(INPUT_PATH)
print("Loaded:", INPUT_PATH, df.shape)

# Base temperature (18°C)
base_temp = 18

# Cooling degree-hours
df["CDD"] = (df["HourlyDryBulbTemperature"] - base_temp).clip(lower=0)

# Heating degree-hours
df["HDD"] = (base_temp - df["HourlyDryBulbTemperature"]).clip(lower=0)

# Save new file
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False)

print("Saved:", OUTPUT_PATH, df.shape)

print("\nCDD Summary")
print(df["CDD"].describe())

print("\nHDD Summary")
print(df["HDD"].describe())

corr = df[["ERCOT", "price_rt_hubavg", "CDD", "HDD"]].corr()
print(corr.round(3))