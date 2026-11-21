import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")

# Create bins
df["HDD_bin"] = df["HDD"].round(0)

# Count observations
counts = df["HDD_bin"].value_counts()

# Keep bins with at least 50 observations
valid_bins = counts[counts >= 50].index

# Apply BOTH conditions
df_plot = df[
    (df["HDD_bin"].isin(valid_bins))
    & (df["HDD"] > 0)
]

# Calculate statistics
hdd_stats = (
    df_plot.groupby("HDD_bin")
    .agg(
        avg_load=("ERCOT", "mean"),
        median_price=("price_rt_hubavg", "median"),
        count=("ERCOT", "size")
    )
    .reset_index()
)

print(hdd_stats)

load_color = "#1f4e79"
price_color = "#b85450"

fig, ax1 = plt.subplots(figsize=(8, 6))

# Load
ax1.plot(
    hdd_stats["HDD_bin"],
    hdd_stats["avg_load"],
    color=load_color,
    marker="o",
    linewidth=2,
    label="Average Load"
)

ax1.set_xlabel("HDD")
ax1.set_ylabel(
    "Average ERCOT Load (MW)",
    color=load_color
)
ax1.tick_params(axis="y", labelcolor=load_color)

# Price
ax2 = ax1.twinx()

ax2.plot(
    hdd_stats["HDD_bin"],
    hdd_stats["median_price"],
    color=price_color,
    marker="s",
    linewidth=2,
    label="Median RT Price"
)

ax2.set_ylabel(
    "Median RT Price ($/MWh)",
    color=price_color
)
ax2.tick_params(axis="y", labelcolor=price_color)

plt.title(
    "Average ERCOT Load and Median RT Price by HDD"
)

ax1.grid(True)

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()

ax1.legend(
    lines1 + lines2,
    labels1 + labels2,
    loc="upper left"
)

plt.tight_layout()

# Save figure
output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "hdd_price_median.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Saved figure to: {output_file}")