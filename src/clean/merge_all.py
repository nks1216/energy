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

    # 3. Convert hour-ending timestamps to local hour-beginning timestamps.
    ercot["hour_start_local"] = (
        ercot["Hour Ending"] - pd.Timedelta(hours=1)
    )

    # 4. Localize hour-beginning timestamps to Texas time.
    #    ERCOT's Repeated Hour Flag = Y marks the repeated (second) occurrence
    #    of the hour after the fall-back transition, i.e. CST.
    #    pandas: ambiguous=True means DST (first occurrence, CDT),
    #    so the flag must be inverted.
    is_repeated = ercot["has_dst_marker"].astype(bool)
    ercot["utc_timestamp"] = (
        ercot["hour_start_local"]
        .dt.tz_localize(
            "America/Chicago",
            ambiguous=(~is_repeated).to_numpy(),
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

    # Repeated-hour check: show BOTH rows of each pair
    pairs = merged[merged["Hour Ending"].duplicated(keep=False)]
    print("\nDST repeated-hour check (both rows of each pair):")
    print(
        pairs.sort_values("utc_timestamp")[
            ["Hour Ending", "has_dst_marker", "utc_timestamp",
             "ERCOT", "price_rt_hubavg", "HourlyDryBulbTemperature"]
        ].to_string(index=False)
    )

    # The flagged (repeated) row must be one hour LATER in UTC than the unflagged row
    for he, g in pairs.groupby("Hour Ending"):
        flagged = g["has_dst_marker"].astype(bool)
        t_flagged = g.loc[flagged, "utc_timestamp"].iloc[0]
        t_normal = g.loc[~flagged, "utc_timestamp"].iloc[0]
        if t_flagged <= t_normal:
            raise ValueError(f"Repeated-hour order is wrong at {he}")

    # 9. Save
    merged = merged.drop(columns="_merge")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print("\nSaved:", OUTPUT_PATH)

if __name__ == "__main__":
    main()