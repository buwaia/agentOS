# Delivery Engine — 补充设计

> 日期：2026-06-28
> 补充三个代码生成缺口：Bedrock Prompt、SAM 模板、错误处理边界

---

## 一、Bedrock Prompt 设计

### 调用时机
仅在 `CreateJobHandler` 中调用一次，用于 UNDERSTAND 阶段。

### Prompt 模板

```
你是一个数学解题助手。请理解下面这道数学题，并以 JSON 格式返回分析结果。

题目：
{problem}

请返回以下 JSON，不要返回任何其他内容：
{
  "problem_type": "题目类型，从以下选项中选一个：algebra | geometry | function | inequality_proof | combinatorics | other",
  "known_conditions": ["已知条件1", "已知条件2", ...],
  "solve_goal": "用一句话说清楚要求什么，例如：证明 ln((a+b)/2) ≥ (ln a + ln b)/2",
  "confidence": 0.95,
  "confidence_reason": "简短说明为什么给这个置信度"
}

confidence 评分标准：
- 0.9-1.0：题目清晰，条件完整，求解目标明确
- 0.7-0.9：题目基本清晰，但有个别条件模糊或需要推断
- 0.5-0.7：题目有歧义，或关键条件缺失，理解存在不确定性
- 0.0-0.5：题目严重残缺或无法理解
```

### 返回解析逻辑

```python
import json, re

def parse_bedrock_response(response_text: str) -> dict:
    # 提取 JSON 块（防止 Claude 在 JSON 前后加说明文字）
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if not match:
        raise ValueError("Bedrock 返回内容不含 JSON")
    
    data = json.loads(match.group())
    
    # 校验必填字段
    required = ["problem_type", "known_conditions", "solve_goal", "confidence"]
    for field in required:
        if field not in data:
            raise ValueError(f"Bedrock 返回缺少字段: {field}")
    
    # confidence 强制在 [0, 1]
    data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
    
    return data
```

### Bedrock 调用配置

```python
BEDROCK_CONFIG = {
    "modelId": "anthropic.claude-sonnet-4-6",   # 从环境变量读取
    "max_tokens": 1024,
    "temperature": 0,   # 确定性输出，不需要创造性
}
```

> **为什么 temperature=0？**
> UNDERSTAND 阶段的输出是结构化数据，需要确定性，不需要创造性。
> 同一道题多次调用应该得到相同的 `problem_type` 和 `known_conditions`。

---

## 二、SAM template.yaml

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.12
    Architectures: [arm64]
    Environment:
      Variables:
        DYNAMODB_TABLE: !Ref JobsTable
        BEDROCK_MODEL_ID: !Ref BedrockModelId
        CONFIDENCE_THRESHOLD: "0.8"

Parameters:
  BedrockModelId:
    Type: String
    Default: "anthropic.claude-sonnet-4-6"

Resources:

  # ── DynamoDB ──────────────────────────────────────────────
  JobsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: delivery-engine-jobs
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE

  # ── IAM Role（共享）──────────────────────────────────────
  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DynamoDBAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:GetItem
                  - dynamodb:PutItem
                  - dynamodb:UpdateItem
                  - dynamodb:Query
                Resource: !GetAtt JobsTable.Arn

  BedrockAccessPolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: BedrockInvokeModel
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Action: bedrock:InvokeModel
            Resource: !Sub "arn:aws:bedrock:${AWS::Region}::foundation-model/${BedrockModelId}"
      Roles:
        - !Ref CreateJobFunctionRole

  # ── Lambda Functions ──────────────────────────────────────
  CreateJobFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/create_job.handler
      CodeUri: src/
      MemorySize: 128
      Timeout: 30
      Role: !GetAtt CreateJobFunctionRole.Arn
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref DeliveryEngineApi
            Method: POST
            Path: /jobs

  CreateJobFunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: DynamoDBAndBedrock
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action: [dynamodb:GetItem, dynamodb:PutItem, dynamodb:UpdateItem, dynamodb:Query]
                Resource: !GetAtt JobsTable.Arn
              - Effect: Allow
                Action: bedrock:InvokeModel
                Resource: !Sub "arn:aws:bedrock:${AWS::Region}::foundation-model/${BedrockModelId}"

  GetJobFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/get_job.handler
      CodeUri: src/
      MemorySize: 128
      Timeout: 10
      Role: !GetAtt LambdaExecutionRole.Arn
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref DeliveryEngineApi
            Method: GET
            Path: /jobs/{job_id}

  AdvanceFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/advance.handler
      CodeUri: src/
      MemorySize: 256
      Timeout: 60
      Role: !GetAtt LambdaExecutionRole.Arn
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref DeliveryEngineApi
            Method: POST
            Path: /jobs/{job_id}/advance

  ApproveFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/approve.handler
      CodeUri: src/
      MemorySize: 128
      Timeout: 10
      Role: !GetAtt LambdaExecutionRole.Arn
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref DeliveryEngineApi
            Method: POST
            Path: /jobs/{job_id}/approve

  GetArtifactFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/get_artifact.handler
      CodeUri: src/
      MemorySize: 128
      Timeout: 10
      Role: !GetAtt LambdaExecutionRole.Arn
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref DeliveryEngineApi
            Method: GET
            Path: /jobs/{job_id}/artifacts/{stage}

  # ── API Gateway ───────────────────────────────────────────
  DeliveryEngineApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      Auth:
        DefaultAuthorizer: ApiKeyAuthorizer
        ApiKeyRequired: true

