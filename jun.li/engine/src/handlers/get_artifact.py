from fastapi import APIRouter, HTTPException
from src.models import Stage
from src.db import get_artifact

router = APIRouter()


@router.get("/jobs/{job_id}/artifacts/{stage}")
def get_artifact_handler(job_id: str, stage: Stage):
    item = get_artifact(job_id, stage.value)
    if not item:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} 的 {stage} 阶段产出物不存在",
            },
        )
    return item
