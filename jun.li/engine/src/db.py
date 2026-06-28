import json
import os
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ["DYNAMODB_TABLE"]


def _to_decimal(obj):
    """Recursively convert float to Decimal for DynamoDB."""
    return json.loads(json.dumps(obj), parse_float=Decimal)


def _table():
    return boto3.resource("dynamodb").Table(TABLE_NAME)


def get_job(job_id: str) -> dict | None:
    result = _table().get_item(Key={"PK": f"JOB#{job_id}", "SK": "META"})
    return result.get("Item")


def put_job_meta(job_id: str, problem: str, status: str, stage: str, created_at: str, problem_type: str = "other") -> None:
    _table().put_item(Item={
        "PK": f"JOB#{job_id}",
        "SK": "META",
        "job_id": job_id,
        "problem": problem,
        "problem_type": problem_type,
        "status": status,
        "current_stage": stage,
        "created_at": created_at,
        "updated_at": created_at,
    })


def update_job_stage(job_id: str, expected_stage: str, new_stage: str, new_status: str, updated_at: str) -> None:
    _table().update_item(
        Key={"PK": f"JOB#{job_id}", "SK": "META"},
        UpdateExpression="SET current_stage = :ns, #st = :nst, updated_at = :ua",
        ConditionExpression="current_stage = :es",
        ExpressionAttributeNames={"#st": "status"},
        ExpressionAttributeValues={
            ":ns": new_stage,
            ":nst": new_status,
            ":ua": updated_at,
            ":es": expected_stage,
        },
    )


def put_artifact(job_id: str, stage: str, payload: dict, created_at: str) -> None:
    _table().put_item(Item={
        "PK": f"JOB#{job_id}",
        "SK": f"ARTIFACT#{stage}",
        "stage": stage,
        "payload": _to_decimal(payload),
        "created_at": created_at,
    })


def get_artifact(job_id: str, stage: str) -> dict | None:
    result = _table().get_item(Key={"PK": f"JOB#{job_id}", "SK": f"ARTIFACT#{stage}"})
    return result.get("Item")


def put_gate_record(job_id: str, gate: str, record: dict) -> None:
    _table().put_item(Item={
        "PK": f"JOB#{job_id}",
        "SK": f"GATE#{gate}",
        **record,
    })


def get_gate_records(job_id: str) -> list[dict]:
    result = _table().query(
        KeyConditionExpression=Key("PK").eq(f"JOB#{job_id}") & Key("SK").begins_with("GATE#")
    )
    return sorted(result.get("Items", []), key=lambda x: x.get("checked_at", ""))


def list_jobs() -> list[dict]:
    result = _table().scan(
        FilterExpression="SK = :meta",
        ExpressionAttributeValues={":meta": "META"},
    )
    items = result.get("Items", [])
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def get_all_job_data(job_id: str) -> list[dict]:
    result = _table().query(KeyConditionExpression=Key("PK").eq(f"JOB#{job_id}"))
    return result.get("Items", [])


def put_distill_event(date: str, job_id: str, event: str, payload: dict) -> None:
    from datetime import datetime, timezone
    _table().put_item(Item={
        "PK": f"DISTILL#{date}",
        "SK": f"{job_id}#{event}",
        "job_id": job_id,
        "event": event,
        "payload": _to_decimal(payload),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })


def query_distill_events(date: str) -> list[dict]:
    result = _table().query(
        KeyConditionExpression=Key("PK").eq(f"DISTILL#{date}")
    )
    return result.get("Items", [])
