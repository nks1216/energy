import pandas as pd 
import glob
import os

files = sorted(glob.glob("data/raw/ercot/*.xlsx"))
dfs = []

for f in files:
    print("Loading:", f)
    df = pd.read_excel(f)

    # 24:00 → next day 00:00 transformation
    df["Hour Ending"] = df["Hour Ending"].astype(str)
    df["Hour Ending"] = df["Hour Ending"].str.replace(" 24:00", " 00:00", regex=False)
    df["Hour Ending"] = df["Hour Ending"].str.replace(" DST", "", regex=False)

    df["Hour Ending"] = pd.to_datetime(df["Hour Ending"], format="mixed")
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

merged["hour"] = merged["Hour Ending"].dt.hour
merged["day"] = merged["Hour Ending"].dt.day
merged["dayofweek"] = merged["Hour Ending"].dt.dayofweek
merged["month"] = merged["Hour Ending"].dt.month
merged["year"] = merged["Hour Ending"].dt.year

os.makedirs("data/interim", exist_ok=True)
merged.to_csv("data/interim/ercot_merge.csv", index=False)
print("Done! Final shape:", merged.shape)