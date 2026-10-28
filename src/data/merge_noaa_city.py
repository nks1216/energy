from pathlib import Path
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

    # Remarks are useful for checking observation times, but may be absent
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
        print(f"Processing {city}...")
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
            merged.sort_values("DATE", kind="stable")
            .reset_index(drop=True)
        )

        # Preserve different reports sharing the same timestamp
        same_time = merged["DATE"].duplicated(
            keep=False
        ).sum()

        print(f"  Identical rows removed: {removed:,}")
        print(f"  Rows sharing a timestamp: {same_time:,}")

        out_path = INTERIM_DIR / f"{city}_merge.csv"

        merged.to_csv(
            out_path,
            index=False,
            encoding="utf-8-sig",
        )

        print(f"  Saved: {out_path} ({len(merged):,} rows)")
        print("  Missing numeric values:")
        print(merged[NUM_COLS].isna().sum().to_string())

    print("All cities processed successfully.")


if __name__ == "__main__":
    main()