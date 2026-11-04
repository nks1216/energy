import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load the merged ERCOT-NOAA dataset
df = pd.read_csv("data/final/final_data.csv")

# Create scatter plot
plt.figure(figsize=(8, 6))

plt.scatter(
    df["HourlyDryBulbTemperature"],
    df["ERCOT"],
    alpha=0.03,
    s=1
)

# Add labels and title
plt.xlabel("Temperature (°C)")
plt.ylabel("ERCOT Load (MW)")
plt.title("Temperature vs ERCOT Load")

plt.tight_layout()

# Create output directory if it does not exist
output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)

# Save figure
output_file = output_dir / "temp_vs_load_scatter.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

# Close figure to free memory
plt.close()

print(f"Saved figure to: {output_file}")