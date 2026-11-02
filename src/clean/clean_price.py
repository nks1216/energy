import pandas as pd

from _common import INTERIM, calendar_hours, numeric, require_unique, save


def clean_price(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["delivery_date"], errors="raise").dt.strftime("%Y-%m-%d")
    df["repeated_hour_flag"] = df["repeated_hour_flag"].astype("string").str.strip().str.upper()
    if not df["repeated_hour_flag"].isin(["N", "Y"]).all():
        raise ValueError("Price: Expected repeated-hour flags N/Y")
    numeric(df, ["delivery_hour", "price_rt_hubavg", "n_intervals"])
    if not df["delivery_hour"].isin(range(1, 25)).all():
        raise ValueError("Price: Expected delivery hours from 1 to 24")
    if df["price_rt_hubavg"].isna().any() or not df["n_intervals"].eq(4).all():
        raise ValueError("Price: Missing prices or incomplete 15-minute intervals")
    keys = ["date", "delivery_hour", "repeated_hour_flag"]
    require_unique(df, keys, "Price")
    result = calendar_hours().merge(df, on=keys, how="outer", validate="one_to_one", indicator=True)
    bad = result["_merge"].ne("both")
    if bad.any():
        raise ValueError(f"Price: Missing or unexpected delivery hours:\n{result.loc[bad, keys + ['_merge']].head(12)}")
    return result[["timestamp_utc", "price_rt_hubavg", "n_intervals", "repeated_hour_flag"]].rename(
        columns={"price_rt_hubavg": "price_mwh"}
    )


def main():
    save(clean_price(pd.read_csv(INTERIM / "price_merge.csv")), "price_clean.csv")


if __name__ == "__main__":
    main()
