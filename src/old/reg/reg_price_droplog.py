import pandas as pd
import statsmodels.formula.api as smf
from pathlib import Path
import numpy as np

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
print(df.shape)

# --------------------------------------------------
# Date variables
# --------------------------------------------------

df["date"] = pd.to_datetime(df["date"])
end = df["date"] + pd.to_timedelta(df["hour"], unit="h")   # hour-ending time
start = end - pd.Timedelta(hours=1)                         # hour-beginning time
df["month"] = start.dt.month
df["year"] = start.dt.year
print(df["year"].value_counts().sort_index())               # check: 2021-2025 only

# --------------------------------------------------
# Price transformation: drop non-positive prices, then log
# --------------------------------------------------

df_full = df.copy()                         

n_before = len(df)
n_nonpos = (df["price_rt_hubavg"] <= 0).sum()
print(f"\nNon-positive price hours: {n_nonpos} ({n_nonpos / n_before:.2%})")

# Diagnostics: when do the dropped hours occur?
nonpos = df_full[df_full["price_rt_hubavg"] <= 0]
print("\nNon-positive price hours by month:")
print(nonpos["month"].value_counts().sort_index())
print("\nNon-positive price hours by hour:")
print(nonpos["hour"].value_counts().sort_index())
print("\nCDD/HDD of dropped hours:")
print(nonpos[["CDD", "HDD"]].describe())

df = df[df["price_rt_hubavg"] > 0].copy()
df["log_price"] = np.log(df["price_rt_hubavg"])

print("\nPrices below $1 (kept):", (df["price_rt_hubavg"] < 1).sum())

# --------------------------------------------------
# Regression sample
# --------------------------------------------------

cols = [
    "price_rt_hubavg",
    "log_price",
    "CDD",
    "HDD",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "hour",
    "month",
    "year",
    "date",
]

df = df.sort_values(["date", "hour"]).reset_index(drop=True)

print("\nBefore dropna:", len(df))
df = df[cols].dropna()
print("After dropna:", len(df))

# remove physically impossible humidity values
df = df[
    (df["HourlyRelativeHumidity"] >= 0)
    & (df["HourlyRelativeHumidity"] <= 100)
]
print(f"\nRegression sample size: {len(df):,}")

# --------------------------------------------------
# Model
# --------------------------------------------------

formula = """
log_price ~
CDD +
HDD +
HourlyRelativeHumidity +
HourlyWindSpeed +
C(hour) +
C(month) +
C(year)
"""

model = smf.ols(
    formula=formula,
    data=df
).fit(
    cov_type="HAC",
    cov_kwds={"maxlags": 24}
)

# --------------------------------------------------
# Save outputs
# --------------------------------------------------

output_dir = Path("report/table")
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / "reg_price_droplog_summary.txt", "w") as f:
    f.write(model.summary().as_text())

coef_table = pd.DataFrame({
    "coef": model.params,
    "std_err": model.bse,
    "t_stat": model.tvalues,
    "p_value": model.pvalues
})
coef_table.to_csv(output_dir / "reg_price_droplog_coef.csv")

with open(output_dir / "reg_price_droplog_stats.txt", "w") as f:
    f.write(f"N = {int(model.nobs)}\n")
    f.write(f"R2 = {model.rsquared:.4f}\n")
    f.write(f"Adj R2 = {model.rsquared_adj:.4f}\n")

print(model.summary())

ttest = model.t_test("CDD - HDD = 0")
print("\nCDD - HDD = 0 test:")
print(ttest)

with open(output_dir / "reg_price_droplog_ttest.txt", "w") as f:
    f.write(str(ttest))

print("\nSaved: report/table/reg_price_droplog_*.{txt,csv}")

print("\nPrice summary (regression sample):")
print(df["price_rt_hubavg"].describe())
print(df["log_price"].describe())

print("diff:", float(np.squeeze(ttest.effect)), "se:", float(np.squeeze(ttest.sd)),
      "p:", float(np.squeeze(ttest.pvalue)))