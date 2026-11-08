from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 11,
})

# --------------------------------------------------
# Regression sample (same filters as the regressions)
# --------------------------------------------------
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] < "2026-01-01"]
df = df.dropna(subset=["ERCOT", "price_rt_hubavg", "CDD", "HDD",
                       "HourlyRelativeHumidity", "HourlyWindSpeed"])
df = df[(df["HourlyRelativeHumidity"] >= 0)
        & (df["HourlyRelativeHumidity"] <= 100)]
print("Sample size:", len(df))                      # 43,425


def bin_stats(d, col):
    d = d.copy()
    d["bin"] = d[col].round(0)            # Same rule for Figure 1
    d = d[d["bin"] >= 1]                  # Exclude CDD(HDD) < 0.5
    g = d.groupby("bin").agg(
        load=("ERCOT", "mean"),
        price=("price_rt_hubavg", "median"),
        n=("ERCOT", "size"),
    ).reset_index()
    print(f"\n{col}: bins dropped (n < 50):")
    print(g.loc[g["n"] < 50, ["bin", "n"]].to_string(index=False))
    return g[g["n"] >= 50]

cdd = bin_stats(df, "CDD")
hdd = bin_stats(df, "HDD")

print("\nLast bins used (check counts):")
print(cdd.tail(3)[["bin", "load", "price", "n"]])
print(hdd.tail(3)[["bin", "load", "price", "n"]])

# --------------------------------------------------
# Two-panel figure
# --------------------------------------------------
fig, ax = plt.subplots(1, 2, figsize=(10, 4), sharex=True)

hot, cold = "#b8325a", "#1f77b4"   

ax[0].plot(cdd["bin"], cdd["load"], color=hot, marker="o", ms=4, lw=2,
           alpha=0.85, label="Hot weather (CDD)")
ax[0].plot(hdd["bin"], hdd["load"], color=cold, marker="s", ms=4, lw=2,
           alpha=0.85, label="Cold weather (HDD)")

ax[1].plot(cdd["bin"], cdd["price"], color=hot, marker="o", ms=4, lw=2)
ax[1].plot(hdd["bin"], hdd["price"], color=cold, marker="s", ms=4, lw=2)

ax[0].set_title("(a) Average load")
ax[0].set_ylabel("Average ERCOT load (MW)")

ax[1].set_title("(b) Median price")
ax[1].set_ylabel("Median real-time price ($/MWh)")

for a in ax:
    a.set_xlabel("Degree-hours from 18°C base")
    a.grid(alpha=0.3)
ax[0].legend(frameon=False)

fig.tight_layout()
out = Path("report/graph")
out.mkdir(parents=True, exist_ok=True)
fig.savefig(out / "cdd_hdd_load_price.png", dpi=300, bbox_inches="tight")
plt.close(fig)
print("\nSaved:", out / "cdd_hdd_load_price.png")

print(cdd[cdd["bin"].isin([10, 15, 20])][["bin", "load", "price", "n"]])
print(hdd[hdd["bin"].isin([10, 15, 20])][["bin", "load", "price", "n"]])