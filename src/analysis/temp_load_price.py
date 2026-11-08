from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],   
    "font.size": 11,
})

# --------------------------------------------------
# Load regression dataset and apply the same filters
# --------------------------------------------------
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] < "2026-01-01"]                       

df = df.dropna(subset=["ERCOT", "price_rt_hubavg", "HourlyDryBulbTemperature",
                       "HourlyRelativeHumidity", "HourlyWindSpeed"])
df = df[(df["HourlyRelativeHumidity"] >= 0)
        & (df["HourlyRelativeHumidity"] <= 100)]
print("Sample size:", len(df))                            

# --------------------------------------------------
# Bin by temperature (1°C)
# --------------------------------------------------
df["temp_bin"] = df["HourlyDryBulbTemperature"].round(0)

stats = (
    df.groupby("temp_bin")
      .agg(avg_load=("ERCOT", "mean"),
           med_price=("price_rt_hubavg", "median"),
           count=("ERCOT", "size"))
      .reset_index()
)

print("\nBins below 5°C (check number of hours):")
print(stats.loc[stats["temp_bin"] < 5, ["temp_bin", "count"]].to_string(index=False))

stats = stats[stats["count"] >= 50]

# --------------------------------------------------
# Two-panel figure
# --------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(10, 4), sharex=True)

ax[0].plot(stats["temp_bin"], stats["avg_load"], linewidth=2)
ax[0].set_title("(a) Mean load")
ax[0].set_ylabel("Mean ERCOT load (MW)")

ax[1].plot(stats["temp_bin"], stats["med_price"], linewidth=2)
ax[1].set_title("(b) Median price")
ax[1].set_ylabel("Median real-time price ($/MWh)")

for a in ax:
    a.axvline(18, linestyle="--", color="gray", linewidth=1)   # base temperature
    a.set_xlabel("Temperature (°C)")
    a.grid(alpha=0.3)

fig.tight_layout()

output_dir = Path("report/graph")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "temp_load_price.png"
fig.savefig(output_file, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"\nSaved figure to: {output_file}")