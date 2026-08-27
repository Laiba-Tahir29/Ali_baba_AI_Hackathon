"""
clean_data.py
--------------
Person A (ML Model) — cleans and splits the cardiovascular dataset.

UPDATE — OUTLIER FILTERING ADDED:
    The raw dataset (dataset/cardio_data.csv) contains ~1,365 rows (1.9%)
    with physiologically impossible values — this is a known issue with
    this dataset (negative blood pressure, ap_hi up to 16020, ap_lo >=
    ap_hi, etc.). These are almost certainly data-entry errors (e.g. a
    decimal point typo turning "120" into "1200"), not real patients.

    Training on these would let the model learn from garbage rows and
    could distort accuracy metrics. This version filters them out before
    the train/test split, using standard physiologically plausible ranges.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv("dataset/cardio_data.csv", sep=";")

original_count = len(df)

# --- Fill missing values (kept from original — dataset currently has none,
# but this stays as a safety net in case of future data updates) ---
for col in df.columns:
    if df[col].dtype in ["int64", "float64"]:
        df[col] = df[col].fillna(df[col].median())
    else:
        df[col] = df[col].fillna(df[col].mode()[0])

# --- Encode any text columns (kept from original — currently a no-op
# since all columns are already numeric, but harmless safety net) ---
for col in df.select_dtypes(include="object").columns:
    df[col] = LabelEncoder().fit_transform(df[col])

# --- Filter out physiologically impossible rows ---
# Blood pressure: systolic (ap_hi) 80-250, diastolic (ap_lo) 40-200,
# and diastolic must be less than systolic (a basic physiological fact).

df = df[
    (df["ap_hi"] >= 80) & (df["ap_hi"] <= 250) &
    (df["ap_lo"] >= 40) & (df["ap_lo"] <= 200) &
    (df["ap_lo"] < df["ap_hi"])
]

# Height/weight: filter out clearly impossible adult values.
df = df[
    (df["height"] >= 100) & (df["height"] <= 220) &
    (df["weight"] >= 30) & (df["weight"] <= 200)
]

removed_count = original_count - len(df)
print(f"Removed {removed_count} rows with impossible values "
      f"({removed_count / original_count * 100:.1f}% of data)")
print(f"Remaining rows: {len(df)}")

train, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["cardio"])
train.to_csv("processed/train.csv", index=False)
test.to_csv("processed/test.csv", index=False)

print("Cleaned data saved to processed/")