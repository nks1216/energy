import pandas as pd
from pathlib import Path

# Import data
path = Path("data/final/final_data.csv")
df = pd.read_csv(path)

# Analysis Variables
variables = {
    "ERCOT Load (MW)": "ERCOT",
    "RT Price ($/MWh)": "price_rt_hubavg",
    "Temperature (C)": "HourlyDryBulbTemperature",
    "Humidity (%)": "HourlyRelativeHumidity",
    "Wind Speed": "HourlyWindSpeed"
}

rows = []

for name, col in variables.items():

    s = df[col].dropna()

    rows.append({
        "Variable": name,
        "Mean": round(s.mean(), 2),
        "Std": round(s.std(), 2),
        "Min": round(s.min(), 2),
        "Max": round(s.max(), 2),
        "N": len(s)
    })

table1 = pd.DataFrame(rows)

print(table1)

# Save
output_path = Path("report/table/table1_summary.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)

table1.to_csv(output_path, index=False)

print(f"\nSaved: {output_path}")