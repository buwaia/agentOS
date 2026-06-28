import pytest
from moto import mock_aws
from src.db import get_job, put_job_meta, update_job_stage, put_artifact, get_artifact


@mock_aws
def test_put_and_get_job(dynamodb_table):
    put_job_meta("job-001", "证明 AM-GM", "running", "UNDERSTAND", "2026-06-28T09:00:00Z")
    result = get_job("job-001")
    assert result is not None
    assert result["job_id"] == "job-001"
    assert result["status"] == "running"
    assert result["current_stage"] == "UNDERSTAND"


@mock_aws
def test_get_job_not_found(dynamodb_table):
    result = get_job("nonexistent")
    assert result is None


@mock_aws
def test_update_job_stage_success(dynamodb_table):
    put_job_meta("job-002", "题目", "running", "UNDERSTAND", "2026-06-28T09:00:00Z")
    update_job_stage("job-002", "UNDERSTAND", "ORIENT", "waiting_approval", "2026-06-28T09:01:00Z")
    result = get_job("job-002")
    assert result["current_stage"] == "ORIENT"
    assert result["status"] == "waiting_approval"


@mock_aws
def test_update_job_stage_conflict(dynamodb_table):
    from botocore.exceptions import ClientError
    put_job_meta("job-003", "题目", "running", "UNDERSTAND", "2026-06-28T09:00:00Z")
    with pytest.raises(ClientError, match="ConditionalCheckFailedException"):
        update_job_stage("job-003", "ORIENT", "SOLVE", "running", "2026-06-28T09:01:00Z")


@mock_aws
def test_put_and_get_artifact(dynamodb_table):
    put_job_meta("job-004", "题目", "running", "UNDERSTAND", "2026-06-28T09:00:00Z")
    payload = {"solve_goal": "证明不等式", "confidence": 0.95}
    put_artifact("job-004", "UNDERSTAND", payload, "2026-06-28T09:00:00Z")
    result = get_artifact("job-004", "UNDERSTAND")
    assert result["payload"]["solve_goal"] == "证明不等式"


@mock_aws
def test_put_and_query_distill_events(dynamodb_table):
    from src.db import put_distill_event, query_distill_events
    put_distill_event("2026-06-28", "job-abc", "G3_FAILED", {
        "problem_type": "proof",
        "failed_field": "intuition_explanation",
    })
    events = query_distill_events("2026-06-28")
    assert len(events) == 1
    assert events[0]["event"] == "G3_FAILED"
    assert events[0]["payload"]["problem_type"] == "proof"
