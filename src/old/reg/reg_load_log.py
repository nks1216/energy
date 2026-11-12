import pandas as pd
import statsmodels.formula.api as smf
from pathlib import Path
import numpy as np

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv("data/final/final_data_cdd_hdd.csv")

print(df.shape)
df["log_load"] = np.log(df["ERCOT"])

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
# Regression sample
# --------------------------------------------------

cols = [
    "log_load",
    "ERCOT",
    "CDD",
    "HDD",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "hour",
    "month", 
    "year", 
    "date"
]

print("Before dropna:", len(df))

df = df.sort_values(["date", "hour"]).reset_index(drop=True)
df = df[cols].dropna()

print("After dropna:", len(df))

print(f"\nRegression sample size: {len(df):,}")

# --------------------------------------------------
# Model 4
# --------------------------------------------------

# remove physically impossible humidity values
df = df[
    (df["HourlyRelativeHumidity"] >= 0)
    &
    (df["HourlyRelativeHumidity"] <= 100)
]

formula = """
log_load ~
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
    cov_kwds={"maxlags":24}
)

# --------------------------------------------------
# Save outputs
# --------------------------------------------------

output_dir = Path("report/table")
output_dir.mkdir(parents=True, exist_ok=True)

# Full regression output
with open(output_dir / "reg_load_log_summary.txt", "w") as f:
    f.write(model.summary().as_text())

# Coefficients
coef_table = pd.DataFrame({
    "coef": model.params,
    "std_err": model.bse,
    "t_stat": model.tvalues,
    "p_value": model.pvalues
})

coef_table.to_csv(
    output_dir / "reg_load_log_coef.csv"
)

# Model fit stats
with open(output_dir / "reg_load_log_stats.txt", "w") as f:
    f.write(f"N = {int(model.nobs)}\n")
    f.write(f"R2 = {model.rsquared:.4f}\n")
    f.write(f"Adj R2 = {model.rsquared_adj:.4f}\n")

print(model.summary())

print("\nSaved:")
print("report/table/reg_load_log_summary.txt")
print("report/table/reg_load_log_coef.csv")
print("report/table/reg_load_log_stats.txt")

print("\nERCOT Load Summary:")
print(df["ERCOT"].describe())

ttest = model.t_test("CDD - HDD = 0")
print("\nCDD - HDD = 0 test:")
print(ttest)

with open(output_dir / "reg_load_log_ttest.txt", "w") as f:
    f.write(str(ttest))

print("diff:", float(np.squeeze(ttest.effect)), "se:", float(np.squeeze(ttest.sd)),
      "p:", float(np.squeeze(ttest.pvalue)))