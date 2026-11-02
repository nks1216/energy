from datetime import timezone, timedelta

import pandas as pd

from _common import INTERIM, numeric, require_unique, save

# Standard LCDv2 bulk files are metric. No unit conversion is performed here.
RENAME = {
    "HourlyDryBulbTemperature": "temperature_c",
    "HourlyDewPointTemperature": "dewpoint_c",
    "HourlyRelativeHumidity": "relative_humidity_pct",
    "HourlyWindSpeed": "wind_speed_ms",
}
CITIES = ["austin", "dallas", "houston", "sanantonio"]


def detect_source_offset():
    """Verify the source clock against UTC times embedded in METAR remarks."""
    offsets = []
    for city in CITIES:
        path = INTERIM / "city" / f"{city}_merge.csv"
        df = pd.read_csv(path, usecols=["DATE", "REPORT_TYPE", "REM"])
        df = df.loc[df["REPORT_TYPE"].astype("string").str.strip().eq("FM-15")].copy()
        df["DATE"] = pd.to_datetime(df["DATE"], errors="raise")
        if df["DATE"].dt.tz is not None:
            raise ValueError("NOAA: Expected the original timezone-naive source clock")
        # Keep a small sample from every year/month, covering winter and summer.
        df = df.sort_values("DATE").groupby(df["DATE"].dt.strftime("%Y-%m"), sort=False).head(40)
        code = df["REM"].astype("string").str.extract(r"\b(\d{2})(\d{2})(\d{2})Z\b")
        valid = code.notna().all(axis=1)
        df = df.loc[valid]
        code = code.loc[valid].astype(int)
        if len(df) < 40 or not df["DATE"].dt.month.isin([1, 2, 12]).any() or not df["DATE"].dt.month.isin([6, 7, 8]).any():
            raise ValueError(f"{city}: Insufficient METAR time evidence. Inspect source DATE/REM before merging.")
        scores = {}
        for offset in [0, 6]:
            utc = df["DATE"] + pd.Timedelta(hours=offset)
            matches = utc.dt.day.eq(code[0]) & utc.dt.hour.eq(code[1]) & utc.dt.minute.eq(code[2])
            # Each sampled month must support the same clock convention.
            scores[offset] = matches.groupby(df["DATE"].dt.strftime("%Y-%m")).mean().min()
        accepted = [offset for offset, score in scores.items() if score >= 0.98]
        if len(accepted) != 1:
            raise ValueError(f"{city}: Source clock could not be verified consistently. Scores: {scores}")
        offsets.append(accepted[0])
        print(f"NOAA {city}: verified DATE + {accepted[0]} hours = UTC; {len(df)} METAR checks")
    if len(set(offsets)) != 1:
        raise ValueError("NOAA: City source clocks differ; rebuild the four-city index in UTC first")
    return offsets[0]


def clean_weather(df, offset):
    df = df.copy()
    dates = pd.to_datetime(df["DATE"], errors="raise")
    if dates.dt.tz is not None or dates.isna().any():
        raise ValueError("NOAA: Invalid source timestamps")
    if not dates.eq(dates.dt.floor("h")).all():
        raise ValueError("NOAA: Expected hourly interval-start labels")
    # A fixed UTC-6 clock never switches to daylight saving time.
    source_tz = timezone(timedelta(hours=-offset))
    df["timestamp_utc"] = dates.dt.tz_localize(source_tz).dt.tz_convert("UTC")
    names = dict(RENAME)
    names.update({f"{old}_n_cities": f"{new}_n_cities" for old, new in RENAME.items()})
    df = df.rename(columns=names)
    values = list(RENAME.values())
    counts = [f"{col}_n_cities" for col in values]
    numeric(df, values + counts)
    for value, count in zip(values, counts):
        if not df[count].isin(range(5)).all():
            raise ValueError(f"NOAA: Invalid city counts in {count}")
        if (df[value].notna() & df[count].ne(4)).any():
            raise ValueError(f"NOAA: {value} should require four valid cities")
    result = df[["timestamp_utc"] + values + counts]
    require_unique(result, ["timestamp_utc"], "NOAA")
    return result


def main():
    offset = detect_source_offset()
    df = pd.read_csv(INTERIM / "texas_merge.csv")
    result = clean_weather(df, offset)
    print("Missing weather values (retained):")
    print(result[list(RENAME.values())].isna().sum().to_string())
    save(result, "noaa_clean.csv")


if __name__ == "__main__":
    main()