Outputs:
  ApiEndpoint:
    Value: !Sub "https://${DeliveryEngineApi}.execute-api.${AWS::Region}.amazonaws.com"
  JobsTableName:
    Value: !Ref JobsTable
```

---

## 三、错误处理边界

### 错误分类

| 类型 | 场景 | HTTP 状态码 | 处理方式 |
|------|------|------------|---------|
| 客户端错误 | 请求体格式不合法 | 422 | 返回字段校验详情 |
| 状态冲突 | advance 的 stage 与当前 Job stage 不符 | 409 | 返回当前实际 stage |
| Gate 失败 | 自动 Gate 校验不通过 | 409 | 返回 GateFailure（具体原因）|
| 审批状态错误 | approve 时 Job 不在 waiting_approval | 409 | 返回当前状态 |
| 资源不存在 | job_id 不存在 | 404 | 返回 ErrorResponse |
| Bedrock 超时 | 调用超过 30s | 503 | Job 保持 UNDERSTAND 阶段，客户端重试 |
| Bedrock 返回异常 | 无法解析 JSON | 503 | Job 进入 blocked，附带 `error_reason` |
| DynamoDB 写入失败 | 网络抖动等 | 503 | 原子操作失败不改变 Job 状态，客户端重试 |

### 状态冲突检查（ConditionExpression）

每次写 DynamoDB 前，用条件写防止并发冲突：

```python
# advance 时校验当前 stage 符合预期
table.update_item(
    Key={"PK": f"JOB#{job_id}", "SK": "META"},
    UpdateExpression="SET current_stage = :new_stage, status = :status",
    ConditionExpression="current_stage = :expected_stage",
    ExpressionAttributeValues={
        ":new_stage": next_stage,
        ":status": "running",
        ":expected_stage": expected_stage,  # 客户端提交的 stage
    }
)
# 抛出 ConditionalCheckFailedException → 返回 409
```

### Bedrock 超时重试策略

```python
BEDROCK_RETRY = {
    "max_attempts": 3,
    "base_delay_seconds": 1,   # 1s → 2s → 4s 指数退避
}
# 3次全失败 → Job 进入 blocked，error_reason = "bedrock_timeout"
# 客户端轮询 GET /jobs/{id}，看到 blocked 后可手动重新触发
```

### 错误响应体格式

```json
{
  "code": "STAGE_MISMATCH",
  "message": "当前阶段是 ORIENT，不能提交 UNDERSTAND 产出物",
  "detail": {
    "expected_stage": "UNDERSTAND",
    "actual_stage": "ORIENT"
  }
}
```

### 错误码列表

| code | 含义 |
|------|------|
| `VALIDATION_ERROR` | 请求体字段缺失或格式错误 |
| `JOB_NOT_FOUND` | job_id 不存在 |
| `STAGE_MISMATCH` | 提交的 stage 与当前 Job stage 不符 |
| `GATE_FAILED` | 自动 Gate 校验不通过 |
| `INVALID_APPROVAL_STATE` | Job 不在 waiting_approval，不能审批 |
| `BEDROCK_ERROR` | Bedrock 调用失败或返回无法解析 |
| `INTERNAL_ERROR` | DynamoDB 或其他内部错误 |
