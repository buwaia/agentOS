import json
import os
import re
import boto3

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-6")
_client = boto3.client(
    "bedrock-runtime",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1"),
)

PROMPT_TEMPLATE = """你是一个数学解题助手。请理解下面这道数学题，并以 JSON 格式返回分析结果。

题目：
{problem}

请返回以下 JSON，不要返回任何其他内容：
{{
  "problem_type": "algebra | geometry | function | inequality_proof | combinatorics | other 中选一个",
  "known_conditions": ["已知条件1", "已知条件2"],
  "solve_goal": "用一句话说清楚要求什么",
  "confidence": 0.95,
  "confidence_reason": "简短说明"
}}

confidence 评分标准：
- 0.9-1.0：题目清晰，条件完整，目标明确
- 0.7-0.9：基本清晰，个别条件模糊
- 0.5-0.7：有歧义或关键条件缺失
- 0.0-0.5：严重残缺或无法理解"""


class BedrockError(Exception):
    pass


def understand_problem(problem: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(problem=problem)
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    })

    last_error = None
    for attempt in range(3):
        try:
            response = _client.invoke_model(modelId=MODEL_ID, body=body)
            text = json.loads(response["body"].read())["content"][0]["text"]
            return _parse_response(text)
        except BedrockError:
            raise
        except Exception as e:
            last_error = e
            if attempt < 2:
                import time
                time.sleep(2 ** attempt)

    raise BedrockError(f"Bedrock 调用失败: {last_error}") from last_error


def _parse_response(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise BedrockError("返回内容不含 JSON")

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise BedrockError(f"JSON 解析失败: {e}") from e

    required = ["problem_type", "known_conditions", "solve_goal", "confidence"]
    for field in required:
        if field not in data:
            raise BedrockError(f"缺少字段: {field}")

    data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
    return data
