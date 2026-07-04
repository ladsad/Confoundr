import argparse
import sys
import pandas as pd
import json

from .schemas import CheckContext, CheckStatus
from .checks.leakage import TargetLeakageCheck
from .checks.confounder import ConfounderAuditCheck
from .checks.positivity import PositivityCheck


def main():
    parser = argparse.ArgumentParser(description="Confoundr: Causal Validity Linter")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    check_parser = subparsers.add_parser("check", help="Run checks on a dataset")
    check_parser.add_argument("data", help="Path to the CSV dataset")
    check_parser.add_argument("--target", required=True, help="Target column name")
    check_parser.add_argument("--treatment", help="Treatment column name (required for some checks)")
    check_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    
    args = parser.parse_args()
    
    if args.command == "check":
        try:
            df = pd.read_csv(args.data)
        except Exception as e:
            print(f"Error reading dataset: {e}", file=sys.stderr)
            sys.exit(1)
            
        context = CheckContext(
            df=df,
            target_col=args.target,
            treatment_col=args.treatment
        )
        
        checks = [
            TargetLeakageCheck(),
            ConfounderAuditCheck(),
            PositivityCheck()
        ]
        
        results = []
        all_passed = True
        
        for check in checks:
            # Note: In a real implementation we'd gracefully skip checks if dependencies aren't met
            # e.g., PositivityCheck needs a treatment_col
            if check.name in ["Confounder Audit", "Positivity (Overlap) Check"] and not args.treatment:
                continue
                
            res = check.run(context)
            results.append(res)
            if res.status != CheckStatus.PASS:
                all_passed = False
                
        if args.format == "json":
            output = [
                {
                    "check_name": r.check_name,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "explanation": r.explanation
                }
                for r in results
            ]
            print(json.dumps(output, indent=2))
        else:
            print("\n--- Confoundr Diagnostics ---\n" + "="*40)
            for r in results:
                icon = "[PASS]" if r.status == CheckStatus.PASS else ("[FAIL]" if r.status == CheckStatus.FAIL else "[WARN]")
                print(f"{icon} {r.check_name}")
                print(f"   {r.explanation}\n")
                
        sys.exit(0 if all_passed else 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
