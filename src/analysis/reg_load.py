import pandas as pd
import statsmodels.formula.api as smf
from pathlib import Path

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv("data/final/final_data_cdd_hdd.csv")

print(df.shape)

# --------------------------------------------------
# Date variables
# --------------------------------------------------

df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month

print("\nHour values:")
print(sorted(df["hour"].unique()))

print("\nMonth values:")
print(sorted(df["month"].unique()))

# --------------------------------------------------
# Regression sample
# --------------------------------------------------

cols = [
    "ERCOT",
    "CDD",
    "HDD",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
    "hour",
    "month",
]

df = df[cols].dropna()

print(f"\nRegression sample size: {len(df):,}")

print("Before dropna:", len(df))

df = df[cols].dropna()

print("After dropna:", len(df))

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
ERCOT ~
CDD +
HDD +
HourlyRelativeHumidity +
HourlyWindSpeed +
C(hour) +
C(month)
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
with open(output_dir / "reg_load_summary.txt", "w") as f:
    f.write(model.summary().as_text())

# Coefficients
coef_table = pd.DataFrame({
    "coef": model.params,
    "std_err": model.bse,
    "t_stat": model.tvalues,
    "p_value": model.pvalues
})

coef_table.to_csv(
    output_dir / "reg_load_coef.csv"
)

# Model fit stats
with open(output_dir / "reg_load_stats.txt", "w") as f:
    f.write(f"N = {int(model.nobs)}\n")
    f.write(f"R2 = {model.rsquared:.4f}\n")
    f.write(f"Adj R2 = {model.rsquared_adj:.4f}\n")

print(model.summary())

print("\nSaved:")
print("report/table/reg_load_summary.txt")
print("report/table/reg_load_coef.csv")
print("report/table/reg_load_stats.txt")

