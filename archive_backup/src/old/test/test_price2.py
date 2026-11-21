import pandas as pd
import statsmodels.formula.api as smf
from pathlib import Path
import numpy as np

# --------------------------------------------------
# Load data
# --------------------------------------------------

df = pd.read_csv("data/final/final_data_cdd_hdd.csv")

print((df["price_rt_hubavg"] <= 0).sum(), (df["price_rt_hubavg"] <= 0).mean())