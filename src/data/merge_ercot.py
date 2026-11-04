
from pathlib import Path
import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "ercot"
OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "ercot_merge.csv"


# --------------------------------------------------
# 2. Load and process individual files
# --------------------------------------------------

def process_file(file_path):
    """Load and process one ERCOT Excel file."""

    print(f"Loading: {file_path.name}")

    df = pd.read_excel(file_path)

    # Preserve original Hour Ending
    raw = df["Hour Ending"].astype("string").str.strip()

    df["hour_ending_raw"] = raw

    # Identify DST marker
    df["has_dst_marker"] = raw.str.endswith(
        " DST",
        na=False
    )

    # Remove DST suffix for datetime conversion
    clean = raw.str.replace(
        " DST",
        "",
        regex=False
    )

    # Split date and time
    parts = clean.str.split(n=1, expand=True)

    # Parse date
    date = pd.to_datetime(
        parts[0],
        format="mixed",
        errors="raise"
    )

    # Add seconds if necessary
    time_text = parts[1]

    time_text = time_text.where(
        time_text.str.count(":") != 1,
        time_text + ":00"
    )

    # Convert time to timedelta
    time_delta = pd.to_timedelta(
        time_text,
        errors="raise"
    )

    # Create normalized Hour Ending
    df["Hour Ending"] = date + time_delta

    return df


# --------------------------------------------------
# 3. Merge all ERCOT files
# --------------------------------------------------

def merge_files():

    files = sorted(INPUT_DIR.glob("*.xlsx"))

    if not files:
        raise FileNotFoundError(
            f"No Excel files found in {INPUT_DIR}"
        )

    dfs = [
        process_file(file_path)
        for file_path in files
    ]

    merged = pd.concat(
        dfs,
        ignore_index=True
    )

    return merged

def check_dst(merged):

    print("\n========== DST CHECK ==========")

    # 1. DST marker distribution check
    print("\nDST marker count:")
    print(merged["has_dst_marker"].value_counts(dropna=False))

    # 2. DST marker row check
    dst_rows = merged.loc[
        merged["has_dst_marker"],
        ["hour_ending_raw", "Hour Ending", "has_dst_marker"]
    ]

    print("\nRecords with DST marker:")
    print(dst_rows.to_string(index=False))

    # 3. Hour Ending dupulication check
    duplicates = merged[
        merged.duplicated(subset=["Hour Ending"], keep=False)
    ].sort_values("Hour Ending")

    print("\nDuplicate Hour Ending records:")
    print(duplicates[
        ["hour_ending_raw", "Hour Ending", "has_dst_marker"]
    ].to_string(index=False))

    print("\nNumber of duplicated timestamps:")
    print(len(duplicates))


# --------------------------------------------------
# 4. Save merged data
# --------------------------------------------------

def save_data(df):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(f"\nSaved to: {OUTPUT_PATH}")


# --------------------------------------------------
# 5. Main
# --------------------------------------------------

def main():

    # Merge all ERCOT files
    merged = merge_files()

    # Check DST and duplicated timestamps
    check_dst(merged)

    # Save interim dataset
    save_data(merged)

    # Summary
    print("\nMerge completed!")
    print("Final shape:", merged.shape)

    print("\nDST marker count:")
    print(merged["has_dst_marker"].value_counts(dropna=False))

    print("\nRecords with DST marker:")

    print(
        merged.loc[
            merged["has_dst_marker"],
            [
                "hour_ending_raw",
                "Hour Ending",
                "has_dst_marker"
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
