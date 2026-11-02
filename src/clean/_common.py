from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
INTERIM = ROOT / "data" / "interim"
CLEAN = ROOT / "data" / "clean"
TZ = "America/Chicago"
START = "2021-01-01"
STOP = "2026-01-01"


def calendar_hours():
    """Use interval starts; preserve both occurrences of the fall-back hour."""
    local = pd.date_range(START, STOP, freq="h", tz=TZ, inclusive="left")
    result = pd.DataFrame({"timestamp_utc": local.tz_convert("UTC")})
    result["datetime_local"] = local
    result["date"] = local.strftime("%Y-%m-%d")
    # ERCOT nominal HE labels are local interval-start hours plus one.
    result["delivery_hour"] = local.hour + 1
    repeated = result.duplicated(["date", "delivery_hour"])
    result["repeated_hour_flag"] = np.where(repeated, "Y", "N")
    return result


def numeric(df, columns):
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if np.isinf(df[col].dropna()).any():
            raise ValueError(f"Infinite values in {col}")


def require_unique(df, columns, name):
    if df[columns].isna().any().any():
        raise ValueError(f"{name}: Missing merge keys")
    bad = df.duplicated(columns, keep=False)
    if bad.any():
        raise ValueError(f"{name}: Duplicate merge keys:\n{df.loc[bad].head(8)}")


def save(df, filename):
    require_unique(df, ["timestamp_utc"], filename)
    CLEAN.mkdir(parents=True, exist_ok=True)
    path = CLEAN / filename
    df.sort_values("timestamp_utc").to_csv(path, index=False, encoding="utf-8-sig")
    print(f"Saved: {path} ({len(df):,} rows)")


if __name__ == "__main__":
    raise SystemExit("This helper is imported by the four cleaning scripts.")
