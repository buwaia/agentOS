# Delivery Engine — 基础设施设计

> 日期：2026-06-28
> 依赖：架构设计文档（2026-06-28-architecture-design.md）

---

## AWS 资源全景

```
┌─────────────────────────────────────────────────────────────┐
│  Region: ap-northeast-1                                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API Gateway (HTTP API)                              │    │
│  │  https://{id}.execute-api.ap-northeast-1.amazonaws  │    │
│  │                                                      │    │
│  │  POST   /jobs                → Lambda: create-job   │    │
│  │  GET    /jobs/{id}           → Lambda: get-job      │    │
│  │  POST   /jobs/{id}/advance   → Lambda: advance      │    │
│  │  POST   /jobs/{id}/approve   → Lambda: approve      │    │
│  │  GET    /jobs/{id}/artifacts → Lambda: get-artifact │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Lambda Functions (Python 3.12, ARM64)               │    │
│  │                                                      │    │
│  │  create-job      128MB   30s timeout                 │    │
│  │  get-job          128MB   10s timeout                │    │
│  │  advance         256MB   60s timeout  (G3校验较重)   │    │
│  │  approve         128MB   10s timeout                 │    │
│  │  get-artifact    128MB   10s timeout                 │    │
│  └────────┬────────────────────────┬────────────────────┘   │
│           │                        │                         │
│  ┌────────▼───────┐    ┌───────────▼──────────────────┐    │
│  │   DynamoDB      │    │  Bedrock (Claude Sonnet 4.6) │    │
│  │   (단일 테이블)  │    │  ap-northeast-1              │    │
│  │                │    │  仅 create-job Lambda 调用    │    │
│  └────────────────┘    └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## DynamoDB 表设计

**表名**：`delivery-engine-jobs`
**Billing**：PAY_PER_REQUEST（按量计费，初期流量不稳定）
**单表设计**，三类实体共用一张表。

### 主键结构

| 属性 | 类型 | 说明 |
|------|------|------|
| `PK` | String | 分区键 |
| `SK` | String | 排序键 |

### 数据模式

**Job 元信息**
```
PK: JOB#{job_id}
SK: META

属性：
  job_id        String
  problem       String   (原始题目文本)
  problem_type  String
  status        String   (running | waiting_approval | blocked | done)
  current_stage String   (UNDERSTAND | ORIENT | SOLVE | VERIFY | DONE | BLOCKED)
  created_at    String   (ISO 8601)
  updated_at    String
```

**阶段产出物**
```
PK: JOB#{job_id}
SK: ARTIFACT#{stage}     例：ARTIFACT#UNDERSTAND

属性：
  stage         String
  payload       Map      (各阶段 JSON 产出物)
  created_at    String
```

**Gate 记录**
```
PK: JOB#{job_id}
SK: GATE#{gate}          例：GATE#G1

属性：
  gate          String   (G1 | G2 | G3 | G4)
  type          String   (auto | manual)
  result        String   (passed | failed)
  reviewer_id   String   (G2 专用)
  comment       String
  checked_at    String
```

### 访问模式

| 操作 | 访问模式 |
|------|---------|
| 读 Job 状态 | `PK=JOB#{id}, SK=META` |
| 读某阶段产出物 | `PK=JOB#{id}, SK=ARTIFACT#{stage}` |
| 读所有 Gate 记录 | `PK=JOB#{id}, SK begins_with GATE#` |
| 读 Job 全部数据 | `PK=JOB#{id}`（一次查询取所有 SK）|

> 无需 GSI，所有访问模式都通过主键覆盖。符合 ADR-001 单表设计原则。

---

## Lambda 配置

### 运行时
- Python 3.12，ARM64（Graviton2，成本低约 20%）
- 代码层：FastAPI via Mangum 适配器（保持本地开发体验一致）

### IAM 角色权限（最小权限原则）

**所有 Lambda 共有**：
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem",
    "dynamodb:Query"
  ],
  "Resource": "arn:aws:dynamodb:*:*:table/delivery-engine-jobs"
}
```

**create-job Lambda 额外权限**：
```json
{
  "Effect": "Allow",
  "Action": ["bedrock:InvokeModel"],
  "Resource": "arn:aws:bedrock:ap-northeast-1::foundation-model/anthropic.claude-sonnet-4-6"
}
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `DYNAMODB_TABLE` | `delivery-engine-jobs` |
| `BEDROCK_MODEL_ID` | `anthropic.claude-sonnet-4-6` |
| `CONFIDENCE_THRESHOLD` | `0.8` |

---

## API Gateway 配置

**类型**：HTTP API（比 REST API 便宜 70%，功能够用）

### 路由映射

| 方法 | 路径 | Lambda | 鉴权 |
|------|------|--------|------|
| POST | /jobs | create-job | API Key |
| GET | /jobs/{job_id} | get-job | API Key |
| POST | /jobs/{job_id}/advance | advance | API Key |
| POST | /jobs/{job_id}/approve | approve | API Key |
| GET | /jobs/{job_id}/artifacts/{stage} | get-artifact | API Key |

**CORS**：允许前端域名（上线前配置具体域名，开发阶段允许 `*`）

**限流**：默认 10,000 req/s，初期无需调整

---

## 部署方式

**工具**：AWS SAM（Serverless Application Model）

```
engine/
├── template.yaml          SAM 模板（Lambda + API Gateway + DynamoDB）
├── src/
│   ├── handlers/
│   │   ├── create_job.py
│   │   ├── get_job.py
│   │   ├── advance.py
│   │   ├── approve.py
│   │   └── get_artifact.py
│   ├── state_machine.py   Gate 校验 + 状态转移逻辑
│   └── bedrock_client.py  Bedrock 调用封装
├── tests/
└── openapi.yaml           API 契约（对应 API Gateway 集成）
```

**部署命令**：
```bash
sam build
sam deploy --guided          # 首次
sam deploy                   # 后续
```

---

## 成本估算（初期）

| 资源 | 用量假设 | 月成本估算 |
|------|---------|-----------|
| Lambda | 10,000 次调用/月，avg 200ms | ~$0（免费额度内）|
| DynamoDB | 10,000 次读写/月 | ~$0（免费额度内）|
| API Gateway | 10,000 次请求/月 | ~$0.01 |
| Bedrock | 1,000 次 UNDERSTAND 调用 | ~$3（Claude Sonnet）|
| **合计** | | **~$3/月** |

> Bedrock 是唯一有实际成本的组件，符合 ADR-002 的预期代价（成本随调用量线性增长）。

---

## 不可逆决策（本文档新增）

### [ADR-004] HTTP API 而非 REST API
- **理由**：HTTP API 成本低 70%，功能（路由 + API Key 鉴权）完全够用
- **代价**：缺少 API Gateway 原生请求验证、Usage Plan 等高级功能
- **不可逆原因**：两者配置模型不同，迁移需要重建 Gateway

### [ADR-005] Lambda 内嵌 State Machine 而非 Step Functions
- **理由**：当前 Job 量小，G2 等待时间不定但无需精确监控，DynamoDB 存状态足够
- **代价**：状态转移逻辑散落在 Lambda 代码中，调试不如 Step Functions 直观
- **不可逆原因**：Step Functions 迁移需要重构所有状态转移逻辑
