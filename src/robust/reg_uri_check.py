from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("data/final/final_data_cdd_hdd.csv")
df["date"] = pd.to_datetime(df["date"])
end = df["date"] + pd.to_timedelta(df["hour"], unit="h")
df["start"] = end - pd.Timedelta(hours=1)
df["month"] = df["start"].dt.month
df["year"] = df["start"].dt.year

df = df.sort_values(["date", "hour"]).reset_index(drop=True)
needed = ["ERCOT", "price_rt_hubavg", "CDD", "HDD",
          "HourlyRelativeHumidity", "HourlyWindSpeed"]
df = df.dropna(subset=needed)
df = df[(df["HourlyRelativeHumidity"] >= 0) & (df["HourlyRelativeHumidity"] <= 100)]

df["log_load"] = np.log(df["ERCOT"])
pos = df[df["price_rt_hubavg"] > 0].copy()
pos["log_price"] = np.log(pos["price_rt_hubavg"])

URI_START, URI_END = "2021-02-08", "2021-02-21"      # Feb 8-20 inclusive

def not_uri(d):
    return d[~((d["start"] >= URI_START) & (d["start"] < URI_END))]

rhs = ("CDD + HDD + HourlyRelativeHumidity + HourlyWindSpeed"
       " + C(hour) + C(month) + C(year)")
rows = []

def run(data, y, label):
    m = smf.ols(f"{y} ~ {rhs}", data=data).fit(
        cov_type="HAC", cov_kwds={"maxlags": 24})
    t = m.t_test("CDD - HDD = 0")
    rows.append({
        "model": label, "N": int(m.nobs), "R2": round(m.rsquared, 3),
        "CDD": m.params["CDD"], "CDD_se": m.bse["CDD"],
        "HDD": m.params["HDD"], "HDD_se": m.bse["HDD"],
        "diff": float(np.squeeze(t.effect)), "diff_se": float(np.squeeze(t.sd)),
        "diff_p": float(np.squeeze(t.pvalue)),
    })

run(df, "log_load", "load, full")
run(not_uri(df), "log_load", "load, excl. Uri")
run(pos, "log_price", "price, full")
run(not_uri(pos), "log_price", "price, excl. Uri")

out = pd.DataFrame(rows)
print(out.round(4).to_string(index=False))

path = Path("report/robust")
path.mkdir(parents=True, exist_ok=True)
out.to_csv(path / "uri_check.csv", index=False)