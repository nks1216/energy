from pathlib import Path
import pandas as pd


# Script location: energy/src/data/merge_noaa_texas.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CITY_DIR = PROJECT_ROOT / "data" / "interim" / "city"
OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "texas_merge.csv"

# These weights describe the four-city index, not all of Texas
POPULATION_WEIGHTS = {
    "dallas": 0.3891,
    "houston": 0.3621,
    "sanantonio": 0.1296,
    "austin": 0.1192,
}

NUMERIC_COLS = [
    "HourlyDryBulbTemperature",
    "HourlyDewPointTemperature",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
]

# Preserve the source clock for now; this is not a UTC index
HOURS = pd.date_range(
    "2021-01-01",
    "2025-12-31 23:00",
    freq="h",
)


def read_hourly(path):
    df = pd.read_csv(
        path,
        usecols=["DATE", "REPORT_TYPE"] + NUMERIC_COLS,
    )

    df["DATE"] = pd.to_datetime(df["DATE"], errors="raise")

    if df["DATE"].isna().any():
        raise ValueError(f"{path.name}: Missing timestamps")

    if df["DATE"].dt.tz is not None:
        raise ValueError(
            f"{path.name}: Expected timestamps "
            "in the original source clock"
        )

    # Use routine METAR observations for consistent hourly sampling
    # Other report types remain available in the city files
    report_type = df["REPORT_TYPE"].astype("string").str.strip()

    df = df.loc[
        report_type.eq("FM-15").fillna(False)
    ].copy()

    if df.empty:
        raise ValueError(
            f"{path.name}: No FM-15 observations found"
        )

    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="raise")

    # Average multiple routine reports at the same timestamp, if present
    observations = (
        df.groupby("DATE")[NUMERIC_COLS]
        .mean()
        .sort_index()
    )

    # A timestamp such as 00:53 belongs to [00:00, 01:00)
    hourly = observations.resample(
        "h",
        closed="left",
        label="left",
    ).mean()

    # Include entirely unobserved hours without filling their values
    return hourly.reindex(HOURS)


def combine_cities(city_hourly):
    if abs(sum(POPULATION_WEIGHTS.values()) - 1.0) > 1e-8:
        raise ValueError("Population weights must sum to one")

    result = pd.DataFrame(index=HOURS)
    result.index.name = "DATE"

    for col in NUMERIC_COLS:
        values = pd.DataFrame({
            city: city_hourly[city][col]
            for city in POPULATION_WEIGHTS
        })

        weights = pd.Series(POPULATION_WEIGHTS)

        # Require all four cities; do not redistribute missing-city weights
        result[col] = (
            values.mul(weights, axis="columns")
            .sum(axis=1, min_count=4)
        )

        # Record the number of cities with valid measurements
        result[f"{col}_n_cities"] = values.notna().sum(axis=1)

    return result


def main():
    city_hourly = {}

    for city in POPULATION_WEIGHTS:
        path = CITY_DIR / f"{city}_merge.csv"

        print(f"Loading: {path}", flush=True)

        city_hourly[city] = read_hourly(path)

        print("Missing hourly values:")
        print(
            city_hourly[city].isna().sum().to_string()
        )

    result = combine_cities(city_hourly)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    result.to_csv(
        OUTPUT_PATH,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S",
        float_format="%.4f",
    )

    print(
        f"\nSaved: {OUTPUT_PATH} "
        f"({len(result):,} rows)"
    )
    print("Missing values in the four-city index:")
    print(
        result[NUMERIC_COLS].isna().sum().to_string()
    )


if __name__ == "__main__":
    main()