import pandas as pd
import io
import time
import sys

try:
    import resource
except ImportError:
    resource = None
from rq import get_current_job

from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.leakage import TargetLeakageCheck
from confoundr.checks.confounder import ConfounderAuditCheck
from confoundr.checks.positivity import PositivityCheck

from .database import SessionLocal
from .models import JobHistory
from .llm import generate_explanation

def run_causal_checks(file_bytes: bytes, filename: str, target_col: str, treatment_col: str = None):
    """
    Background job to run all causal validity checks on a dataset.
    """
    if resource:
        try:
            # Hard limit: 500 MB RAM and 300 CPU seconds per job to prevent DoS via malicious datasets
            max_mem = 500 * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_mem, max_mem))
            resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
        except ValueError:
            pass # Ignore if limits are already lower

    start_time = time.time()
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith('.parquet'):
            df = pd.read_parquet(io.BytesIO(file_bytes))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(file_bytes))
        else:
            raise ValueError("Unsupported file format.")
    except Exception as e:
        raise ValueError(f"Failed to parse file: {str(e)}")
        
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in the dataset.")
        
    context = CheckContext(
        df=df,
        target_col=target_col,
        treatment_col=treatment_col
    )
    
    checks = [
        TargetLeakageCheck(),
        ConfounderAuditCheck(),
        PositivityCheck()
    ]
    
    results = []
    
    for check in checks:
        if check.name in ["Confounder Audit", "Positivity (Overlap) Check"] and not treatment_col:
            continue
            
        try:
            res = check.run(context)
            
            ai_insight = None
            if res.status.value == "fail":
                ai_insight = generate_explanation(res.check_name, res.explanation, res.evidence)
                
            results.append({
                "check_name": res.check_name,
                "status": res.status.value,
                "severity": res.severity.value,
                "explanation": res.explanation,
                "evidence": res.evidence,
                "ai_insight": ai_insight
            })
        except Exception as e:
            results.append({
                "check_name": check.name,
                "status": CheckStatus.ERROR.value,
                "severity": check.default_severity.value,
                "explanation": f"Check failed to execute: {str(e)}",
                "evidence": {}
            })
            
    # Save to database
    end_time = time.time()
    job = get_current_job()
    if job:
        db = SessionLocal()
        try:
            history_record = JobHistory(
                job_id=job.id,
                filename=filename,
                target_col=target_col,
                treatment_col=treatment_col,
                status="finished",
                execution_time_seconds=end_time - start_time,
                results=results
            )
            db.add(history_record)
            db.commit()
        except Exception as e:
            print(f"Failed to save job {job.id} to db: {e}")
            db.rollback()
        finally:
            db.close()
            
    return results
