import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv("dataset/cardio_data.csv", sep=";")

for col in df.columns:
    if df[col].dtype in ["int64", "float64"]:
        df[col] = df[col].fillna(df[col].median())
    else:
        df[col] = df[col].fillna(df[col].mode()[0])

for col in df.select_dtypes(include="object").columns:
    df[col] = LabelEncoder().fit_transform(df[col])

train, test = train_test_split(df, test_size=0.2, random_state=42)
train.to_csv("processed/train.csv", index=False)
test.to_csv("processed/test.csv", index=False)

print("Cleaned data saved to processed/")