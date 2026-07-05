from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io

import os
from rq import Queue
from redis import Redis
from rq.job import Job

from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.leakage import TargetLeakageCheck
from confoundr.checks.confounder import ConfounderAuditCheck
from confoundr.checks.positivity import PositivityCheck
from .jobs import run_causal_checks

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)
job_queue = Queue(connection=redis_conn)

app = FastAPI(
    title="Confoundr API",
    description="API for Confoundr Causal Validity Checks (Sync + Async)",
    version="0.2.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/v1/check")
async def run_checks(
    file: UploadFile = File(...),
    target_col: str = Form(...),
    treatment_col: str = Form(None),
):
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.parquet') or filename.endswith('.json')):
        raise HTTPException(status_code=400, detail="Only CSV, Parquet, and JSON files are supported.")
        
    try:
        contents = await file.read()
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith('.parquet'):
            df = pd.read_parquet(io.BytesIO(contents))
        elif filename.endswith('.json'):
            df = pd.read_json(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
        
    if target_col not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{target_col}' not found in the dataset.")
        
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
            results.append({
                "check_name": res.check_name,
                "status": res.status.value,
                "severity": res.severity.value,
                "explanation": res.explanation,
                "evidence": res.evidence
            })
        except Exception as e:
            results.append({
                "check_name": check.name,
                "status": CheckStatus.ERROR.value,
                "severity": check.default_severity.value,
                "explanation": f"Check failed to execute: {str(e)}",
                "evidence": {}
            })
            
    return JSONResponse(content={"results": results})

@app.post("/api/v1/async-check")
async def run_checks_async(
    file: UploadFile = File(...),
    target_col: str = Form(...),
    treatment_col: str = Form(None),
):
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.parquet') or filename.endswith('.json')):
        raise HTTPException(status_code=400, detail="Only CSV, Parquet, and JSON files are supported.")
        
    contents = await file.read()
    
    # Enqueue the background job
    job = job_queue.enqueue(
        run_causal_checks,
        contents,
        filename,
        target_col,
        treatment_col,
        job_timeout='10m',
        result_ttl=86400 # keep result for 24h
    )
    
    return JSONResponse(status_code=202, content={
        "message": "Job accepted for processing.",
        "job_id": job.id,
        "status": job.get_status()
    })

@app.get("/api/v1/job/{job_id}")
def get_job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "job_id": job.id,
        "status": job.get_status(),
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "ended_at": job.ended_at.isoformat() if job.ended_at else None,
    }
    
    if job.is_finished:
        response["results"] = job.result
    elif job.is_failed:
        response["error"] = str(job.exc_info)
        
    return JSONResponse(content=response)
