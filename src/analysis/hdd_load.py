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
        count=("ERCOT", "size")
    )
    .reset_index()
)

print(hdd_stats)

# Plot
plt.figure(figsize=(8, 6))
plt.plot(
    hdd_stats["HDD_bin"],
    hdd_stats["avg_load"],
    marker="o"
)

plt.xlabel("HDD")
plt.ylabel("Average ERCOT Load (MW)")
plt.title("Average ERCOT Load by HDD")
plt.grid(True)
plt.tight_layout()

# Save figure
output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "hdd_load.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Saved figure to: {output_file}")