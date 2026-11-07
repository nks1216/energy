import pandas as pd

df = pd.read_csv(
    "data/raw/noaa/LCD_USW00003927_2024.csv",
    low_memory=False
)

test = df[
    df["DATE"].str.contains("2024-01-20")
]

print(
    test[[
        "DATE",
        "HourlyDryBulbTemperature",
        "HourlyDewPointTemperature",
        "HourlyRelativeHumidity"
    ]]
    .tail(20)
)

df = pd.read_csv(
    "data/raw/noaa/LCD_USW00003927_2024.csv",
    low_memory=False
)

mask = df["DATE"].str.contains("2024-01-20T20:53")

print(
    df.loc[mask].T
)