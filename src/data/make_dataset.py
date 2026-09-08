import pandas as pd

# Load data
ercot = pd.read_csv("ercot_merge.csv")
texas = pd.read_csv("texas_merge.csv")

# Convert datetime columns
ercot['DATE'] = pd.to_datetime(ercot['Hour Ending'])
texas['DATE'] = pd.to_datetime(texas['DATE'])

# Drop unnecessary regional load columns
drop_cols = ['COAST','EAST','FWEST','NORTH','NCENT','SOUTH','SCENT','WEST']
ercot = ercot.drop(columns=drop_cols)

# Merge ERCOT and weather data
df = ercot.merge(texas, on='DATE', how='inner')

# Sort by datetime
df = df.sort_values('DATE').reset_index(drop=True)

# Train/Test split
train = df[df['year'] <= 2024].copy()
test  = df[df['year'] == 2025].copy()

# Save output files
train.to_csv("train_2021_2024.csv", index=False)
test.to_csv("test_2025.csv", index=False