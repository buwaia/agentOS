"""Local dev server: real DynamoDB (us-east-1) + uvicorn."""
import os
import sys

# Point to real AWS DynamoDB
os.environ["DYNAMODB_TABLE"] = "DeliveryEngineLocal"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("[local] Using real DynamoDB table 'DeliveryEngineLocal' (us-east-1)")


def _mock_understand(problem: str) -> dict:
    print(f"[local] mock Bedrock: understand_problem called")
    return {
        "confidence": 0.95,
        "problem_type": "proof",
        "known_conditions": ["integers", "prime factorization", "rational definition"],
        "solve_goal": f"Prove or solve: {problem[:80]}",
    }


# Bedrock still mocked — real calls require additional setup
import src.bedrock_client as bc

bc.understand_problem = _mock_understand
print("[local] Bedrock patched with mock (no real AWS calls)")

import uvicorn
from src.app import app  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
