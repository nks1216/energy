import os
import pandas as pd
from functools import reduce

# Define file paths for raw population CSV files
pop_files = {
    "austin": "data/raw/population/AUSPOP.csv",
    "dallas": "data/raw/population/DFWPOP.csv",
    "houston": "data/raw/population/HTNPOP.csv",
    "sanantonio": "data/raw/population/SATPOP.csv"
}

dfs = []

# Read each city's CSV file and filter for the 2021-2025 period
for city, path in pop_files.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
        
    df = pd.read_csv(path)
    df['observation_date'] = pd.to_datetime(df['observation_date'])
    df['year'] = df['observation_date'].dt.year
    
    # Filter observations between 2021 and 2025
    df = df[(df['year'] >= 2021) & (df['year'] <= 2025)]
    
    # Convert observation_date to clean 'YYYY-MM-DD' string format matching raw data
    df['observation_date'] = df['observation_date'].dt.strftime('%Y-%m-%d')
    
    # Rename value column to the respective city name
    value_col = [c for c in df.columns if c not in ['observation_date', 'year']][0]
    df = df.rename(columns={value_col: city})
    df = df[['observation_date', 'year', city]]
    dfs.append(df)

# Merge all four city DataFrames on 'observation_date' and 'year'
merged_df = reduce(lambda left, right: pd.merge(left, right, on=['observation_date', 'year'], how='outer'), dfs)
merged_df = merged_df.sort_values('observation_date').reset_index(drop=True)

# Compute mean population and population weights for 2021-2025
mean_pops = merged_df[['austin', 'dallas', 'houston', 'sanantonio']].mean()
total_mean_pop = mean_pops.sum()
weights = mean_pops / total_mean_pop

# Create a summary DataFrame
summary_df = pd.DataFrame({
    'City': mean_pops.index,
    'Mean_Population_2021_2025': mean_pops.values,
    'Population_Weight': weights.values
})

# Export processed population data and weights to an Excel file in data/interim/
os.makedirs("data/interim", exist_ok=True)
output_excel_path = "data/interim/population_summary.xlsx"

with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
    merged_df.to_excel(writer, sheet_name='Yearly_Data_2021_2025', index=False)
    summary_df.to_excel(writer, sheet_name='Average_Weights', index=False)

print(f"Success! Population summary saved to: {output_excel_path}")
print("\n[Calculated 2021-2025 Population Weights]")
print(weights)