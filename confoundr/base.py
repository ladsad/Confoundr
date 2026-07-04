from abc import ABC, abstractmethod
from typing import Any, Dict

from .schemas import CheckContext, CheckResult, CheckStatus, Severity

class BaseCheck(ABC):
    """
    Abstract base class for all causal validity checks.
    Any new check must inherit from this and implement the `run` method.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the check."""
        pass
        
    @property
    def default_severity(self) -> Severity:
        """The default severity if the check fails."""
        return Severity.HIGH
        
    @abstractmethod
    def run(self, context: CheckContext) -> CheckResult:
        """
        Execute the check against the provided context.
        
        Args:
            context (CheckContext): Data and metadata for the check.
            
        Returns:
            CheckResult: The outcome of the check, including pass/fail status and evidence.
        """
        pass
        
    def _create_result(self, 
                       status: CheckStatus, 
                       explanation: str, 
                       severity: Severity = None,
                       evidence: Dict[str, Any] = None) -> CheckResult:
        """Helper to create a CheckResult with the check's name."""
        return CheckResult(
            check_name=self.name,
            status=status,
            severity=severity or self.default_severity,
            explanation=explanation,
            evidence=evidence or {}
        )
