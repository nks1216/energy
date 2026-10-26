import pandas as pd
import numpy as np

input_files = {
    "austin": "data/interim/austin_merge.csv",
    "dallas": "data/interim/dallas_merge.csv",
    "houston": "data/interim/houston_merge.csv",
    "sanantonio": "data/interim/sanantonio_merge.csv",
}

dfs = []

for city, path in input_files.items():
    print(f"Loading {city}: {path}")
    df = pd.read_csv(path)

    # Convert DATE column to datetime
    df["DATE"] = pd.to_datetime(df["DATE"])

    # Add city label for later grouping
    df["city"] = city

    dfs.append(df)

all_cities = pd.concat(dfs, ignore_index=True)

# Convert NOAA weather-type strings into a binary precipitation flag
def rain_flag(x):
    if pd.isna(x):
        return 0

    s = str(x).lower()

    # Weather event keywords indicating precipitation or related conditions
    rain_keywords = ["ra", "dz", "sn", "ts", "fg", "br", "up"]

    # Return 1 if any keyword appears in the string
    return 1 if any(k in s for k in rain_keywords) else 0

all_cities["rain_flag"] = all_cities["HourlyPresentWeatherType"].apply(rain_flag)
all_cities = all_cities.set_index("DATE")

# numeric columns only (exclude rain_flag)
numeric_cols = [
    "HourlyDryBulbTemperature",
    "HourlyDewPointTemperature",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "HourlyWindDirection",
    "HourlyPrecipitation",
]

# resample numeric columns to hourly intervals (fixes SPECI irregular timestamps)
resampled_numeric = (
    all_cities
    .groupby("city")[numeric_cols]
    .resample("1h")
    .mean()
)

# resample rain_flag separately using max
resampled_rain = (
    all_cities
    .groupby("city")["rain_flag"]
    .resample("1h")
    .max()
)

# merge back
all_cities_resampled = pd.concat([resampled_numeric, resampled_rain], axis=1).reset_index()

# Define population weight dictionary for the 4 major cities
population_weights = {
    "dallas": 0.3891,       # 0.389066
    "houston": 0.3621,      # 0.362130
    "sanantonio": 0.1296,   # 0.129629
    "austin": 0.1192,       # 0.119176
}

# Map the weight column to the DataFrame
all_cities_resampled["weight"] = all_cities_resampled["city"].map(population_weights)

# Define function to compute weighted average grouped by DATE
def weighted_mean(group):
    w = group["weight"]
    res = {}
    for col in numeric_cols:
        # Compute weighted average (excluding NaN values)
        valid_idx = group[col].notna() & w.notna()
        if valid_idx.sum() > 0:
            res[col] = np.average(group.loc[valid_idx, col], weights=w[valid_idx])
        else:
            res[col] = np.nan
            
    # Compute population-weighted average for rain_flag (0 to 1 proportion)
    valid_rain_idx = group["rain_flag"].notna() & w.notna()
    if valid_rain_idx.sum() > 0:
        res["rain_flag"] = np.average(group.loc[valid_rain_idx, "rain_flag"], weights=w[valid_rain_idx])
    else:
        res["rain_flag"] = 0.0
        
    return pd.Series(res)

print("Computing population-weighted statewide weather averages...")
statewide = (
    all_cities_resampled.groupby("DATE").apply(weighted_mean).reset_index()
)

# rounding for cleaner output (rain_flag is now a weighted proportion, so round to 3 decimals)
statewide = statewide.round({
    "HourlyDryBulbTemperature": 2,
    "HourlyDewPointTemperature": 2,
    "HourlyRelativeHumidity": 2,
    "HourlyWindSpeed": 2,
    "HourlyWindDirection": 1,
    "HourlyPrecipitation": 3,
    "rain_flag": 3
})

output_path = "data/interim/texas_merge.csv"
statewide.to_csv(output_path, index=False)

print(f"Saved statewide weather file: {output_path}")