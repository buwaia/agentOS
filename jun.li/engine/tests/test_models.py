import pytest
from pydantic import ValidationError
from src.models import UnderstandPayload, OrientPayload, CandidatePath, SolvePayload, SolveStep


def test_understand_payload_requires_solve_goal():
    with pytest.raises(ValidationError):
        UnderstandPayload(
            stage="UNDERSTAND",
            problem_type="algebra",
            known_conditions=["a > 0"],
            confidence=0.9,
        )


def test_understand_payload_confidence_clamped():
    p = UnderstandPayload(
        stage="UNDERSTAND",
        problem_type="algebra",
        known_conditions=["a > 0"],
        solve_goal="求最大值",
        confidence=1.5,
    )
    assert p.confidence <= 1.0


def test_orient_payload_requires_min_two_paths():
    with pytest.raises(ValidationError):
        OrientPayload(
            stage="ORIENT",
            candidate_paths=[
                CandidatePath(path_id="p1", description="路径1", intuition_basis="半圆")
            ],
            selected_path_id="p1",
            selection_rationale="几何直觉",
        )


def test_candidate_path_intuition_basis_required():
    with pytest.raises(ValidationError):
        CandidatePath(path_id="p1", description="路径1", intuition_basis="")


def test_solve_step_reason_required():
    with pytest.raises(ValidationError):
        SolveStep(step=1, expression="x=1", reason="")
