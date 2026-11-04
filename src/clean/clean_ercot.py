
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = PROJECT_ROOT / "data" / "interim" / "ercot_merge.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "ercot_clean.csv"


# --------------------------------------------------
# 2. Load data
# --------------------------------------------------

def load_data():

    df = pd.read_csv(INPUT_PATH)

    print("Original data shape:", df.shape)

    return df


# --------------------------------------------------
# 3. Clean data
# --------------------------------------------------

def clean_data(df):

    # Select required columns
    selected_columns = [
        "Hour Ending",
        "ERCOT",
        "has_dst_marker",
    ]

    df = df[selected_columns].copy()

    # Convert Hour Ending to datetime
    df["Hour Ending"] = pd.to_datetime(
        df["Hour Ending"],
        errors="coerce"
    )

    # Convert ERCOT demand to numeric
    df["ERCOT"] = pd.to_numeric(
        df["ERCOT"],
        errors="coerce"
    )

    # Remove missing observations
    df = df.dropna(
        subset=["Hour Ending", "ERCOT"]
    )

    # Sort by time
    df = df.sort_values("Hour Ending")

    # Reset index
    df = df.reset_index(drop=True)

    print("Cleaned data shape:", df.shape)

    return df


# --------------------------------------------------
# 4. Save data
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

    print("Cleaned data saved to:")
    print(OUTPUT_PATH)


# --------------------------------------------------
# 5. Main
# --------------------------------------------------

def main():

    df = load_data()

    df_clean = clean_data(df)

    save_data(df_clean)


if __name__ == "__main__":
    main()
