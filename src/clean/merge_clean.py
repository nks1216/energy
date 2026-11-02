import pandas as pd

from _common import CLEAN, calendar_hours, require_unique, save


def read_clean(filename):
    df = pd.read_csv(CLEAN / filename)
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="raise")
    require_unique(df, ["timestamp_utc"], filename)
    return df


def main():
    result = calendar_hours()[["timestamp_utc", "datetime_local", "date"]]
    for name, filename in [
        ("ercot", "ercot_clean.csv"),
        ("price", "price_clean.csv"),
        ("noaa", "noaa_clean.csv"),
    ]:
        source = read_clean(filename)
        extra = (~source["timestamp_utc"].isin(result["timestamp_utc"])).sum()
        if extra:
            print(f"{name}: {extra} source hours outside the target local-date range")
        result = result.merge(source, on="timestamp_utc", how="left", validate="one_to_one", indicator="_matched")
        result[f"{name}_matched"] = result.pop("_matched").eq("both")
        missing = (~result[f"{name}_matched"]).sum()
        print(f"{name}: {missing} unmatched target hours")
        if name != "noaa" and missing:
            raise ValueError(f"{name}: Missing target hours; check the cleaning outputs")

    local = result["datetime_local"].dt
    result["hour"] = local.hour
    result["day"] = local.day
    result["dayofweek"] = local.dayofweek
    result["month"] = local.month
    result["year"] = local.year
    result["is_summer"] = local.month.isin([6, 7, 8])
    result["core_complete"] = result[["load_mw", "price_mwh", "temperature_c"]].notna().all(axis=1)
    print("\nMissing core values:")
    print(result[["load_mw", "price_mwh", "temperature_c"]].isna().sum().to_string())
    print(f"\nHours with all three core measurements: {result['core_complete'].sum():,}")
    save(result, "energy_hourly.csv")


if __name__ == "__main__":
    main()
