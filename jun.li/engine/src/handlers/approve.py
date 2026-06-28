from datetime import datetime, timezone, date as _date
from fastapi import APIRouter, HTTPException
from src.models import ApproveRequest, Job, Stage, JobStatus
from src.db import get_job, update_job_stage, put_gate_record, put_distill_event

router = APIRouter()


@router.post("/jobs/{job_id}/approve", response_model=Job)
def approve_orient(job_id: str, req: ApproveRequest):
    now = datetime.now(timezone.utc).isoformat()

    item = get_job(job_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} 不存在"},
        )

    if item["status"] != JobStatus.WAITING_APPROVAL.value:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INVALID_APPROVAL_STATE",
                "message": f"Job 当前状态是 {item['status']}，不在等待审批",
            },
        )

    if req.approved:
        new_stage = Stage.SOLVE.value
        new_status = JobStatus.RUNNING.value
        result = "passed"
    else:
        new_stage = Stage.ORIENT.value
        new_status = JobStatus.RUNNING.value
        result = "failed"

    update_job_stage(job_id, Stage.ORIENT.value, new_stage, new_status, now)
    put_gate_record(job_id, "G2", {
        "gate": "G2", "type": "manual", "result": result,
        "reviewer_id": req.reviewer_id, "comment": req.comment, "checked_at": now,
    })

    put_distill_event(
        date=_date.today().isoformat(),
        job_id=job_id,
        event=f"G2_{'PASSED' if req.approved else 'REJECTED'}",
        payload={
            "approved": req.approved,
            "comment": req.comment or "",
            "problem": item.get("problem", "")[:100],
        },
    )

    item = get_job(job_id)
    return Job(
        job_id=item["job_id"], problem=item["problem"],
        status=item["status"], current_stage=item["current_stage"],
        created_at=item["created_at"], updated_at=item["updated_at"],
    )
