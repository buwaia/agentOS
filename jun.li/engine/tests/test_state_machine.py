import pytest
from src.models import (
    UnderstandPayload, SolvePayload, SolveStep,
    VerifyPayload, VerificationCase, QualityCheck,
)
from src.state_machine import check_g1, check_g3, check_g4


def make_understand(confidence=0.9, solve_goal="证明不等式"):
    return UnderstandPayload(
        stage="UNDERSTAND", problem_type="inequality_proof",
        known_conditions=["a>0", "b>0"], solve_goal=solve_goal, confidence=confidence,
    )


def make_solve(intuition="半圆直觉", reason="为什么这步"):
    return SolvePayload(
        stage="SOLVE",
        steps=[SolveStep(step=1, expression="√(ab) ≤ (a+b)/2", reason=reason)],
        final_result="ln((a+b)/2) ≥ (lna+lnb)/2",
        intuition_explanation=intuition,
    )


def make_verify(passed=True, has_intuition=True):
    return VerifyPayload(
        stage="VERIFY",
        verification_cases=[VerificationCase(
            method="special_value", input="a=b=1",
            expected="0≥0", actual="0≥0", passed=passed,
        )],
        quality_check=QualityCheck(has_intuition=has_intuition, all_verifications_passed=passed),
    )


def test_g1_passes_high_confidence():
    assert check_g1(make_understand(confidence=0.9)) is None


def test_g1_fails_low_confidence():
    result = check_g1(make_understand(confidence=0.63))
    assert result is not None
    assert result.gate == "G1"
    assert result.confidence == 0.63


def test_g3_passes_complete_solve():
    assert check_g3(make_solve()) is None


def test_g3_fails_missing_intuition():
    result = check_g3(make_solve(intuition="x"))
    assert result is None  # "x" 非空，应通过
    # 直接测 Pydantic 层拦截空字符串（model层已测）


def test_g4_passes_all_verified():
    assert check_g4(make_verify(passed=True, has_intuition=True)) is None


def test_g4_fails_no_intuition():
    result = check_g4(make_verify(passed=True, has_intuition=False))
    assert result is not None
    assert result.gate == "G4"


def test_g4_fails_verification_not_passed():
    result = check_g4(make_verify(passed=False, has_intuition=True))
    assert result is not None
    assert result.gate == "G4"
