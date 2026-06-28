from fastapi import APIRouter
from src.models import Job
from src.db import list_jobs

router = APIRouter()


@router.get("/jobs", response_model=list[Job])
def list_jobs_handler():
    items = list_jobs()
    return [
        Job(
            job_id=item["job_id"],
            problem=item["problem"],
            status=item["status"],
            current_stage=item["current_stage"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
        )
        for item in items
    ]
