from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter
from src.models import CreateJobRequest, Job, Stage, JobStatus, UnderstandPayload
from src.db import put_job_meta, put_artifact, update_job_stage, put_gate_record, get_job
from src.bedrock_client import understand_problem, BedrockError
from src.state_machine import check_g1, g1_next_stage

router = APIRouter()


@router.post("/jobs", status_code=201, response_model=Job)
def create_job(req: CreateJobRequest):
    job_id = f"job-{uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    put_job_meta(job_id, req.problem, JobStatus.RUNNING.value, Stage.UNDERSTAND.value, now, req.problem_type)

    try:
        bedrock_result = understand_problem(req.problem)
    except BedrockError as e:
        update_job_stage(job_id, Stage.UNDERSTAND.value, Stage.BLOCKED.value, JobStatus.BLOCKED.value, now)
        put_gate_record(job_id, "G1", {
            "gate": "G1", "type": "auto", "result": "failed",
            "comment": str(e), "checked_at": now,
        })
        return _load_job(job_id)

    put_artifact(job_id, Stage.UNDERSTAND.value, bedrock_result, now)

    payload = UnderstandPayload(stage=Stage.UNDERSTAND, **bedrock_result)
    failure = check_g1(payload)

    if failure:
        update_job_stage(job_id, Stage.UNDERSTAND.value, Stage.BLOCKED.value, JobStatus.BLOCKED.value, now)
        put_gate_record(job_id, "G1", {
            "gate": "G1", "type": "auto", "result": "failed",
            "comment": failure.reason, "checked_at": now,
        })
    else:
        next_stage, next_status = g1_next_stage(bedrock_result.get("problem_type", "other"))
        update_job_stage(job_id, Stage.UNDERSTAND.value, next_stage.value, next_status, now)
        put_gate_record(job_id, "G1", {
            "gate": "G1", "type": "auto", "result": "passed", "checked_at": now,
        })

    return _load_job(job_id)


def _load_job(job_id: str) -> Job:
    item = get_job(job_id)
    return Job(
        job_id=item["job_id"], problem=item["problem"],
        status=item["status"], current_stage=item["current_stage"],
        created_at=item["created_at"], updated_at=item["updated_at"],
    )
