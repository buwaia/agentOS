from datetime import date as _date, datetime, timezone
from fastapi import APIRouter, HTTPException
from src.models import AdvanceRequest, Job, Stage
from src.db import get_job, put_artifact, update_job_stage, put_gate_record, put_distill_event
from src.models import GateLevel
from src.state_machine import next_stage_after_advance, GateFailedException, g1_next_stage

router = APIRouter()

GATE_MAP = {
    Stage.UNDERSTAND.value: "G1",
    Stage.SOLVE.value: "G3",
    Stage.VERIFY.value: "G4",
}


@router.post("/jobs/{job_id}/advance", response_model=Job)
def advance_stage(job_id: str, req: AdvanceRequest):
    now = datetime.now(timezone.utc).isoformat()

    item = get_job(job_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": f"Job {job_id} 不存在"},
        )

    current = item["current_stage"]
    if current == Stage.ORIENT.value:
        raise HTTPException(
            status_code=409,
            detail={"code": "STAGE_MISMATCH", "message": "ORIENT 阶段请使用 /approve 接口（G2 是人工门禁）"},
        )

    problem_type = item.get("problem_type", "other")
    try:
        new_stage, new_status = next_stage_after_advance(Stage(current), req.payload, problem_type)
    except GateFailedException as e:
        gate_name = GATE_MAP.get(current, current)
        is_l2 = e.failure.level == GateLevel.L2
        try:
            from src.db import get_artifact as _ga
            ua = _ga(job_id, "UNDERSTAND")
            put_distill_event(
                date=_date.today().isoformat(),
                job_id=job_id,
                event=f"{gate_name}_{'WARNING' if is_l2 else 'FAILED'}",
                payload={
                    "problem_type": (ua.get("payload", {}) if ua else {}).get("problem_type", "unknown"),
                    "gate": gate_name,
                    "reason": e.failure.reason,
                    "level": e.failure.level.value,
                },
            )
        except Exception:
            pass
        if is_l2:
            # L2 warning: continue to next stage, record warning gate
            gate = GATE_MAP.get(current)
            put_artifact(job_id, current, req.payload.model_dump(), now)
            update_job_stage(job_id, current, Stage.DONE.value, "done", now)
            if gate:
                put_gate_record(job_id, gate, {
                    "gate": gate, "type": "auto", "result": "warning",
                    "comment": e.failure.reason, "checked_at": now,
                })
            item = get_job(job_id)
            return Job(
                job_id=item["job_id"], problem=item["problem"],
                status=item["status"], current_stage=item["current_stage"],
                created_at=item["created_at"], updated_at=item["updated_at"],
            )
        raise HTTPException(status_code=409, detail=e.failure.model_dump())
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail={"code": "STAGE_MISMATCH", "message": str(e)},
        )

    gate = GATE_MAP.get(current)
    put_artifact(job_id, current, req.payload.model_dump(), now)
    update_job_stage(job_id, current, new_stage.value, new_status, now)
    if gate:
        put_gate_record(job_id, gate, {"gate": gate, "type": "auto", "result": "passed", "checked_at": now})

    # 写蒸馏事件
    understand_artifact = None
    try:
        from src.db import get_artifact
        ua = get_artifact(job_id, "UNDERSTAND")
        if ua:
            understand_artifact = ua.get("payload", {})
    except Exception:
        pass

    distill_event = f"{gate}_PASSED" if gate else f"{current}_DONE"
    put_distill_event(
        date=_date.today().isoformat(),
        job_id=job_id,
        event=distill_event,
        payload={
            "problem_type": (understand_artifact or {}).get("problem_type", "unknown"),
            "stage": current,
            "gate": gate,
        },
    )

    item = get_job(job_id)
    return Job(
        job_id=item["job_id"], problem=item["problem"],
        status=item["status"], current_stage=item["current_stage"],
        created_at=item["created_at"], updated_at=item["updated_at"],
    )
