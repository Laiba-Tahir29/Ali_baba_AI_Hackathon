"""
train_model.py
---------------
Person A (ML Model) — trains a cardiovascular risk classifier on the
cleaned dataset (processed/train.csv, processed/test.csv from clean_data.py).

MODEL CHOICE: RandomForestClassifier
    - Good accuracy on tabular medical data without heavy tuning
    - Fast to train (seconds, not minutes) — good for hackathon iteration
    - Has built-in feature_importances_ — needed for predict_risk()'s
      top_factors output, without adding a separate explainability library
    - Handles the mix of binary (smoke/alco/active) and continuous
      (height/weight/ap_hi/ap_lo) features without scaling

Run this in Qoder Quest Mode (or directly) to train and save the model:
    python train_model.py
"""

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

# Feature order MUST match predict_risk.py's FEATURE_COLUMNS exactly —
# this is the columns from the dataset, excluding 'id' (not predictive)
# and 'cardio' (the target we're predicting).
FEATURE_COLUMNS = [
    "age", "gender", "height", "weight", "ap_hi", "ap_lo",
    "cholesterol", "gluc", "smoke", "alco", "active",
]
TARGET_COLUMN = "cardio"

MODEL_OUTPUT_PATH = "cardio_risk_model.pkl"


def load_data():
    train = pd.read_csv("processed/train.csv")
    test = pd.read_csv("processed/test.csv")
    return train, test


def train():
    train_df, test_df = load_data()

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,          # prevents overfitting on this dataset size
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,              # use all CPU cores — faster training
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("=" * 60)
    print("MODEL EVALUATION (on held-out test set)")
    print("=" * 60)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC:  {roc_auc_score(y_test, y_proba):.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    print("Feature importances (used for top_factors in predict_risk):")
    importances = sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )
    for name, importance in importances:
        print(f"  {name}: {importance:.4f}")

    joblib.dump(model, MODEL_OUTPUT_PATH)
    print(f"\nModel saved to {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    train()