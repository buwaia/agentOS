import json
import pytest
from unittest.mock import patch, MagicMock
from src.bedrock_client import understand_problem, BedrockError

VALID_RESPONSE = json.dumps({
    "problem_type": "inequality_proof",
    "known_conditions": ["a > 0", "b > 0"],
    "solve_goal": "证明 ln((a+b)/2) ≥ (ln a + ln b)/2",
    "confidence": 0.95,
    "confidence_reason": "题目清晰",
})


def _mock_bedrock(response_text: str):
    mock = MagicMock()
    mock.invoke_model.return_value = {
        "body": MagicMock(read=lambda: json.dumps(
            {"content": [{"text": response_text}]}
        ).encode())
    }
    return mock


def test_understand_problem_success():
    with patch("src.bedrock_client._client", _mock_bedrock(VALID_RESPONSE)):
        result = understand_problem("证明 ln((a+b)/2) ≥ (ln a + ln b)/2")
    assert result["problem_type"] == "inequality_proof"
    assert result["confidence"] == 0.95
    assert len(result["known_conditions"]) == 2


def test_understand_problem_confidence_clamped():
    response = json.dumps({
        "problem_type": "algebra",
        "known_conditions": ["x > 0"],
        "solve_goal": "求最大值",
        "confidence": 1.5,
    })
    with patch("src.bedrock_client._client", _mock_bedrock(response)):
        result = understand_problem("求最大值")
    assert result["confidence"] == 1.0


def test_understand_problem_invalid_json_raises():
    with patch("src.bedrock_client._client", _mock_bedrock("这不是JSON")):
        with pytest.raises(BedrockError, match="返回内容不含 JSON"):
            understand_problem("题目")


def test_understand_problem_missing_field_raises():
    response = json.dumps({"problem_type": "algebra"})
    with patch("src.bedrock_client._client", _mock_bedrock(response)):
        with pytest.raises(BedrockError, match="缺少字段"):
            understand_problem("题目")
