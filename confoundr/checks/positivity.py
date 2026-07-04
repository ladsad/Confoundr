import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ..base import BaseCheck
from ..schemas import CheckContext, CheckResult, CheckStatus, Severity


class PositivityCheck(BaseCheck):
    """
    Checks the positivity assumption by calculating propensity scores 
    and ensuring sufficient overlap between the treated and control groups.
    If groups are perfectly separated, causal inference is impossible.
    """
    
    def __init__(self, overlap_threshold: float = 0.05):
        # We flag a failure if the overlap of propensity scores is less than 5% of the range
        self.overlap_threshold = overlap_threshold
        
    @property
    def name(self) -> str:
        return "Positivity (Overlap) Check"
        
    @property
    def default_severity(self) -> Severity:
        return Severity.HIGH

    def run(self, context: CheckContext) -> CheckResult:
        df = context.df
        treatment_col = context.treatment_col
        
        if not treatment_col or treatment_col not in df.columns:
            return self._create_result(CheckStatus.ERROR, "Treatment column not specified or not found.")
            
        features = context.feature_cols
        if not features:
            features = [c for c in df.columns if c not in [context.target_col, treatment_col, context.time_col]]
            
        # Drop rows with missing values for simple propensity scoring
        analysis_df = df[features + [treatment_col]].dropna()
        if len(analysis_df) < 20:
             return self._create_result(CheckStatus.ERROR, "Insufficient complete rows to estimate propensity scores.")
             
        X = analysis_df[features].select_dtypes(include=[np.number])
        if X.empty:
            return self._create_result(CheckStatus.ERROR, "No numeric features available to calculate propensity scores.")
            
        y = analysis_df[treatment_col]
        # Binarize treatment just in case
        if len(y.unique()) != 2:
            return self._create_result(CheckStatus.ERROR, f"Treatment column '{treatment_col}' must be binary.")
            
        y_binary = (y == y.unique()[0]).astype(int)
        
        # Estimate Propensity Scores
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            clf = LogisticRegression(penalty=None, solver='lbfgs', max_iter=1000)
            clf.fit(X_scaled, y_binary)
            # Propensity score is the probability of being in treatment group (y_binary=1)
            propensity_scores = clf.predict_proba(X_scaled)[:, 1]
        except Exception as e:
            return self._create_result(CheckStatus.ERROR, f"Failed to calculate propensity scores: {str(e)}")
            
        analysis_df = analysis_df.assign(_propensity_score=propensity_scores, _treatment_binary=y_binary)
        
        # Check overlap
        ps_treated = analysis_df[analysis_df['_treatment_binary'] == 1]['_propensity_score']
        ps_control = analysis_df[analysis_df['_treatment_binary'] == 0]['_propensity_score']
        
        if len(ps_treated) == 0 or len(ps_control) == 0:
            return self._create_result(CheckStatus.ERROR, "Missing either treatment or control groups.")
            
        min_treated, max_treated = ps_treated.min(), ps_treated.max()
        min_control, max_control = ps_control.min(), ps_control.max()
        
        # Overlap region
        overlap_min = max(min_treated, min_control)
        overlap_max = min(max_treated, max_control)
        
        overlap_width = max(0, overlap_max - overlap_min)
        total_range = max(max_treated, max_control) - min(min_treated, min_control)
        
        overlap_ratio = overlap_width / total_range if total_range > 0 else 0
        
        evidence = {
            "treated_min": round(min_treated, 4),
            "treated_max": round(max_treated, 4),
            "control_min": round(min_control, 4),
            "control_max": round(max_control, 4),
            "overlap_ratio": round(overlap_ratio, 4)
        }
        
        if overlap_ratio < self.overlap_threshold:
            explanation = (f"Severe positivity violation. The propensity score distributions for treated "
                           f"and control groups have virtually no overlap (overlap ratio: {overlap_ratio:.2%}). "
                           f"Treated range: [{min_treated:.2f}, {max_treated:.2f}], Control range: [{min_control:.2f}, {max_control:.2f}].")
            return self._create_result(CheckStatus.FAIL, explanation, evidence=evidence)
            
        explanation = f"Positivity assumption holds. Satisfactory overlap in propensity scores (overlap ratio: {overlap_ratio:.2%})."
        return self._create_result(CheckStatus.PASS, explanation, evidence=evidence)
