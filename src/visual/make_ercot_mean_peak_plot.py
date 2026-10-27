import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

# 1. Set file paths
data_path = "data/interim/ercot_merge.csv"
output_dir = "report/graph"
output_filename = "ercot_daily_trend.png"
output_path = os.path.join(output_dir, output_filename)

# Create output directory if it does not exist
os.makedirs(output_dir, exist_ok=True)

# 2. Load ERCOT data
print("Loading ERCOT data...")
df = pd.read_csv(data_path)

# Convert 'Hour Ending' column to datetime format
df["Hour Ending"] = pd.to_datetime(df["Hour Ending"])

# Create a Date column (strip time information for daily aggregation)
df["Date"] = df["Hour Ending"].dt.date

# 3. Aggregate daily mean and peak loads
# Based on the ERCOT total demand column ('ERCOT')
print("Aggregating daily mean and peak loads...")
daily_df = (
    df.groupby("Date")["ERCOT"]
    .agg(Daily_Mean="mean", Daily_Peak="max")
    .reset_index()
)

# Convert Date column back to datetime for time-series plotting
daily_df["Date"] = pd.to_datetime(daily_df["Date"])

# 4. Set plotting style and configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# (1) First subplot: Daily Peak Load (highlighting winter storms and summer peaks)
axes[0].plot(
    daily_df["Date"],
    daily_df["Daily_Peak"],
    color="#d9534f",
    linewidth=1.0,
    label="Daily Peak Load",
)
axes[0].set_ylabel("Peak Demand (MW)", fontsize=11, fontweight="bold")
axes[0].set_title(
    "ERCOT Daily Peak and Mean Electricity Demand (2021-2025)",
    fontsize=14,
    fontweight="bold",
    pad=15,
)
axes[0].legend(loc="upper left")
axes[0].grid(True, linestyle="--", alpha=0.6)

# (2) Second subplot: Daily Mean Load (checking baseload trends and seasonality)
axes[1].plot(
    daily_df["Date"],
    daily_df["Daily_Mean"],
    color="#0275d8",
    linewidth=1.0,
    label="Daily Mean Load",
)
axes[1].set_ylabel("Mean Demand (MW)", fontsize=11, fontweight="bold")
axes[1].set_xlabel("Date", fontsize=11, fontweight="bold")
axes[1].legend(loc="upper left")
axes[1].grid(True, linestyle="--", alpha=0.6)

# Set X-axis date formatting (display by year)
axes[1].xaxis.set_major_locator(mdates.YearLocator())
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.autofmt_xdate(ha="center")

# Adjust layout and save figure
plt.tight_layout()
plt.savefig(output_path, dpi=300)
print(f"Successfully saved plot to {output_path}")

# Check for data anomality for top 5 Daily Mean
print(daily_df.sort_values(by="Daily_Mean", ascending=False).head(5))