import pandas as pd
import os

# Directories
INTERIM_DIR = 'data/interim'
CLEAN_DIR = 'data/clean'

# Create directories if missing
os.makedirs(INTERIM_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)

# Load data
ercot = pd.read_csv(f"{INTERIM_DIR}/ercot_merge.csv")
texas = pd.read_csv(f"{INTERIM_DIR}/texas_merge.csv")

# Datetime unify
ercot['DATE'] = pd.to_datetime(ercot['Hour Ending'])
texas['DATE'] = pd.to_datetime(texas['DATE'])

# Drop unnecessary regional load columns
drop_cols = ['COAST','EAST','FWEST','NORTH','NCENT','SOUTH','SCENT','WEST']
ercot = ercot.drop(columns=drop_cols)

# Merge ERCOT and weather data
df = ercot.merge(texas, on='DATE', how='inner')

# Remove duplicate datetime column
df = df.drop(columns=['Hour Ending'])

# Move DATE to the front
cols = ['DATE'] + [c for c in df.columns if c != 'DATE']
df = df[cols]

# Sort by datetime
df = df.sort_values('DATE').reset_index(drop=True)

# Train/Test split
train = df[df['year'] <= 2024].copy()
test  = df[df['year'] == 2025].copy()

# Save output files
train.to_csv(f"{CLEAN_DIR}/train_2021_2024.csv", index=False)
test.to_csv(f"{CLEAN_DIR}/test_2025.csv", index=False)

print("Saved to data/clean/")