from pathlib import Path
import pandas as pd

# --------------------------------------------------
# Load regression dataset and apply the same filters
# --------------------------------------------------
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] < "2026-01-01"]

needed = ["ERCOT", "price_rt_hubavg", "HourlyDryBulbTemperature",
          "CDD", "HDD", "HourlyRelativeHumidity", "HourlyWindSpeed"]
df = df.dropna(subset=needed)
df = df[(df["HourlyRelativeHumidity"] >= 0)
        & (df["HourlyRelativeHumidity"] <= 100)]

pos = df[df["price_rt_hubavg"] > 0]

print("Load regression sample:", len(df))        # 43,425
print("Positive-price sample:", len(pos))        # 42,505
print("Share of hours with CDD > 0: %.3f" % (df["CDD"] > 0).mean())
print("Share of hours with HDD > 0: %.3f" % (df["HDD"] > 0).mean())

# --------------------------------------------------
# Rows: (label, series, number of decimals)
# --------------------------------------------------
rows = [
    ("Load (MW)",                     df["ERCOT"],                    0),
    ("Price, all hours ($/MWh)",      df["price_rt_hubavg"],          1),
    ("Price, positive hours ($/MWh)", pos["price_rt_hubavg"],         1),
    ("Temperature (°C)",              df["HourlyDryBulbTemperature"], 2),
    ("CDD (degree-hours)",            df["CDD"],                      2),
    ("HDD (degree-hours)",            df["HDD"],                      2),
    ("Relative humidity (%)",         df["HourlyRelativeHumidity"],   2),
    ("Wind speed (m/s)",              df["HourlyWindSpeed"],          2),
]

def fmt(x, d):
    return f"{x:,.{d}f}"

records = []
for name, s, d in rows:
    min_str = fmt(s.min(), 4) if (name.startswith("Price, positive")
                                  and round(s.min(), d) == 0) else fmt(s.min(), d)
    records.append({
        "Variable": name,
        "Mean": fmt(s.mean(), d),
        "Std":  fmt(s.std(), d),
        "Min":  min_str,
        "Max":  fmt(s.max(), d),
        "N":    f"{int(s.count()):,}",
    })

table = pd.DataFrame(records)
print("\n" + table.to_string(index=False))

output_dir = Path("report/table")
output_dir.mkdir(parents=True, exist_ok=True)
table.to_csv(output_dir / "summary_stats.csv", index=False)
print("\nSaved: report/table/summary_stats.csv")