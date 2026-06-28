from fastapi import APIRouter, HTTPException
from src.models import Job, GateRecord
from src.db import get_job, get_gate_records

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=Job)
def get_job_handler(job_id: str):
    item = get_job(job_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} 不存在"},
        )
    gates = [GateRecord(**g) for g in get_gate_records(job_id)]
    return Job(
        job_id=item["job_id"],
        problem=item["problem"],
        status=item["status"],
        current_stage=item["current_stage"],
        gate_history=gates,
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )
