from pathlib import Path
import calendar

import numpy as np
import pandas as pd


# 1. Configure paths
# Script location: energy/src/data/merge_price.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "price"
OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "price_merge.csv"

YEARS = range(2021, 2026)
MONTHS = list(calendar.month_abbr)[1:]  # Jan, Feb, ..., Dec

COLUMN_MAP = {
    "Delivery Date": "delivery_date",
    "Delivery Hour": "delivery_hour",
    "Delivery Interval": "delivery_interval",
    "Repeated Hour Flag": "repeated_hour_flag",
    "Settlement Point Name": "settlement_point_name",
    "Settlement Point Price": "price_rt_hubavg",
}

HOUR_KEY = [
    "delivery_date",
    "delivery_hour",
    "repeated_hour_flag",
]


# 2. Read the monthly sheets for one year
def read_year(year):
    file_path = RAW_DIR / f"RTMLZHBSPP_{year}.xlsx"

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    monthly_frames = []

    with pd.ExcelFile(file_path, engine="openpyxl") as workbook:
        # Allow differences in sheet-name whitespace and capitalization
        sheet_lookup = {
            name.strip().lower(): name
            for name in workbook.sheet_names
        }

        for month_number, month in enumerate(MONTHS, start=1):
            if month.lower() not in sheet_lookup:
                raise ValueError(
                    f"{file_path.name}: Missing monthly sheet: {month}"
                )

            sheet_name = sheet_lookup[month.lower()]
            print(
                f"Reading: {file_path.name} / {sheet_name}",
                flush=True,
            )

            # Read only the required columns
            df = pd.read_excel(
                workbook,
                sheet_name=sheet_name,
                usecols=lambda col: str(col).strip() in COLUMN_MAP,
            )

            df.columns = df.columns.astype(str).str.strip()

            missing_columns = set(COLUMN_MAP) - set(df.columns)
            if missing_columns:
                raise ValueError(
                    f"{file_path.name}/{sheet_name}: "
                    f"Missing required columns: {missing_columns}"
                )

            df = df.rename(columns=COLUMN_MAP)

            # Keep only HB_HUBAVG records
            point_names = (
                df["settlement_point_name"]
                .astype("string")
                .str.strip()
                .str.upper()
            )

            df = df.loc[
                point_names.eq("HB_HUBAVG").fillna(False)
            ].copy()

            if df.empty:
                raise ValueError(
                    f"{file_path.name}/{sheet_name}: "
                    "No HB_HUBAVG records found."
                )

            # Parse dates and validate the year and month
            df["delivery_date"] = pd.to_datetime(
                df["delivery_date"],
                errors="raise",
            )

            dates = df["delivery_date"]

            valid_dates = (
                dates.notna()
                & dates.dt.year.eq(year)
                & dates.dt.month.eq(month_number)
                & dates.eq(dates.dt.normalize())
            )

            if not valid_dates.all():
                raise ValueError(
                    f"{file_path.name}/{sheet_name}: "
                    "Invalid dates or dates outside the expected year/month."
                )

            monthly_frames.append(df)

    return pd.concat(monthly_frames, ignore_index=True)


# 3. Validate records and calculate hourly average prices
def make_hourly(raw):
    raw = raw.copy()

    # Preserve the distinction between regular and repeated hours
    raw["repeated_hour_flag"] = (
        raw["repeated_hour_flag"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    if not raw["repeated_hour_flag"].isin(["N", "Y"]).all():
        raise ValueError(
            "Repeated Hour Flag contains missing values "
            "or values other than N/Y."
        )

    # Validate delivery hours and 15-minute intervals
    for column, allowed_values in [
        ("delivery_hour", range(1, 25)),
        ("delivery_interval", range(1, 5)),
    ]:
        values = pd.to_numeric(raw[column], errors="raise")

        if not values.isin(allowed_values).all():
            raise ValueError(
                f"{column} contains values outside the allowed range."
            )

        raw[column] = values.astype(int)

    # Convert prices to numeric values while retaining negative prices
    raw["price_rt_hubavg"] = pd.to_numeric(
        raw["price_rt_hubavg"],
        errors="raise",
    )

    if not np.isfinite(raw["price_rt_hubavg"]).all():
        raise ValueError(
            "Prices contain missing or infinite values."
        )

    # Check for duplicate intervals within each date, hour, and flag
    interval_key = HOUR_KEY + ["delivery_interval"]

    duplicated = raw.duplicated(interval_key, keep=False)

    if duplicated.any():
        sample = raw.loc[
            duplicated,
            interval_key + ["price_rt_hubavg"],
        ].head(10)

        raise ValueError(
            "Duplicate 15-minute intervals found:\n"
            f"{sample.to_string(index=False)}"
        )

    # Average the four 15-minute prices within each hour
    hourly = raw.groupby(HOUR_KEY, as_index=False).agg(
        price_rt_hubavg=("price_rt_hubavg", "mean"),
        n_intervals=("delivery_interval", "size"),
    )

    # Stop before saving if any hour does not contain four intervals
    incomplete = hourly["n_intervals"].ne(4)

    if incomplete.any():
        sample = hourly.loc[incomplete].head(10)

        raise ValueError(
            "Hours with missing 15-minute intervals found:\n"
            f"{sample.to_string(index=False)}"
        )

    hourly = hourly.sort_values(HOUR_KEY).reset_index(drop=True)

    return hourly


# 4. Combine all years and save the output
def main():
    yearly_frames = []

    for year in YEARS:
        yearly_frames.append(read_year(year))

    raw = pd.concat(yearly_frames, ignore_index=True)
    hourly = make_hourly(raw)

    # Check annual row counts to detect potentially missing entire hours
    for year in YEARS:
        actual = int(hourly["delivery_date"].dt.year.eq(year).sum())
        expected = 8784 if calendar.isleap(year) else 8760

        print(
            f"{year}: {actual:,} rows / expected {expected:,} rows"
        )

        if actual != expected:
            raise ValueError(
                f"Unexpected number of hourly records for {year}. "
                "Check the source data for missing hours "
                "or differences in hour labeling."
            )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    hourly.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d",
    )

    print(f"\nSaved: {OUTPUT_PATH}")
    print(f"Total rows: {len(hourly):,}")
    print(hourly.head().to_string(index=False))


if __name__ == "__main__":
    main()