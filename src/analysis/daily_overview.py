from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 11,
})

# --------------------------------------------------
# Load data
# --------------------------------------------------
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
df["date"] = pd.to_datetime(df["date"])
df["log_load"] = np.log(df["ERCOT"])

# Same time construction as reg_load_log.py
end = df["date"] + pd.to_timedelta(df["hour"], unit="h")
df["start"] = end - pd.Timedelta(hours=1)

df["month"] = df["start"].dt.month
df["year"] = df["start"].dt.year

# --------------------------------------------------
# Apply the load-regression sample filters
# --------------------------------------------------
required = [
    "log_load", "ERCOT", "CDD", "HDD",
    "HourlyRelativeHumidity", "HourlyWindSpeed",
    "hour", "month", "year", "date",
]

df = df.sort_values(["date", "hour"])
df = df.dropna(subset=required).copy()
df = df[
    df["HourlyRelativeHumidity"].between(0, 100)
].copy()

# No temperature-bin exclusions.
# Zero and negative prices are retained.
print("Load regression sample:", len(df))
print(df["year"].value_counts().sort_index())

# --------------------------------------------------
# Daily means based on the hour-beginning date
# --------------------------------------------------
daily = (
    df.set_index("start")
      .resample("D")
      .agg(
          mean_load=("ERCOT", "mean"),
          mean_price=("price_rt_hubavg", "mean"),
          mean_temperature=("HourlyDryBulbTemperature", "mean"),
          n_load=("ERCOT", "count"),
          n_price=("price_rt_hubavg", "count"),
          n_temperature=("HourlyDryBulbTemperature", "count"),
      )
)

# --------------------------------------------------
# Save daily data
# --------------------------------------------------
graph_dir = Path("report/graph")
table_dir = Path("report/table")

graph_dir.mkdir(parents=True, exist_ok=True)
table_dir.mkdir(parents=True, exist_ok=True)

data_path = table_dir / "daily_load_price_temp.csv"
daily.to_csv(data_path, index_label="date")

# --------------------------------------------------
# Settings shared by both figures
# --------------------------------------------------
storm_start = pd.Timestamp("2021-02-08")
storm_end = pd.Timestamp("2021-02-21")  # exclusive

storm_mask = (
    (daily.index >= storm_start)
    & (daily.index < storm_end)
)

panels = [
    ("mean_load", "(a) Daily mean load",
     "Load (MW)", "#2878B5"),
    ("mean_price", "(b) Daily mean real-time price",
     "Price ($/MWh)", "#D95319"),
    ("mean_temperature", "(c) Daily mean temperature",
     "Temperature (°C)", "#2A9D8F"),
]

# --------------------------------------------------
# Create two figures
# --------------------------------------------------
for exclude_uri_price in [False, True]:

    plot_data = daily.copy()

    if exclude_uri_price:
        # Leave a gap without changing load or temperature.
        plot_data.loc[storm_mask, "mean_price"] = np.nan

    fig, axes = plt.subplots(
        3, 1,
        figsize=(11, 8),
        sharex=True,
    )

    for ax, (column, title, ylabel, color) in zip(axes, panels):

        if exclude_uri_price and column == "mean_price":
            title = (
                "(b) Daily mean real-time price "
                "excluding February 8–20, 2021"
            )

        ax.axvspan(
            storm_start,
            storm_end,
            color="gray",
            alpha=0.25,
            linewidth=0,
            zorder=0,
        )

        ax.plot(
            plot_data.index,
            plot_data[column],
            color=color,
            linewidth=1,
        )

        ax.set_title(title, loc="left")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.25)
        ax.set_axisbelow(True)

    axes[0].ticklabel_format(
        axis="y", style="plain", useOffset=False
    )

    axes[0].legend(
        handles=[
            Patch(
                facecolor="gray",
                alpha=0.25,
                label="February 8–20, 2021",
            )
        ],
        loc="upper right",
        frameon=False,
    )

    axes[2].axhline(
        0, color="gray", linestyle="--", linewidth=0.8
    )

    axes[2].xaxis.set_major_locator(mdates.YearLocator())
    axes[2].xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )
    axes[2].set_xlabel("Date")
    axes[2].set_xlim(
        daily.index.min(), daily.index.max()
    )

    # Fixed margins keep panel sizes aligned between figures.
    fig.subplots_adjust(
        left=0.11,
        right=0.98,
        bottom=0.08,
        top=0.95,
        hspace=0.35,
    )

    if exclude_uri_price:
        filename = "daily_load_price_temp_excluding_uri_price.png"
    else:
        filename = "daily_load_price_temp.png"

    figure_path = graph_dir / filename

    # Do not crop: preserve identical image dimensions.
    fig.savefig(figure_path, dpi=300)
    plt.close(fig)

    print(f"Saved: {figure_path}")

print(f"Saved: {data_path}")