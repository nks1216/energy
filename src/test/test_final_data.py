import pandas as pd

#chk = pd.read_csv("data/final/final_data_cdd_hdd.csv")
#chk["date"] = pd.to_datetime(chk["date"])

#print(chk.loc[chk["date"] == "2021-01-01",
#              ["date", "hour", "ERCOT", "price_rt_hubavg"]].head(4))

#raw = pd.read_excel("data/raw/price/RTMLZHBSPP_2021.xlsx", sheet_name="Jan")
#raw = raw[(raw["Settlement Point Name"] == "HB_HUBAVG")
#          & (pd.to_datetime(raw["Delivery Date"]) == "2021-01-01")]
#hourly = raw.groupby("Delivery Hour")["Settlement Point Price"].mean()
#print(hourly.loc[[1, 24]])

#print(chk.loc[((chk["date"] == "2021-01-01") & (chk["hour"] == 1))
#              | ((chk["date"] == "2021-01-02") & (chk["hour"] == 0)),
#              ["date", "hour", "price_rt_hubavg"]])

raw = pd.read_excel("data/raw/price/RTMLZHBSPP_2021.xlsx", sheet_name="Nov")
raw = raw[(raw["Settlement Point Name"] == "HB_HUBAVG")
          & (raw["Delivery Hour"] == 2)
          & (pd.to_datetime(raw["Delivery Date"]) == "2021-11-07")]
print(raw[["Delivery Date", "Delivery Hour", "Delivery Interval",
           "Repeated Hour Flag", "Settlement Point Price"]].to_string())