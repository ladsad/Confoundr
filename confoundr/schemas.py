from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import pandas as pd


class CheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CheckResult:
    """The standard output schema for any causal validity check."""
    check_name: str
    status: CheckStatus
    severity: Severity
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    
    def is_passed(self) -> bool:
        return self.status == CheckStatus.PASS


@dataclass
class CheckContext:
    """Context and configuration provided to a check when it runs."""
    df: pd.DataFrame
    target_col: str
    time_col: Optional[str] = None
    treatment_col: Optional[str] = None
    feature_cols: Optional[List[str]] = None
    config: Dict[str, Any] = field(default_factory=dict)
