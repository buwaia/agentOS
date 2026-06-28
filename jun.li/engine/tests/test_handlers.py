import pytest
from moto import mock_aws
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

BEDROCK_RESULT = {
    "problem_type": "inequality_proof",
    "known_conditions": ["a > 0", "b > 0"],
    "solve_goal": "证明 ln((a+b)/2) ≥ (lna+lnb)/2",
    "confidence": 0.95,
}

LOW_CONFIDENCE_RESULT = {**BEDROCK_RESULT, "confidence": 0.5}


@pytest.mark.asyncio
@mock_aws
async def test_create_job_success(dynamodb_table):
    from src.app import app
    with patch("src.handlers.create_job.understand_problem", return_value=BEDROCK_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/jobs", json={"problem": "证明 AM-GM 不等式"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["current_stage"] == "ORIENT"
    assert data["status"] == "waiting_approval"
    assert "job_id" in data


@pytest.mark.asyncio
@mock_aws
async def test_create_job_low_confidence_blocked(dynamodb_table):
    from src.app import app
    with patch("src.handlers.create_job.understand_problem", return_value=LOW_CONFIDENCE_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/jobs", json={"problem": "模糊题目"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "blocked"
    assert resp.json()["current_stage"] == "BLOCKED"


@pytest.mark.asyncio
@mock_aws
async def test_get_job_not_found(dynamodb_table):
    from src.app import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/jobs/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
@mock_aws
async def test_approve_g2_pass(dynamodb_table):
    from src.app import app
    with patch("src.handlers.create_job.understand_problem", return_value=BEDROCK_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/jobs", json={"problem": "证明不等式"})
            job_id = create_resp.json()["job_id"]
            resp = await client.post(f"/jobs/{job_id}/approve", json={
                "approved": True, "reviewer_id": "teacher-001", "comment": "半圆几何，通过"
            })
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "SOLVE"
    assert resp.json()["status"] == "running"


@pytest.mark.asyncio
@mock_aws
async def test_approve_g2_reject(dynamodb_table):
    from src.app import app
    with patch("src.handlers.create_job.understand_problem", return_value=BEDROCK_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/jobs", json={"problem": "证明不等式"})
            job_id = create_resp.json()["job_id"]
            resp = await client.post(f"/jobs/{job_id}/approve", json={
                "approved": False, "reviewer_id": "teacher-001", "comment": "路径纯公式，退回"
            })
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "ORIENT"
    assert resp.json()["status"] == "running"


@pytest.mark.asyncio
@mock_aws
async def test_approve_wrong_state_returns_409(dynamodb_table):
    from src.app import app
    with patch("src.handlers.create_job.understand_problem", return_value=LOW_CONFIDENCE_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/jobs", json={"problem": "题目"})
            job_id = create_resp.json()["job_id"]
            resp = await client.post(f"/jobs/{job_id}/approve", json={
                "approved": True, "reviewer_id": "teacher-001"
            })
    assert resp.status_code == 409


@pytest.mark.asyncio
@mock_aws
async def test_advance_orient_returns_409(dynamodb_table):
    from src.app import app
    with patch("src.handlers.create_job.understand_problem", return_value=BEDROCK_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            create_resp = await client.post("/jobs", json={"problem": "题目"})
            job_id = create_resp.json()["job_id"]
            resp = await client.post(f"/jobs/{job_id}/advance", json={
                "stage": "ORIENT",
                "payload": {
                    "stage": "ORIENT",
                    "candidate_paths": [
                        {"path_id": "p1", "description": "路径1", "intuition_basis": "半圆"},
                        {"path_id": "p2", "description": "路径2", "intuition_basis": "代数"},
                    ],
                    "selected_path_id": "p1",
                    "selection_rationale": "半圆几何更直观",
                }
            })
    assert resp.status_code == 409


def test_advance_writes_distill_event_on_g3_pass(client, dynamodb_table):
    from src.db import query_distill_events
    from datetime import datetime, timezone
    # 先建一个处于 SOLVE 阶段的 job
    job_id = "job-distill-test"
    from src.db import put_job_meta, put_artifact
    now = datetime.now(timezone.utc).isoformat()
    put_job_meta(job_id, "test problem", "running", "SOLVE", now)
    put_artifact(job_id, "UNDERSTAND", {"confidence": 0.95, "problem_type": "proof",
        "known_conditions": [], "solve_goal": "test", "stage": "UNDERSTAND"}, now)

    resp = client.post(f"/jobs/{job_id}/advance", json={
        "stage": "SOLVE",
        "payload": {
            "stage": "SOLVE",
            "steps": [{"step": 1, "expression": "x=1", "reason": "because"}],
            "final_result": "done",
            "intuition_explanation": "key insight here",
        }
    })
    assert resp.status_code == 200

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = query_distill_events(today)
    g3_events = [e for e in events if "G3_PASSED" in e["SK"]]
    assert len(g3_events) == 1
    assert g3_events[0]["payload"]["problem_type"] == "proof"


def test_approve_writes_distill_event_on_g2(client, dynamodb_table):
    from src.db import query_distill_events
    from datetime import datetime, timezone
    job_id = "job-g2-distill"
    from src.db import put_job_meta
    now = datetime.now(timezone.utc).isoformat()
    put_job_meta(job_id, "prove something", "waiting_approval", "ORIENT", now)

    resp = client.post(f"/jobs/{job_id}/approve", json={
        "approved": True,
        "comment": "good intuition",
    })
    assert resp.status_code == 200

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = query_distill_events(today)
    g2_events = [e for e in events if "G2_PASSED" in e["SK"]]
    assert len(g2_events) == 1
