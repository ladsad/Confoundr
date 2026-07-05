from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import io

from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.leakage import TargetLeakageCheck
from confoundr.checks.confounder import ConfounderAuditCheck
from confoundr.checks.positivity import PositivityCheck

app = FastAPI(
    title="Confoundr API",
    description="Synchronous API MVP for Confoundr Causal Validity Checks",
    version="0.1.0",
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
