import pandas as pd
from pathlib import Path

cities = ["dallas", "houston", "sanantonio", "austin"]
dates = ["2021-11-07", "2022-11-06", "2023-11-05"]

for city in cities:
    path = Path(f"data/interim/city/{city}_merge.csv")
    df = pd.read_csv(path)

    df["utc_timestamp"] = pd.to_datetime(
        df["utc_timestamp"], utc=True
    )

    df["utc_hour"] = df["utc_timestamp"].dt.floor("h")

    df = df[df["REPORT_TYPE"].astype(str).str.strip() == "FM-15"]

    print(f"\n========== {city.upper()} ==========")

    for date in dates:
        start = pd.Timestamp(date, tz="UTC") + pd.Timedelta(hours=6)
        end = start + pd.Timedelta(hours=2)

        result = df[
            df["utc_timestamp"].between(start, end, inclusive="left")
        ][["DATE", "utc_timestamp", "HourlyDryBulbTemperature"]]

        print(f"\n{date}")
        print(result.to_string(index=False))