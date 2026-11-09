import numpy as np
import pandas as pd

old = pd.read_csv("src/old/final_data_cdd_hdd_old.csv")      
new = pd.read_csv("data/final/final_data_cdd_hdd.csv")

cols = ["HourlyDryBulbTemperature", "HourlyRelativeHumidity", "HourlyWindSpeed",
        "CDD", "HDD", "ERCOT", "price_rt_hubavg"]
same = np.isclose(old[cols].astype(float), new[cols].astype(float), equal_nan=True)
changed = ~same.all(axis=1)

print("changed rows:", changed.sum())                              # 4가 나와야 함
print(new.loc[changed, ["date", "hour"] + cols].to_string())
print("ERCOT/price changed:", (~same[:, 5:7].all(axis=1)).sum())   # 0이어야 함