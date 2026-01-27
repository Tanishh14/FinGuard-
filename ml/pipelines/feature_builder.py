import pandas as pd

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build numerical features for anomaly detection
    Compatible with credit card fraud dataset
    """

    features = df.drop(columns=["Class"], errors="ignore")

    # Ensure numeric only
    features = features.select_dtypes(include=["number"])

    return features
