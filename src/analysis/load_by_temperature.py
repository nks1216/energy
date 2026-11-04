import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load dataset
df = pd.read_csv("data/final/final_data.csv")

# Create temperature bins (1°C intervals)
df["temp_bin"] = (
    df["HourlyDryBulbTemperature"]
    .round(0)
)

# Calculate average load by temperature bin
avg_load = (
    df.groupby("temp_bin")["ERCOT"]
      .mean()
      .reset_index()
)

# Plot
plt.figure(figsize=(8, 6))

plt.plot(
    avg_load["temp_bin"],
    avg_load["ERCOT"],
    linewidth=2.5,
    color="steelblue"
)

plt.xlabel("Temperature (°C)")
plt.ylabel("Average ERCOT Load (MW)")
plt.title("Average ERCOT Load by Temperature")

plt.grid(alpha=0.3)

# Save figure
output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "load_by_temperature.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print(f"Saved figure to: {output_file}")