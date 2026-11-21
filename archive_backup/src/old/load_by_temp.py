from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("data/final/final_data.csv")

# Create temperature bins (1°F intervals)
df["temp_bin"] = (
    df["HourlyDryBulbTemperature"]
    .round(0)
)

# Calculate average load and count by temperature bin
temp_stats = (
    df.groupby("temp_bin")
      .agg(
          avg_load=("ERCOT", "mean"),
          count=("ERCOT", "size")
      )
      .reset_index()
)

# Remove bins with fewer than 50 observations
temp_stats = temp_stats[
    temp_stats["count"] >= 50
]

# Plot
plt.figure(figsize=(8, 6))

plt.plot(
    temp_stats["temp_bin"],
    temp_stats["avg_load"],
    linewidth=2
)

plt.xlabel("Temperature (°C)")
plt.ylabel("Average ERCOT Load (MW)")
plt.title("Average ERCOT Load by Temperature")

plt.grid(alpha=0.3)

# Save figure
output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "load_by_temp.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Saved figure to: {output_file}")