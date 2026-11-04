
from pathlib import Path
import pandas as pd

# ==================================================
# 1. PATH SETTINGS
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ERCOT_PATH = PROJECT_ROOT / "data" / "interim" / "ercot_merge.csv"
PRICE_PATH = PROJECT_ROOT / "data" / "interim" / "price_merge.csv"

OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "ercot_price_merge.csv"


# ==================================================
# 2. LOAD DATA
# ==================================================

def load_data():

    print("Loading ERCOT data...")
    ercot = pd.read_csv(ERCOT_PATH)

    print("Loading price data...")
    price = pd.read_csv(PRICE_PATH)

    return ercot, price


# ==================================================
# 3. PREPARE MERGE KEYS
# ==================================================

def prepare_data(ercot, price):

    # ERCOT timestamp
    ercot["Hour Ending"] = pd.to_datetime(
        ercot["Hour Ending"]
    )

    ercot["date"] = ercot["Hour Ending"].dt.date
    ercot["hour"] = ercot["Hour Ending"].dt.hour

    # Price date and hour
    price["delivery_date"] = pd.to_datetime(
        price["delivery_date"]
    ).dt.date

    # Convert repeated hour flag to boolean
    price["has_dst_marker"] = (
        price["repeated_hour_flag"] == "Y"
    )

    # ERCOT hour-ending convention:
    # Hour Ending 01:00 corresponds to Delivery Hour 1.
    # Hour Ending 24:00 is represented as 00:00
    # on the following calendar date.
    ercot["delivery_date"] = ercot["Hour Ending"].dt.date
    ercot["delivery_hour"] = ercot["Hour Ending"].dt.hour

    # Convert midnight (00:00) to delivery hour 24
    midnight = ercot["delivery_hour"] == 0

    ercot.loc[midnight, "delivery_date"] = (
        ercot.loc[midnight, "Hour Ending"]
        .apply(lambda x: (x - pd.Timedelta(days=1)).date())
    )

    ercot.loc[midnight, "delivery_hour"] = 24

    return ercot, price


# ==================================================
# 4. MERGE DATA
# ==================================================

def merge_data(ercot, price):

    merge_keys = [
        "delivery_date",
        "delivery_hour",
        "has_dst_marker"
    ]

    print("\nMerging ERCOT and price data...")

    merged = pd.merge(
        ercot,
        price,
        on=merge_keys,
        how="left",
        validate="one_to_one",
        indicator=True
    )

    return merged


# ==================================================
# 5. CHECK MERGE RESULTS
# ==================================================

def check_merge(merged, ercot, price):

    print("\n========== MERGE CHECK ==========")

    print("\nERCOT observations:", len(ercot))
    print("Price observations:", len(price))
    print("Merged observations:", len(merged))

    print("\nMerge status:")
    print(merged["_merge"].value_counts())

    print("\nMissing price values:")
    print(merged["price_rt_hubavg"].isna().sum())

    print("\nRepeated hour observations:")
    print(
        merged.loc[
            merged["has_dst_marker"],
            [
                "delivery_date",
                "delivery_hour",
                "has_dst_marker",
                "price_rt_hubavg"
            ]
        ].to_string(index=False)
    )

    # Check unmatched price observations
    print("\nUnmatched price observations:")
    unmatched = price.merge(
        ercot[
            [
                "delivery_date",
                "delivery_hour",
                "has_dst_marker"
            ]
        ].drop_duplicates(),
        on=[
            "delivery_date",
            "delivery_hour",
            "has_dst_marker"
        ],
        how="left",
        indicator=True
    )

    print(
        unmatched.loc[
            unmatched["_merge"] == "left_only"
        ].to_string(index=False)
    )


# ==================================================
# 6. SAVE DATA
# ==================================================

def save_data(merged):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    merged = merged.drop(columns=["_merge"])

    merged.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\nSaved to:", OUTPUT_PATH)


# ==================================================
# 7. MAIN
# ==================================================

def main():

    ercot, price = load_data()

    ercot, price = prepare_data(
        ercot,
        price
    )

    merged = merge_data(
        ercot,
        price
    )

    check_merge(
        merged,
        ercot,
        price
    )

    save_data(merged)

    print("\nERCOT-Price merge completed!")
    print("Final shape:", merged.shape)


if __name__ == "__main__":
    main()
