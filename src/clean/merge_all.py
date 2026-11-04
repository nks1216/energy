from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ERCOT_PATH = PROJECT_ROOT / "data" / "clean" / "ercot_price_merge.csv"
NOAA_PATH = PROJECT_ROOT / "data" / "clean" / "utc_noaa.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "ercot_price_noaa.csv"

def main():
    # 1. Read data
    ercot = pd.read_csv(ERCOT_PATH)
    noaa = pd.read_csv(NOAA_PATH)

    # 2. Parse ERCOT local hour-ending timestamps
    ercot["Hour Ending"] = pd.to_datetime(ercot["Hour Ending"])

    # 3. Localize ERCOT hour-ending timestamps to Texas time.
    #    DST-marked repeated hours are the first occurrence (CDT).
    #    Non-DST-marked repeated hours are the second occurrence (CST).
    ercot["utc_hour_ending"] = (
        ercot["Hour Ending"]
        .dt.tz_localize(
            "America/Chicago",
            ambiguous=ercot["has_dst_marker"].astype(bool).to_numpy(),
            nonexistent="NaT",
        )
        .dt.tz_convert("UTC")
    )

    # 3. Convert hour-ending timestamps to local hour-beginning timestamps.
    ercot["hour_start_local"] = (
        ercot["Hour Ending"] - pd.Timedelta(hours=1)
    )

    # 4. Localize hour-beginning timestamps to Texas time.
    ercot["utc_timestamp"] = (
        ercot["hour_start_local"]
        .dt.tz_localize(
            "America/Chicago",
            ambiguous=ercot["has_dst_marker"].astype(bool).to_numpy(),
            nonexistent="shift_forward",
        )
        .dt.tz_convert("UTC")
    )

    # 5. Parse NOAA UTC timestamps
    noaa["utc_timestamp"] = pd.to_datetime(
        noaa["utc_timestamp"],
        errors="coerce",
        utc=True,
    )

    # 6. Check duplicate keys
    if ercot["utc_timestamp"].duplicated().any():
        raise ValueError("Duplicate UTC timestamps found in ERCOT data.")

    if noaa["utc_timestamp"].duplicated().any():
        raise ValueError("Duplicate UTC timestamps found in NOAA data.")

    # 7. Merge
    merged = ercot.merge(
        noaa,
        on="utc_timestamp",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    # 8. Validation
    print("ERCOT rows:", len(ercot))
    print("NOAA rows:", len(noaa))
    print("Merged rows:", len(merged))
    print("\nMerge status:")
    print(merged["_merge"].value_counts(dropna=False))

    print("\nMissing NOAA temperature:",
          merged["HourlyDryBulbTemperature"].isna().sum())

    print("\nTemperature city coverage:")
    print(
        merged["HourlyDryBulbTemperature_n_cities"]
        .value_counts(dropna=False)
        .sort_index()
    )

    print("\nDST repeated-hour check:")
    print(
        merged.loc[
            merged["has_dst_marker"].astype(bool),
            ["Hour Ending", "hour_ending_raw",
             "utc_timestamp", "ERCOT",
             "price_rt_hubavg", "HourlyDryBulbTemperature"]
        ].to_string(index=False)
    )

    # 9. Save
    merged = merged.drop(columns="_merge")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print("\nSaved:", OUTPUT_PATH)

if __name__ == "__main__":
    main()