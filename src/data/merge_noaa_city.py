import pandas as pd 
import glob
import os

station_map = {    
    "USW00003927": "dallas",
    "USW00012921": "sanantonio",
    "USW00012960": "houston",
    "USW00013904": "austin"
    }

keep_cols = [
    "DATE",
    "HourlyDryBulbTemperature",
    "HourlyDewPointTemperature",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "HourlyWindDirection",
    "HourlyPrecipitation",
    "HourlyPresentWeatherType"
]

RAW_DIR ='data/raw/noaa'
INTERIM_DIR = 'data/interim'
os.makedirs(INTERIM_DIR, exist_ok=True)

num_cols = [
    "HourlyDryBulbTemperature",
    "HourlyDewPointTemperature",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "HourlyWindDirection",
    "HourlyPrecipitation"
]

for station, city in station_map.items():
    print(f"Processing{city} ({station}) ...")

    files = sorted(glob.glob(f"{RAW_DIR}/LCD_{station}_*.csv"))
    dfs = []

    for f in files:
        print(f" - Loading {f}")
        df = pd.read_csv(f)

        df = df[keep_cols]
        df["DATE"] = pd.to_datetime(df["DATE"])

        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.sort_values("DATE").drop_duplicates("DATE", keep="last")
        dfs.append(df)

    merged = pd.concat(dfs, ignore_index=True)

    merged["HourlyDryBulbTemperature"] = merged["HourlyDryBulbTemperature"].interpolate()
    merged["HourlyDewPointTemperature"] = merged["HourlyDewPointTemperature"].interpolate()
    merged["HourlyRelativeHumidity"] = merged["HourlyRelativeHumidity"].interpolate()
    merged["HourlyWindSpeed"] = merged["HourlyWindSpeed"].interpolate()
    merged["HourlyWindDirection"] = merged["HourlyWindDirection"].interpolate()
    merged["HourlyPrecipitation"] = merged["HourlyPrecipitation"].fillna(0)
    merged["HourlyPresentWeatherType"] = merged["HourlyPresentWeatherType"].fillna("None")

    out_path = f"{INTERIM_DIR}/{city}_merge.csv"
    merged.to_csv(out_path, index=False)

    print(f"  → Saved: {out_path}")

print("All cities processed successfully.")