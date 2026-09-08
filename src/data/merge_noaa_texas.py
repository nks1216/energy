import pandas as pd

input_files = {
    "austin": "data/clean/austin_2021_2025_clean.csv",
    "dallas": "data/clean/dallas_2021_2025_clean.csv",
    "houston": "data/clean/houston_2021_2025_clean.csv",
    "sanantonio": "data/clean/sanantonio_2021_2025_clean.csv",
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

# Compute statewide averages across the four cities
statewide = (
    all_cities_resampled
    .groupby("DATE")
    .agg({
        "HourlyDryBulbTemperature": "mean",
        "HourlyDewPointTemperature": "mean",
        "HourlyRelativeHumidity": "mean",
        "HourlyWindSpeed": "mean",
        "HourlyWindDirection": "mean",
        "HourlyPrecipitation": "mean",
        "rain_flag": "max", # If any city reports precipitation, statewide = 1
    })
    .reset_index()
)

# rounding for cleaner output
statewide = statewide.round({
    "HourlyDryBulbTemperature": 2,
    "HourlyDewPointTemperature": 2,
    "HourlyRelativeHumidity": 2,
    "HourlyWindSpeed": 2,
    "HourlyWindDirection": 1,
    "HourlyPrecipitation": 3,
    "rain_flag": 0
})

output_path = "data/clean/texas_merge.csv"
statewide.to_csv(output_path, index=False)

print(f"Saved statewide weather file: {output_path}")