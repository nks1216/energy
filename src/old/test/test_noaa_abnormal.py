import pandas as pd
from pathlib import Path

CITY_DIR = Path("data/interim/city")

cities = [
    "austin",
    "dallas",
    "houston",
    "sanantonio",
]

for city in cities:
    df = pd.read_csv(
        CITY_DIR / f"{city}_merge.csv"
    )

    max_rh = df["HourlyRelativeHumidity"].max()

    print(
        f"{city}: max RH = {max_rh:.2f}"
    )

    abnormal = df[
        df["HourlyRelativeHumidity"] > 100
    ]

    print(
        f"RH > 100 observations: {len(abnormal)}"
    )

    if len(abnormal) > 0:
        print(
            abnormal[
                [
                    "DATE",
                    "HourlyDryBulbTemperature",
                    "HourlyDewPointTemperature",
                    "HourlyRelativeHumidity",
                ]
            ].head()
        )

    print("-" * 50)