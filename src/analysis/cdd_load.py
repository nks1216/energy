import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")

# Create bins
df["CDD_bin"] = df["CDD"].round(0)

# Count observations
counts = df["CDD_bin"].value_counts()

# Keep bins with at least 50 observations
valid_bins = counts[counts >= 50].index

# Apply BOTH conditions
df_plot = df[
    (df["CDD_bin"].isin(valid_bins))
    & (df["CDD"] > 0)
]

# Calculate statistics
cdd_stats = (
    df_plot.groupby("CDD_bin")
    .agg(
        avg_load=("ERCOT", "mean"),
        count=("ERCOT", "size")
    )
    .reset_index()
)

print(cdd_stats)

# Plot
plt.figure(figsize=(8, 6))
plt.plot(
    cdd_stats["CDD_bin"],
    cdd_stats["avg_load"],
    marker="o"
)

plt.xlabel("CDD")
plt.ylabel("Average ERCOT Load (MW)")
plt.title("Average ERCOT Load by CDD")
plt.grid(True)
plt.tight_layout()

# Save figure
output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "cdd_load.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Saved figure to: {output_file}")