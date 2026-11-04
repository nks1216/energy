from pathlib import Path
import pandas as pd

# ============================================================
# Paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CITY_DIR = PROJECT_ROOT / "data" / "interim" / "city"
OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "utc_noaa.csv"


# ============================================================
# Settings
# ============================================================

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

# UTC hourly timestamps for the ERCOT study period
UTC_HOURS = pd.date_range(
    start="2021-01-01 06:00:00",
    end="2026-01-01 05:00:00",
    freq="h",
    tz="UTC",
)


# ============================================================
# Read and aggregate each city using UTC
# ============================================================

def read_hourly_utc(path):

    df = pd.read_csv(
        path,
        usecols=["utc_timestamp", "REPORT_TYPE"] + NUMERIC_COLS,
    )

    # Parse UTC timestamps
    df["utc_timestamp"] = pd.to_datetime(
        df["utc_timestamp"],
        errors="coerce",
        utc=True,
    )

    # Keep FM-15 (METAR) observations only
    report_type = df["REPORT_TYPE"].astype("string").str.strip()

    df = df.loc[
        report_type.eq("FM-15").fillna(False)
    ].copy()

    # Exclude observations without a valid UTC timestamp
    missing_utc = df["utc_timestamp"].isna().sum()

    df = df.dropna(subset=["utc_timestamp"]).copy()

    # Convert weather variables to numeric
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Assign each observation to its UTC hourly bin
    df["utc_hour"] = df["utc_timestamp"].dt.floor("h")

    # Average observations within each UTC hour
    hourly = (
        df.groupby("utc_hour")[NUMERIC_COLS]
        .mean()
        .sort_index()
    )

    # Reindex to the common UTC hourly timeline
    hourly = hourly.reindex(UTC_HOURS)

    print(f"File: {path.name}")
    print(f"FM-15 observations: {len(df):,}")
    print(f"Missing UTC timestamps: {missing_utc:,}")
    print(f"Hourly observations: {len(hourly):,}")
    print(f"Missing hourly temperature: "
          f"{hourly['HourlyDryBulbTemperature'].isna().sum():,}")

    return hourly


# ============================================================
# Combine four cities using population weights
# ============================================================

def combine_cities(city_hourly):

    if abs(sum(POPULATION_WEIGHTS.values()) - 1.0) > 1e-8:
        raise ValueError("Population weights must sum to 1.")

    result = pd.DataFrame(index=UTC_HOURS)

    result.index.name = "utc_timestamp"

    weights = pd.Series(POPULATION_WEIGHTS)

    for col in NUMERIC_COLS:

        values = pd.DataFrame({
            city: city_hourly[city][col]
            for city in POPULATION_WEIGHTS
        })

        # Population-weighted average
        result[col] = (
            values.mul(weights, axis="columns")
            .sum(axis=1, min_count=4)
        )

        # Number of cities with available observations
        result[f"{col}_n_cities"] = values.notna().sum(axis=1)

    return result


# ============================================================
# Main
# ============================================================

def main():

    city_hourly = {}

    for city in POPULATION_WEIGHTS:

        path = CITY_DIR / f"{city}_merge.csv"

        if not path.exists():
            raise FileNotFoundError(path)

        print(f"\nProcessing {city}...")

        city_hourly[city] = read_hourly_utc(path)

    result = combine_cities(city_hourly)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    result.to_csv(OUTPUT_PATH)

    print("\n===================================")
    print("NOAA UTC aggregation completed")
    print("===================================")

    print(f"Output: {OUTPUT_PATH}")
    print(f"Final shape: {result.shape}")

    print("\nMissing observations:")
    print(result.isna().sum())

    print("\nNumber of cities:")
    print(result["HourlyDryBulbTemperature_n_cities"].value_counts().sort_index())

    print("\nFirst 5 observations:")
    print(result.head())

    print("\nLast 5 observations:")
    print(result.tail())


if __name__ == "__main__":
    main()