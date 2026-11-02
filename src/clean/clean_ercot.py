import pandas as pd

from _common import INTERIM, TZ, calendar_hours, numeric, save


def clean_load(df):
    df = df.copy()
    raw = df["hour_ending_raw"].astype("string").str.strip()
    text = raw.str.replace(" DST", "", regex=False)
    parts = text.str.split(n=1, expand=True)
    df["date"] = pd.to_datetime(parts[0], format="mixed", errors="raise").dt.strftime("%Y-%m-%d")
    durations = pd.to_timedelta(parts[1].where(parts[1].str.count(":") != 1, parts[1] + ":00"))
    hours = durations.dt.total_seconds() / 3600
    if not hours.isin(range(1, 25)).all():
        raise ValueError("ERCOT: Expected whole hour-ending labels from 1 to 24")
    df["source_hour"] = hours.astype(int)
    numeric(df, ["ERCOT"])
    if df["ERCOT"].isna().any() or df["ERCOT"].le(0).any():
        raise ValueError("ERCOT: Missing or nonpositive load")

    # The supplied merge script preserves source order within each day.
    # On transition days, validate that order against the physical clock.
    schedule = calendar_hours()
    expected_dates = set(schedule["date"])
    if set(df["date"]) != expected_dates:
        raise ValueError("ERCOT: Missing or unexpected delivery dates")
    frames = []
    source_days = dict(tuple(df.groupby("date", sort=False)))
    for date, expected in schedule.groupby("date", sort=True):
        actual = source_days[date].reset_index(drop=True)
        expected = expected.reset_index(drop=True)
        nominal = expected["delivery_hour"].tolist()
        # Some load workbooks use actual end-clock labels on transition days.
        end = (expected["timestamp_utc"] + pd.Timedelta(hours=1)).dt.tz_convert(TZ)
        end_hours = end.dt.hour.where(end.dt.hour.ne(0), 24).tolist()
        labels = actual["source_hour"].tolist()
        if len(actual) != len(expected) or (labels != nominal and labels != end_hours):
            raise ValueError(
                f"ERCOT {date}: Unexpected hour sequence; no timestamps were guessed.\n"
                f"Observed: {labels}\nExpected nominal: {nominal}\n"
                f"Expected end-clock: {end_hours}"
            )
        part = pd.DataFrame({
            "timestamp_utc": expected["timestamp_utc"],
            "load_mw": actual["ERCOT"],
            "hour_ending_raw": actual["hour_ending_raw"],
            "has_dst_marker": actual["hour_ending_raw"].astype("string").str.endswith(" DST"),
        })
        frames.append(part)
        if len(expected) != 24:
            print(f"ERCOT transition day {date}: {len(expected)} hours; source order preserved")
    return pd.concat(frames, ignore_index=True)


def main():
    df = pd.read_csv(INTERIM / "ercot_merge.csv", usecols=["hour_ending_raw", "ERCOT"])
    save(clean_load(df), "ercot_clean.csv")


if __name__ == "__main__":
    main()
