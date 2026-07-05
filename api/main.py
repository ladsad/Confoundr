from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import pandas as pd
import io

import os
from rq import Queue
from redis import Redis
from rq.job import Job
from sqlalchemy.orm import Session
from sqlalchemy import func
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.leakage import TargetLeakageCheck
from confoundr.checks.confounder import ConfounderAuditCheck
from confoundr.checks.positivity import PositivityCheck
from .jobs import run_causal_checks
import subprocess
import sys
from contextlib import asynccontextmanager

from .database import engine, get_db
from .models import Base, JobHistory

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = Redis.from_url(redis_url)
job_queue = Queue(connection=redis_conn)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database schema
    Base.metadata.create_all(bind=engine)
    
    # Start the worker process in the background when the API starts
    worker_process = subprocess.Popen([sys.executable, "-m", "api.worker"])
    yield
    # Terminate the worker when the API shuts down
    worker_process.terminate()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Confoundr API",
    description="API for Confoundr Causal Validity Checks (Sync + Async)",
    version="0.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Prometheus Metrics
QUEUE_DEPTH = Gauge('confoundr_queue_depth', 'Number of jobs currently waiting in the queue')
JOB_SUCCESS_COUNT = Gauge('confoundr_jobs_success_total', 'Total number of successfully finished jobs')
JOB_FAIL_COUNT = Gauge('confoundr_jobs_failed_total', 'Total number of failed jobs')
AVG_EXEC_TIME = Gauge('confoundr_avg_execution_time_seconds', 'Average execution time of jobs')

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """Expose Prometheus metrics for observability."""
    # 1. Get queue depth directly from Redis/RQ
    QUEUE_DEPTH.set(len(job_queue))
    
    # 2. Get historical stats from Postgres
    successes = db.query(JobHistory).filter(JobHistory.status == 'finished').count()
    failures = db.query(JobHistory).filter(JobHistory.status == 'failed').count()
    
    avg_time = db.query(func.avg(JobHistory.execution_time_seconds)).filter(JobHistory.status == 'finished').scalar()
    
    JOB_SUCCESS_COUNT.set(successes)
    JOB_FAIL_COUNT.set(failures)
    if avg_time:
        AVG_EXEC_TIME.set(float(avg_time))
        
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/api/v1/history")
def get_history(limit: int = 10, db: Session = Depends(get_db)):
    """Retrieve the most recent job executions and their causal validity results."""
    history = db.query(JobHistory).order_by(JobHistory.created_at.desc()).limit(limit).all()
    
    return JSONResponse(content={"history": [
        {
            "job_id": h.job_id,
            "filename": h.filename,
            "target_col": h.target_col,
            "treatment_col": h.treatment_col,
            "status": h.status,
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "execution_time_seconds": h.execution_time_seconds,
            "results": h.results
        } for h in history
    ]})

@app.post("/api/v1/check")
async def run_checks(
    file: UploadFile = File(...),
    target_col: str = Form(...),
    treatment_col: str = Form(None),
):
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
        
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
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")
        
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.parquet') or filename.endswith('.json')):
        raise HTTPException(status_code=400, detail="Only CSV, Parquet, and JSON files are supported.")
        
    contents = await file.read()
    
    # Enqueue the background job
    try:
        job = job_queue.enqueue(
            run_causal_checks,
            args=(contents, filename, target_col, treatment_col),
            job_timeout=300, # Strict 5-minute timeout for security
            result_ttl=86400
        )
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"Enqueue failed: {str(e)} - {traceback.format_exc()}")
    
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
