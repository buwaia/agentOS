import os
import pytest
import boto3
from moto import mock_aws

os.environ["DYNAMODB_TABLE"] = "delivery-engine-jobs"
os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-sonnet-4-6"
os.environ["CONFIDENCE_THRESHOLD"] = "0.8"
os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"


@pytest.fixture
def dynamodb_table():
    with mock_aws():
        client = boto3.client("dynamodb", region_name="ap-northeast-1")
        client.create_table(
            TableName="delivery-engine-jobs",
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield boto3.resource("dynamodb", region_name="ap-northeast-1").Table(
            "delivery-engine-jobs"
        )


@pytest.fixture
def client(dynamodb_table):
    from fastapi.testclient import TestClient
    from src.app import app
    with TestClient(app) as c:
        yield c
