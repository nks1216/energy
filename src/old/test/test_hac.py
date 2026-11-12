from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import S_hac_simple


# --------------------------------------------------
# HAC covariance using actual UTC hourly intervals
# --------------------------------------------------
def fit_utc_hac(base, timestamps, maxlags=24):
    """
    Keep OLS coefficients unchanged.
    Calculate Bartlett HAC covariance on a regular UTC hourly grid.
    No small-sample correction; use asymptotic normal (z) tests.
    """
    utc = pd.DatetimeIndex(
        pd.to_datetime(timestamps, utc=True, errors="raise")
    )

    if len(utc) != int(base.nobs):
        raise ValueError("Timestamp count does not match regression N.")
    if utc.hasnans or not utc.is_unique:
        raise ValueError("UTC timestamps must be nonmissing and unique.")
    if not utc.is_monotonic_increasing:
        raise ValueError("Sort the sample by UTC before fitting OLS.")

    grid = pd.date_range(
        start=utc.min(),
        end=utc.max(),
        freq="h",
    )
    positions = grid.get_indexer(utc)

    if (positions < 0).any():
        raise ValueError("Some timestamps are not on the hourly grid.")

    # OLS score contribution for each retained observation: x_t * residual_t
    X = np.asarray(base.model.exog)
    residuals = np.asarray(base.resid)
    scores = X * residuals[:, None]

    # Zeros preserve excluded hours in the covariance calculation only.
    grid_scores = np.zeros((len(grid), X.shape[1]))
    grid_scores[positions] = scores

    # Bartlett weights: w(k) = 1 - k / (maxlags + 1)
    meat = S_hac_simple(grid_scores, nlags=maxlags)

    bread = np.asarray(base.normalized_cov_params)
    covariance = bread @ meat @ bread
    covariance = (covariance + covariance.T) / 2

    # Obtain a results object, then replace its default HAC covariance.
    # summary(), bse, pvalues, and t_test() will use the new covariance.
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

df["log_load"] = np.log(df["ERCOT"])


# --------------------------------------------------
# Date variables: retain the original definitions
# --------------------------------------------------
end = df["date"] + pd.to_timedelta(df["hour"], unit="h")
start = end - pd.Timedelta(hours=1)

df["month"] = start.dt.month
df["year"] = start.dt.year


# --------------------------------------------------
# Regression sample: retain the original filters
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
    "date",
    "utc_timestamp",
]

print("Before dropna:", len(df))
df = df[cols].dropna().copy()
print("After dropna:", len(df))

df = df[
    df["HourlyRelativeHumidity"].between(0, 100)
].copy()

if not np.isfinite(df["log_load"]).all():
    raise ValueError("Log load contains nonfinite values.")

df = df.sort_values("utc_timestamp").reset_index(drop=True)

print(f"\nFinal regression sample size: {len(df):,}")
print(df["year"].value_counts().sort_index())


# --------------------------------------------------
# OLS specification: unchanged
# --------------------------------------------------
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

base = smf.ols(
    formula=formula,
    data=df,
    missing="raise",
).fit()

# Standard HAC using retained row order, for comparison
row_hac = base.get_robustcov_results(
    cov_type="HAC",
    maxlags=24,
    use_correction=False,
    use_t=False,
)

# HAC using actual UTC hourly intervals
model = fit_utc_hac(
    base,
    df["utc_timestamp"],
    maxlags=24,
)


# --------------------------------------------------
# Internal check:
# On a gap-free grid, UTC HAC must match standard HAC.
# --------------------------------------------------
check_time = pd.date_range(
    "2000-01-01",
    periods=int(base.nobs),
    freq="h",
    tz="UTC",
)
check_model = fit_utc_hac(base, check_time, maxlags=24)

np.testing.assert_allclose(
    check_model.cov_params(),
    row_hac.cov_params(),
    rtol=1e-7,
    atol=1e-10,
)
print("\nGap-free HAC equivalence check: passed")


# --------------------------------------------------
# Coefficient table
# --------------------------------------------------
names = base.model.exog_names

coef_table = pd.DataFrame({
    "coef": np.asarray(model.params),
    "std_err": np.asarray(model.bse),
    "z_stat": np.asarray(model.tvalues),
    "p_value": np.asarray(model.pvalues),
}, index=names)

ci = np.asarray(model.conf_int())
coef_table["ci_lower"] = ci[:, 0]
coef_table["ci_upper"] = ci[:, 1]


# --------------------------------------------------
# Compare the two covariance calculations
# --------------------------------------------------
comparison_rows = []

for label, result in [
    ("HAC: 24 retained observations", row_hac),
    ("HAC: 24 actual UTC hours", model),
]:
    se = pd.Series(np.asarray(result.bse), index=names)
    pval = pd.Series(np.asarray(result.pvalues), index=names)
    test = result.t_test("CDD - HDD = 0")

    comparison_rows.append({
        "method": label,
        "CDD_se": se["CDD"],
        "CDD_p": pval["CDD"],
        "HDD_se": se["HDD"],
        "HDD_p": pval["HDD"],
        "diff": float(np.squeeze(test.effect)),
        "diff_se": float(np.squeeze(test.sd)),
        "diff_p": float(np.squeeze(test.pvalue)),
    })

comparison = pd.DataFrame(comparison_rows)

print("\nHAC comparison:")
print(comparison.to_string(
    index=False,
    float_format=lambda x: f"{x:.6g}",
))


# --------------------------------------------------
# Save outputs: preserve existing output files
# --------------------------------------------------
output_dir = Path("report/table")
output_dir.mkdir(parents=True, exist_ok=True)

stem = "reg_load_log_utc_hac"

with open(
    output_dir / f"{stem}_summary.txt", "w", encoding="utf-8"
) as f:
    f.write(model.summary().as_text())

coef_table.to_csv(output_dir / f"{stem}_coef.csv")

with open(
    output_dir / f"{stem}_stats.txt", "w", encoding="utf-8"
) as f:
    f.write(f"N = {int(model.nobs)}\n")
    f.write(f"R2 = {model.rsquared:.4f}\n")
    f.write(f"Adj R2 = {model.rsquared_adj:.4f}\n")

ttest = model.t_test("CDD - HDD = 0")

with open(
    output_dir / f"{stem}_ttest.txt", "w", encoding="utf-8"
) as f:
    f.write(str(ttest))

comparison.to_csv(
    output_dir / f"{stem}_comparison.csv",
    index=False,
)

print("\nUTC-based HAC regression results:")
print(model.summary())

print("\nCDD - HDD = 0 test:")
print(ttest)

print("\nERCOT Load Summary:")
print(df["ERCOT"].describe())

print(f"\nSaved: report/table/{stem}_*.txt / *.csv")