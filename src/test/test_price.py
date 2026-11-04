import pandas as pd

df = pd.read_csv("data/interim/price_merge.csv")

# Repeated Hour Flag 분포 확인
print(df["repeated_hour_flag"].value_counts(dropna=False))

# 2021년 DST 전환일 전후 확인
result = df[
    (df["delivery_date"] >= "2021-11-07") &
    (df["delivery_date"] <= "2021-11-08")
]

print(
    result[
        ["delivery_date", "delivery_hour",
         "repeated_hour_flag", "price_rt_hubavg", "n_intervals"]
    ].to_string(index=False)
)