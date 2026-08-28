
"""
clean_data.py
-------------
Person A (ML Model)

Cleans and splits the cardiovascular dataset.

Pipeline:
1. Load raw cardiovascular dataset
2. Remove unnecessary ID from model features
3. Remove physiologically impossible rows
4. Split into train/test
5. Calculate imputation values ONLY from training data
6. Apply the same imputation values to train and test
7. Save processed datasets
8. Save imputation values for production/prediction
"""

import pandas as pd
from sklearn.model_selection import train_test_split


# ============================================================
# 1. LOAD DATASET
# ============================================================

df = pd.read_csv("dataset/cardio_data.csv", sep=";")

print(f"Original dataset shape: {df.shape}")


# ============================================================
# 2. DEFINE MODEL FEATURES + TARGET
# ============================================================

FEATURES = [
    "age",
    "gender",
    "height",
    "weight",
    "ap_hi",
    "ap_lo",
    "cholesterol",
    "gluc",
    "smoke",
    "alco",
    "active"
]

TARGET = "cardio"


# Keep only features required by the ML model + target
df = df[FEATURES + [TARGET]]


# ============================================================
# 3. REMOVE PHYSIOLOGICALLY IMPOSSIBLE ROWS
# ============================================================

original_count = len(df)

# Blood pressure:
# systolic: 80–250
# diastolic: 40–200
# diastolic must be lower than systolic

df = df[
    (df["ap_hi"] >= 80)
    & (df["ap_hi"] <= 250)
    & (df["ap_lo"] >= 40)
    & (df["ap_lo"] <= 200)
    & (df["ap_lo"] < df["ap_hi"])
]

# Height / weight:
# Clearly impossible values are removed.

df = df[
    (df["height"] >= 100)
    & (df["height"] <= 220)
    & (df["weight"] >= 30)
    & (df["weight"] <= 200)
]

removed_count = original_count - len(df)

print(
    f"Removed {removed_count} rows with impossible values "
    f"({removed_count / original_count * 100:.1f}% of data)"
)

print(f"Remaining rows: {len(df)}")


# ============================================================
# 4. TRAIN / TEST SPLIT
# ============================================================

train, test = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=df[TARGET]
)

print(f"Training rows: {len(train)}")
print(f"Testing rows: {len(test)}")


# ============================================================
# 5. IMPUTATION
# ============================================================
# IMPORTANT:
# Calculate imputation values ONLY from training data.
#
# This prevents data leakage.
#
# The same values will later be used for:
# - test data
# - extracted medical reports
# - consolidated patient profiles
# ============================================================

imputation_values = {}

for col in FEATURES:

    # All current dataset features are numeric.
    # Median is therefore used for missing values.

    if pd.api.types.is_numeric_dtype(train[col]):

        value = train[col].median()

    else:

        value = train[col].mode()[0]

    imputation_values[col] = value

    train[col] = train[col].fillna(value)
    test[col] = test[col].fillna(value)


# ============================================================
# 6. SAVE PROCESSED DATA
# ============================================================

train.to_csv(
    "processed/train.csv",
    index=False
)

test.to_csv(
    "processed/test.csv",
    index=False
)


# ============================================================
# 7. SAVE IMPUTATION VALUES
# ============================================================
# risk_model.py / prediction pipeline can load this file later.
#
# Example:
# If glucose is missing from a medical report,
# use the training-data glucose median saved here.
# ============================================================

imputation_df = pd.DataFrame(
    {
        "feature": list(imputation_values.keys()),
        "imputation_value": list(imputation_values.values())
    }
)

imputation_df.to_csv(
    "processed/imputation_values.csv",
    index=False
)


# ============================================================
# 8. FINAL OUTPUT
# ============================================================

print("\n========================================")
print("DATA CLEANING COMPLETED SUCCESSFULLY")
print("========================================")

print("Saved files:")
print("  processed/train.csv")
print("  processed/test.csv")
print("  processed/imputation_values.csv")

print("\nModel features:")
print(FEATURES)

print(f"\nTarget: {TARGET}")
