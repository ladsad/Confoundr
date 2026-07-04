import pandas as pd
import numpy as np
from typing import Dict, List, Any

from ..base import BaseCheck
from ..schemas import CheckContext, CheckResult, CheckStatus, Severity


class TargetLeakageCheck(BaseCheck):
    """
    Detects potential target leakage by checking for suspiciously high 
    correlations between features and the target variable.
    """
    
    def __init__(self, correlation_threshold: float = 0.90):
        self.correlation_threshold = correlation_threshold
        
    @property
    def name(self) -> str:
        return "Target Leakage Detector"
        
    @property
    def default_severity(self) -> Severity:
        return Severity.CRITICAL

    def run(self, context: CheckContext) -> CheckResult:
        df = context.df
        target_col = context.target_col
        
        if target_col not in df.columns:
            return self._create_result(
                status=CheckStatus.ERROR,
                explanation=f"Target column '{target_col}' not found in dataframe."
            )
            
        features = context.feature_cols
        if not features:
            # Default to all other columns
            features = [c for c in df.columns if c != target_col and c != context.time_col]
            
        # Ensure we only check numeric features for correlation for now
        numeric_df = df[features + [target_col]].select_dtypes(include=[np.number])
        if target_col not in numeric_df.columns:
             # Target is not numeric. For a v0.1 we might need to handle categorical target 
             # by label encoding or similar.
             # Let's do a simple label encoding if it's not numeric and has < 100 unique values
             if df[target_col].nunique() < 100:
                 numeric_df[target_col] = pd.factorize(df[target_col])[0]
             else:
                 return self._create_result(
                     status=CheckStatus.ERROR,
                     explanation=f"Target column '{target_col}' is non-numeric and has too many unique values for simple correlation check."
                 )
                 
        leaky_features = []
        correlations = {}
        
        # Calculate correlations
        for feature in features:
            if feature in numeric_df.columns:
                corr = numeric_df[feature].corr(numeric_df[target_col])
                correlations[feature] = corr
                
                # Check absolute correlation
                if pd.notna(corr) and abs(corr) > self.correlation_threshold:
                    leaky_features.append({
                        "feature": feature,
                        "correlation": round(corr, 4)
                    })
                    
        if leaky_features:
            features_str = ", ".join([f"{item['feature']} ({item['correlation']})" for item in leaky_features])
            explanation = (f"Found {len(leaky_features)} features with suspiciously high correlation "
                           f"(> {self.correlation_threshold}) to the target '{target_col}', which may indicate target leakage. "
                           f"Leaky features: {features_str}")
            return self._create_result(
                status=CheckStatus.FAIL,
                explanation=explanation,
                evidence={"leaky_features": leaky_features, "all_correlations": correlations}
            )
            
        return self._create_result(
            status=CheckStatus.PASS,
            explanation=f"No features found with correlation higher than {self.correlation_threshold} to the target.",
            evidence={"all_correlations": correlations}
        )
