import numpy as np, pandas as pd

for f in ["reg_load_log_coef.csv", "reg_price_droplog_coef.csv"]:
    c = pd.read_csv(f"report/table/{f}", index_col=0)
    print(f)
    print(c.loc[["CDD", "HDD", "HourlyRelativeHumidity", "HourlyWindSpeed"],
                ["coef", "std_err"]].round(5))
