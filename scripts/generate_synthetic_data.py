import pandas as pd
import numpy as np
import os

def generate_datasets(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Clean dataset (Passes all checks)
    np.random.seed(42)
    n = 1000
    df_clean = pd.DataFrame({
        "age": np.random.normal(40, 10, n),
        "income": np.random.normal(60000, 15000, n),
        # Randomized treatment independent of features
        "treatment": np.random.randint(0, 2, n),
        # Target depends on features and treatment
        "target": np.random.randn(n)
    })
    df_clean.to_csv(f"{output_dir}/clean_dataset.csv", index=False)
    
    # 2. Leaky dataset
    np.random.seed(42)
    df_leaky = df_clean.copy()
    # Feature perfectly predicts the target (Target Leakage)
    df_leaky["target_proxy"] = df_leaky["target"] * 1.5 + np.random.normal(0, 0.1, n)
    df_leaky.to_csv(f"{output_dir}/leaky_dataset.csv", index=False)
    
    # 3. Confounded dataset
    np.random.seed(42)
    # Hidden confounder influences both treatment and target
    confounder = np.random.normal(0, 1, n)
    df_confounded = pd.DataFrame({
        "age": np.random.normal(40, 10, n),
        "hidden_confounder": confounder,
        "treatment": (confounder > 0).astype(int),
        "target": confounder * 3.0 + np.random.randn(n)
    })
    df_confounded.to_csv(f"{output_dir}/confounded_dataset.csv", index=False)
    
    # 4. Positivity violation dataset
    np.random.seed(42)
    feature = np.random.normal(0, 1, n)
    # Complete separation based on feature
    treatment = (feature > 0).astype(int)
    df_positivity = pd.DataFrame({
        "feature_1": feature,
        "treatment": treatment,
        "target": np.random.randn(n)
    })
    df_positivity.to_csv(f"{output_dir}/positivity_violation_dataset.csv", index=False)

if __name__ == "__main__":
    generate_datasets()
    print("Generated 4 synthetic benchmark datasets in data/")
