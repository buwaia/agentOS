import os
from src.models import (
    Stage, JobStatus, GateFailure, GateLevel,
    UnderstandPayload, SolvePayload, VerifyPayload,
)

CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.8"))

STAGE_TRANSITIONS = {
    Stage.UNDERSTAND: Stage.ORIENT,
    Stage.ORIENT: Stage.SOLVE,
    Stage.SOLVE: Stage.VERIFY,
    Stage.VERIFY: Stage.DONE,
}

PROFILE_MAP = {
    "inequality_proof": "proof",
    "combinatorics":    "proof",
    "geometry":         "proof",
    "algebra":          "calculation",
    "function":         "calculation",
    "shortanswer":      "shortanswer",
    "other":            "calculation",
}


def get_profile(problem_type: str) -> str:
    return PROFILE_MAP.get(problem_type, "calculation")


def g1_next_stage(problem_type: str) -> tuple[Stage, str]:
    """After G1 passes, determine next stage based on profile."""
    profile = get_profile(problem_type)
    if profile == "shortanswer":
        return Stage.SOLVE, JobStatus.RUNNING.value
    return Stage.ORIENT, JobStatus.WAITING_APPROVAL.value


def check_g1(payload: UnderstandPayload) -> GateFailure | None:
    if payload.confidence < CONFIDENCE_THRESHOLD:
        return GateFailure(
            gate="G1",
            reason=f"confidence {payload.confidence} < {CONFIDENCE_THRESHOLD}",
            confidence=payload.confidence,
            action="标记 BLOCKED，等待人工确认题目理解",
        )
    return None


def check_g3(payload: SolvePayload) -> GateFailure | None:
    if not payload.intuition_explanation:
        return GateFailure(
            gate="G3",
            reason="intuition_explanation 为空",
            action="补充函数结果的直觉解释后重新提交（R5）",
        )
    for step in payload.steps:
        if not step.reason:
            return GateFailure(
                gate="G3",
                reason=f"第 {step.step} 步缺少 reason",
                action="每步推导必须说明原因",
            )
    return None


def check_g4(payload: VerifyPayload) -> GateFailure | None:
    failed_cases = [c for c in payload.verification_cases if not c.passed]
    if failed_cases:
        return GateFailure(
            gate="G4",
            reason=f"{len(failed_cases)} 个验证用例未通过",
            action="修正推导后重新验证",
            level=GateLevel.L1,
        )
    if not payload.quality_check.has_intuition:
        return GateFailure(
            gate="G4",
            reason="quality_check.has_intuition = false，解析缺乏直觉描述（R001）",
            action="在解析中加入几何类比或直觉描述",
            level=GateLevel.L1,
        )
    if not payload.quality_check.has_story:
        # L2: warning only, job continues
        return GateFailure(
            gate="G4",
            reason="quality_check.has_story = false，解析缺乏故事性叙述",
            action="建议补充类比或故事性描述，但不阻断",
            level=GateLevel.L2,
        )
    return None


class GateFailedException(Exception):
    def __init__(self, failure: GateFailure):
        self.failure = failure


def next_stage_after_advance(current: Stage, payload, problem_type: str = "other") -> tuple[Stage, str]:
    if current == Stage.UNDERSTAND:
        failure = check_g1(payload)
        if failure:
            return Stage.BLOCKED, JobStatus.BLOCKED.value
        return g1_next_stage(problem_type)

    if current == Stage.SOLVE:
        failure = check_g3(payload)
        if failure:
            raise GateFailedException(failure)
        return Stage.VERIFY, JobStatus.RUNNING.value

    if current == Stage.VERIFY:
        failure = check_g4(payload)
        if failure:
            raise GateFailedException(failure)
        return Stage.DONE, JobStatus.DONE.value

    raise ValueError(f"阶段 {current} 不支持 advance（G2 走 /approve）")
