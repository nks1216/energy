from pathlib import Path
import re
import pandas as pd


# Script location: energy/src/data/merge_noaa_city.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "noaa"
INTERIM_DIR = PROJECT_ROOT / "data" / "interim" / "city"

STATION_MAP = {
    "USW00003927": "dallas",
    "USW00012921": "sanantonio",
    "USW00012960": "houston",
    "USW00013904": "austin",
}

WEATHER_COLS = [
    "HourlyDryBulbTemperature",
    "HourlyDewPointTemperature",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "HourlyWindDirection",
    "HourlyPrecipitation",
    "HourlyPresentWeatherType",
]

NUM_COLS = WEATHER_COLS[:-1]
KEEP_COLS = ["DATE", "REPORT_TYPE", "REM"] + WEATHER_COLS

# METAR observation time format: DDHHMMZ
METAR_TIME_PATTERN = re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})Z")


def extract_utc_timestamp(date_value, remarks):
    """
    Extract the METAR UTC timestamp from REM.

    DATE is retained as the original NOAA local timestamp.
    The UTC timestamp is reconstructed using the METAR DDHHMMZ
    information and the year/month inferred from DATE.

    Returns NaT if no reliable candidate can be identified.
    """

    if pd.isna(remarks) or pd.isna(date_value):
        return pd.NaT

    matches = METAR_TIME_PATTERN.findall(str(remarks))

    if not matches:
        return pd.NaT

    local_date = pd.Timestamp(date_value)
    candidates = []

    # Check the previous, current, and next month.
    # This handles observations close to month boundaries.
    for month_offset in [-1, 0, 1]:
        month_date = local_date + pd.DateOffset(months=month_offset)

        for day_str, hour_str, minute_str in matches:
            day = int(day_str)
            hour = int(hour_str)
            minute = int(minute_str)

            try:
                candidate = pd.Timestamp(
                    year=month_date.year,
                    month=month_date.month,
                    day=day,
                    hour=hour,
                    minute=minute,
                )
            except ValueError:
                continue

            # Texas local time is normally 5 or 6 hours
            # behind UTC. Allow a wider 4–8 hour window.
            difference = candidate - local_date

            if pd.Timedelta(hours=4) <= difference <= pd.Timedelta(hours=8):
                candidates.append(candidate)

    if not candidates:
        return pd.NaT

    # Choose the candidate closest to the expected UTC offset.
    best_candidate = min(
        candidates,
        key=lambda x: abs(
            (x - local_date) - pd.Timedelta(hours=5.5)
        ),
    )

    return best_candidate.tz_localize("UTC")


def clean_file(path):
    # Read selected columns and keep precipitation markers as text
    df = pd.read_csv(
        path,
        usecols=lambda col: col in KEEP_COLS,
        dtype={"HourlyPrecipitation": "string"},
        low_memory=False,
    )

    required = ["DATE", "REPORT_TYPE"] + WEATHER_COLS
    missing = set(required) - set(df.columns)

    if missing:
        raise ValueError(
            f"{path.name}: Missing required columns: {missing}"
        )

    # Remarks are useful for extracting observation times
    if "REM" not in df.columns:
        df["REM"] = pd.NA

    df = df[KEEP_COLS].copy()

    df["REPORT_TYPE"] = (
        df["REPORT_TYPE"].astype("string").str.strip()
    )

    # Exclude daily and monthly summaries
    df = df.loc[
        ~df["REPORT_TYPE"].isin(["SOD", "SOM"])
    ].copy()

    df["DATE"] = pd.to_datetime(df["DATE"], errors="raise")

    if df["DATE"].isna().any():
        raise ValueError(
            f"{path.name}: Missing observation timestamps"
        )

    # Preserve trace precipitation and distinguish it from missing values
    df["precipitation_raw"] = df["HourlyPrecipitation"].copy()

    df["precipitation_trace"] = (
        df["precipitation_raw"]
        .str.strip()
        .eq("T")
        .fillna(False)
    )

    # Unparseable numeric values remain missing
    # Do not fill missing measurements or interpolate
    for col in NUM_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Retain wind direction for reference, excluding invalid angular values
    df["HourlyWindDirection"] = df["HourlyWindDirection"].where(
        df["HourlyWindDirection"].between(0, 360)
    )

    # Extract UTC timestamp from METAR remarks
    df["utc_timestamp"] = [
        extract_utc_timestamp(date_value, remarks)
        for date_value, remarks in zip(df["DATE"], df["REM"])
    ]

    return df


def main():
    # Check all input paths before writing any output
    city_files = {}

    for station, city in STATION_MAP.items():
        files = sorted(
            RAW_DIR.glob(f"LCD_{station}_*.csv")
        )

        if not files:
            raise FileNotFoundError(
                f"No input files found for {city} in {RAW_DIR}"
            )

        city_files[city] = files

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)

    for city, files in city_files.items():
        print(f"\nProcessing {city}...")
        frames = []

        for path in files:
            print(f"  Loading: {path.name}", flush=True)
            frames.append(clean_file(path))

        merged = pd.concat(frames, ignore_index=True)

        if merged.empty:
            raise ValueError(
                f"No observation records remain for {city}"
            )

        # Remove only rows identical across all retained fields
        before = len(merged)
        merged = merged.drop_duplicates()
        removed = before - len(merged)

        merged = (
            merged.sort_values(
                ["DATE", "utc_timestamp"],
                kind="stable",
                na_position="last",
            )
            .reset_index(drop=True)
        )

        # Diagnostics
        same_time = merged["DATE"].duplicated(
            keep=False
        ).sum()

        utc_success = merged["utc_timestamp"].notna().sum()
        utc_missing = merged["utc_timestamp"].isna().sum()

        print(f"  Identical rows removed: {removed:,}")
        print(f"  Rows sharing a local timestamp: {same_time:,}")
        print(f"  UTC timestamps extracted: {utc_success:,}")
        print(f"  UTC timestamps missing: {utc_missing:,}")

        # Check whether different UTC timestamps are preserved
        duplicated_local = merged[
            merged["DATE"].duplicated(keep=False)
        ]

        if not duplicated_local.empty:
            print("  Sample duplicated local timestamps:")
            print(
                duplicated_local[
                    ["DATE", "utc_timestamp",
                     "HourlyDryBulbTemperature"]
                ].head(10).to_string(index=False)
            )

        out_path = INTERIM_DIR / f"{city}_merge.csv"

        merged.to_csv(
            out_path,
            index=False,
            encoding="utf-8-sig",
        )

        print(f"  Saved: {out_path} ({len(merged):,} rows)")
        print("  Missing numeric values:")
        print(merged[NUM_COLS].isna().sum().to_string())

    print("\nAll cities processed successfully.")


if __name__ == "__main__":
    main()