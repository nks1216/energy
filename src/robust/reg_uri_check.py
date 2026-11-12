from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import S_hac_simple


# --------------------------------------------------
# HAC using actual UTC hourly intervals
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

    # Preserve excluded hours in the covariance time axis only.
    # No prices, loads, or weather values are imputed.
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

df["date"] = pd.to_datetime(df["date"])
df["utc_timestamp"] = pd.to_datetime(
    df["utc_timestamp"], utc=True, errors="raise"
)

if df["utc_timestamp"].isna().any():
    raise ValueError("Missing UTC timestamps.")
if df["utc_timestamp"].duplicated().any():
    raise ValueError("Duplicate UTC timestamps.")

# Retain the original local-time definitions
end = df["date"] + pd.to_timedelta(df["hour"], unit="h")
df["start"] = end - pd.Timedelta(hours=1)
df["month"] = df["start"].dt.month
df["year"] = df["start"].dt.year


# --------------------------------------------------
# Sample filters: unchanged
# --------------------------------------------------
needed = [
    "ERCOT",
    "price_rt_hubavg",
    "CDD",
    "HDD",
    "HourlyRelativeHumidity",
    "HourlyWindSpeed",
]

df = df.dropna(subset=needed).copy()
df = df[
    df["HourlyRelativeHumidity"].between(0, 100)
].copy()

df = df.sort_values("utc_timestamp").reset_index(drop=True)

df["log_load"] = np.log(df["ERCOT"])

if not np.isfinite(df["log_load"]).all():
    raise ValueError("Log load contains nonfinite values.")

pos = df.loc[df["price_rt_hubavg"] > 0].copy()
pos["log_price"] = np.log(pos["price_rt_hubavg"])

if not np.isfinite(pos["log_price"]).all():
    raise ValueError("Log price contains nonfinite values.")


# --------------------------------------------------
# Uri exclusion: February 8–20 inclusive, local dates
# --------------------------------------------------
URI_START = pd.Timestamp("2021-02-08")
URI_END = pd.Timestamp("2021-02-21")  # exclusive


def not_uri(data):
    storm = (
        (data["start"] >= URI_START)
        & (data["start"] < URI_END)
    )
    return data.loc[~storm].copy()


# --------------------------------------------------
# Regression specification
# --------------------------------------------------
rhs = (
    "CDD + HDD + HourlyRelativeHumidity + HourlyWindSpeed"
    " + C(hour) + C(month) + C(year)"
)

rows = []


def run(data, y, label):
    data = data.sort_values("utc_timestamp").reset_index(drop=True)

    base = smf.ols(
        f"{y} ~ {rhs}",
        data=data,
        missing="raise",
    ).fit()

    model = fit_utc_hac(
        base,
        data["utc_timestamp"],
        maxlags=24,
    )

    # Attach names because robust results return arrays
    names = base.model.exog_names
    coef = pd.Series(np.asarray(model.params), index=names)
    se = pd.Series(np.asarray(model.bse), index=names)
    pval = pd.Series(np.asarray(model.pvalues), index=names)

    test = model.t_test("CDD - HDD = 0")

    rows.append({
        "model": label,
        "N": int(model.nobs),
        "R2": model.rsquared,
        "CDD": coef["CDD"],
        "CDD_se": se["CDD"],
        "CDD_p": pval["CDD"],
        "HDD": coef["HDD"],
        "HDD_se": se["HDD"],
        "HDD_p": pval["HDD"],
        "diff": float(np.squeeze(test.effect)),
        "diff_se": float(np.squeeze(test.sd)),
        "diff_p": float(np.squeeze(test.pvalue)),
    })


run(df, "log_load", "load, full")
run(not_uri(df), "log_load", "load, excl. Uri")
run(pos, "log_price", "price, full")
run(not_uri(pos), "log_price", "price, excl. Uri")


# --------------------------------------------------
# Display and save
# --------------------------------------------------
out = pd.DataFrame(rows)

print(out.to_string(
    index=False,
    formatters={
        "R2": "{:.3f}".format,
        "CDD": "{:.4f}".format,
        "CDD_se": "{:.4f}".format,
        "CDD_p": "{:.6g}".format,
        "HDD": "{:.4f}".format,
        "HDD_se": "{:.4f}".format,
        "HDD_p": "{:.6g}".format,
        "diff": "{:.4f}".format,
        "diff_se": "{:.4f}".format,
        "diff_p": "{:.6g}".format,
    },
))

output_dir = Path("report/robust")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "uri_check.csv"
out.to_csv(output_file, index=False)

print(f"\nSaved: {output_file}")