from __future__ import annotations
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, field_validator


class Stage(str, Enum):
    UNDERSTAND = "UNDERSTAND"
    ORIENT = "ORIENT"
    SOLVE = "SOLVE"
    VERIFY = "VERIFY"
    DONE = "DONE"
    BLOCKED = "BLOCKED"


class JobStatus(str, Enum):
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    DONE = "done"


class GateRecord(BaseModel):
    gate: str
    type: str
    result: str
    reviewer_id: str | None = None
    comment: str | None = None
    checked_at: str | None = None


class Job(BaseModel):
    job_id: str
    problem: str
    status: JobStatus
    current_stage: Stage
    gate_history: list[GateRecord] = []
    created_at: str
    updated_at: str


class CandidatePath(BaseModel):
    path_id: str
    description: str
    intuition_basis: Annotated[str, Field(min_length=1)]


class SolveStep(BaseModel):
    step: int
    expression: str
    reason: Annotated[str, Field(min_length=1)]


class VerificationCase(BaseModel):
    method: str
    input: str
    expected: str
    actual: str
    passed: bool


class QualityCheck(BaseModel):
    has_intuition: bool
    has_story: bool = False
    all_verifications_passed: bool


class UnderstandPayload(BaseModel):
    stage: Stage = Stage.UNDERSTAND
    problem_type: str
    known_conditions: Annotated[list[str], Field(min_length=1)]
    solve_goal: Annotated[str, Field(min_length=1)]
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


class OrientPayload(BaseModel):
    stage: Stage = Stage.ORIENT
    candidate_paths: Annotated[list[CandidatePath], Field(min_length=2)]
    selected_path_id: str
    selection_rationale: Annotated[str, Field(min_length=1)]


class SolvePayload(BaseModel):
    stage: Stage = Stage.SOLVE
    steps: Annotated[list[SolveStep], Field(min_length=1)]
    final_result: str
    intuition_explanation: Annotated[str, Field(min_length=1)]


class VerifyPayload(BaseModel):
    stage: Stage = Stage.VERIFY
    verification_cases: Annotated[list[VerificationCase], Field(min_length=1)]
    quality_check: QualityCheck


class CreateJobRequest(BaseModel):
    problem: Annotated[str, Field(min_length=1)]
    problem_type: str = "other"


class AdvanceRequest(BaseModel):
    stage: Stage
    payload: UnderstandPayload | OrientPayload | SolvePayload | VerifyPayload


class ApproveRequest(BaseModel):
    approved: bool
    reviewer_id: str | None = None
    comment: str | None = None


class GateLevel(str, Enum):
    L1 = "L1"  # hard block
    L2 = "L2"  # warning, continue
    L3 = "L3"  # human review


class GateFailure(BaseModel):
    gate: str
    reason: str
    confidence: float | None = None
    action: str
    level: GateLevel = GateLevel.L1


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict | None = None
