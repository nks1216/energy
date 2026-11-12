from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import S_hac_simple


# --------------------------------------------------
# HAC standard errors using actual UTC time intervals
# --------------------------------------------------
def fit_utc_hac(base, timestamps, maxlags=24):
    utc = pd.DatetimeIndex(
        pd.to_datetime(timestamps, utc=True, errors="raise")
    )

    if len(utc) != int(base.nobs):
        raise ValueError("Timestamp count does not match regression N.")
    if utc.hasnans or not utc.is_unique:
        raise ValueError("UTC timestamps must be nonmissing and unique.")
    if not utc.is_monotonic_increasing:
        raise ValueError("Sort by UTC before fitting OLS.")

    grid = pd.date_range(
        start=utc.min(),
        end=utc.max(),
        freq="h",
    )
    positions = grid.get_indexer(utc)

    if (positions < 0).any():
        raise ValueError("Some timestamps are not on the hourly grid.")

    X = np.asarray(base.model.exog)
    residuals = np.asarray(base.resid)
    scores = X * residuals[:, None]

    # Preserve time gaps in the covariance calculation only.
    # Excluded prices and weather values are not imputed.
    grid_scores = np.zeros((len(grid), X.shape[1]))
    grid_scores[positions] = scores

    meat = S_hac_simple(grid_scores, nlags=maxlags)
    bread = np.asarray(base.normalized_cov_params)

    covariance = bread @ meat @ bread
    covariance = (covariance + covariance.T) / 2

    result = base.get_robustcov_results(
        cov_type="HAC",
        maxlags=maxlags,
        use_correction=False,
        use_t=False,
    )

    result.cov_params_default = covariance
    result._cache.clear()

    result.cov_kwds["description"] = (
        "HAC standard errors using actual UTC hourly intervals, "
        f"Bartlett weights, maximum lag {maxlags} hours, "
        "without small-sample correction"
    )

    return result


# --------------------------------------------------
# Load data
# --------------------------------------------------
df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
print("Original shape:", df.shape)

df["date"] = pd.to_datetime(df["date"])
df["utc_timestamp"] = pd.to_datetime(
    df["utc_timestamp"], utc=True, errors="raise"
)

if df["utc_timestamp"].isna().any():
    raise ValueError("Missing UTC timestamps.")
if df["utc_timestamp"].duplicated().any():
    raise ValueError("Duplicate UTC timestamps.")


# --------------------------------------------------
# Date variables: same definitions as before
# --------------------------------------------------
end = df["date"] + pd.to_timedelta(df["hour"], unit="h")
start = end - pd.Timedelta(hours=1)

df["month"] = start.dt.month
df["year"] = start.dt.year


# --------------------------------------------------
# Price diagnostics before sample filtering
# --------------------------------------------------
n_before = len(df)
nonpos = df.loc[df["price_rt_hubavg"] <= 0].copy()

print(
    f"\nNon-positive price hours before other filters: "
    f"{len(nonpos):,} ({len(nonpos) / n_before:.2%})"
)

print("\nNon-positive price hours by month:")
print(nonpos["month"].value_counts().sort_index())

print("\nNon-positive price hours by hour:")
print(nonpos["hour"].value_counts().sort_index())

print("\nCDD/HDD of non-positive-price hours:")
print(nonpos[["CDD", "HDD"]].describe())


# --------------------------------------------------
# Drop non-positive prices, then take logarithms
# --------------------------------------------------
df = df.loc[df["price_rt_hubavg"] > 0].copy()
df["log_price"] = np.log(df["price_rt_hubavg"])


# --------------------------------------------------
# Regression sample: same filters as before
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
    "utc_timestamp",
]

print("\nBefore dropna:", len(df))
df = df[cols].dropna().copy()
print("After dropna:", len(df))

df = df[
    df["HourlyRelativeHumidity"].between(0, 100)
].copy()

if not np.isfinite(df["log_price"]).all():
    raise ValueError("Log price contains nonfinite values.")

df = df.sort_values("utc_timestamp").reset_index(drop=True)

print(f"\nFinal regression sample size: {len(df):,}")
print(df["year"].value_counts().sort_index())

print(
    "\nPrices below $1 in final sample (kept):",
    (df["price_rt_hubavg"] < 1).sum(),
)


# --------------------------------------------------
# OLS model: unchanged specification
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

base = smf.ols(
    formula=formula,
    data=df,
    missing="raise",
).fit()

model = fit_utc_hac(
    base,
    df["utc_timestamp"],
    maxlags=24,
)


# --------------------------------------------------
# Save outputs
# --------------------------------------------------
output_dir = Path("report/table")
output_dir.mkdir(parents=True, exist_ok=True)

summary_text = model.summary().as_text()

with open(
    output_dir / "reg_price_droplog_summary.txt",
    "w",
    encoding="utf-8",
) as f:
    f.write(summary_text)

coef_table = pd.DataFrame(
    {
        "coef": np.asarray(model.params),
        "std_err": np.asarray(model.bse),
        "z_stat": np.asarray(model.tvalues),
        "p_value": np.asarray(model.pvalues),
    },
    index=base.model.exog_names,
)

coef_table.to_csv(output_dir / "reg_price_droplog_coef.csv")

with open(
    output_dir / "reg_price_droplog_stats.txt",
    "w",
    encoding="utf-8",
) as f:
    f.write(f"N = {int(model.nobs)}\n")
    f.write(f"R2 = {model.rsquared:.4f}\n")
    f.write(f"Adj R2 = {model.rsquared_adj:.4f}\n")

print(summary_text)


# --------------------------------------------------
# Equality test using UTC-based HAC covariance
# --------------------------------------------------
equality_test = model.t_test("CDD - HDD = 0")

print("\nCDD - HDD = 0 test (z test):")
print(equality_test)

with open(
    output_dir / "reg_price_droplog_ztest.txt",
    "w",
    encoding="utf-8",
) as f:
    f.write(str(equality_test))

print(
    "\ndiff:", float(np.squeeze(equality_test.effect)),
    "se:", float(np.squeeze(equality_test.sd)),
    "p:", float(np.squeeze(equality_test.pvalue)),
)

print("\nPrice summary (regression sample):")
print(df["price_rt_hubavg"].describe())
print(df["log_price"].describe())

print("\nSaved:")
print(output_dir / "reg_price_droplog_summary.txt")
print(output_dir / "reg_price_droplog_coef.csv")
print(output_dir / "reg_price_droplog_stats.txt")
print(output_dir / "reg_price_droplog_ztest.txt")