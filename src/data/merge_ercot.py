import glob
import os
import pandas as pd

files = sorted(glob.glob("data/raw/ercot/*.xlsx"))

if not files:
    raise FileNotFoundError("No Excel files found in data/raw/ercot/")

dfs = []

for f in files:
    print("Loading:", f)
    df = pd.read_excel(f)

    # Preserve original labels and DST markers
    raw = df["Hour Ending"].astype("string").str.strip()
    df["hour_ending_raw"] = raw
    df["has_dst_marker"] = raw.str.endswith(" DST", na=False)

    # Remove the suffix from the parsing copy
    clean = raw.str.replace(" DST", "", regex=False)

    # Parse the date and hour separately; hour 24 advances to the next day
    # Split the date and time
    parts = clean.str.split(n=1, expand=True)

    # Accept both MM/DD/YYYY and YYYY-MM-DD
    date = pd.to_datetime(
        parts[0],
        format="mixed",
        errors="raise",
    )

    # Add seconds only when the time contains hours and minutes
    time_text = parts[1]
    time_text = time_text.where(
        time_text.str.count(":") != 1,
        time_text + ":00",
    )

    # Hour 24 automatically advances to the next day
    hour = pd.to_timedelta(time_text, errors="raise")

    df["Hour Ending"] = date + hour

    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

# Extract calendar variables from the hour-ending timestamp
dt = merged["Hour Ending"].dt
merged["hour"] = dt.hour
merged["day"] = dt.day
merged["dayofweek"] = dt.dayofweek
merged["month"] = dt.month
merged["year"] = dt.year

os.makedirs("data/interim", exist_ok=True)
merged.to_csv("data/interim/ercot_merge.csv", index=False)

print("Done! Final shape:", merged.shape)


print("Done! Final shape:", merged.shape)

# Display records with a DST marker
print(
    merged.loc[
        merged["has_dst_marker"],
        ["hour_ending_raw", "Hour Ending", "has_dst_marker"],
    ].to_string(index=False)
)