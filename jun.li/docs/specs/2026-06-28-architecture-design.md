# Delivery Engine — 架构设计

> 日期：2026-06-28

---

## 系统边界

```
外部调用者（前端 / 老师审批工具）
          │
          ▼
    ┌─────────────────────────────────────────┐
    │         Delivery Engine                  │
    │                                          │
    │  API 层 → 状态机层 → AI 推理层            │
    │                    ↕                     │
    │              持久化层                     │
    └─────────────────────────────────────────┘
```

引擎对外是一个黑盒：进去的是题目，出来的是经过 4 个 Gate 验证的解答。

---

## 组件图

```
┌──────────────────────────────────────────────────────────────┐
│                        外部调用者                             │
│         学生端（提交题目）     老师端（G2 审批）               │
└─────────────┬──────────────────────┬────────────────────────┘
              │                      │
              ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│   POST /jobs   GET /jobs/{id}   POST /advance   POST /approve│
└──────┬──────────────┬──────────────┬─────────────┬──────────┘
       │              │              │             │
       ▼              ▼              ▼             ▼
┌────────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐
│ CreateJob  │ │  GetJob    │ │ Advance  │ │   Approve    │
│  Handler   │ │  Handler   │ │ Handler  │ │   Handler    │
└─────┬──────┘ └─────┬──────┘ └────┬─────┘ └──────┬───────┘
      │              │             │              │
      └──────────────┴─────────────┴──────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌─────────────────┐      ┌─────────────────────┐
    │   State Machine  │      │    DynamoDB          │
    │                  │      │  (Job + Artifacts)   │
    │ UNDERSTAND        │      │                     │
    │   → ORIENT        │      │  PK: JOB#{job_id}   │
    │     → SOLVE       │      │  SK: META           │
    │       → VERIFY    │      │      ARTIFACT#{stage}│
    │         → DONE    │      │      GATE#{gate}     │
    └────────┬─────────┘      └─────────────────────┘
             │
             ▼ (UNDERSTAND 阶段)
    ┌─────────────────┐
    │  Bedrock         │
    │  (Claude)        │
    │  题目理解 + 置信度│
    └─────────────────┘
```

---

## 组件职责

### API Gateway
- 唯一入口，路由到对应 Lambda
- 不做业务逻辑，只做路由 + 基础鉴权（API Key）

### Lambda Handlers（5个，无状态）
每个 Handler 只做三件事：解析请求 → 调用 State Machine → 返回响应

| Handler | 职责 |
|---------|------|
| CreateJobHandler | 创建 Job 记录，触发 UNDERSTAND |
| GetJobHandler | 读 DynamoDB，返回当前状态 |
| AdvanceHandler | 接收产出物，校验自动 Gate（G1/G3/G4），写入结果 |
| ApproveHandler | 接收人工审批结果，执行 G2，更新状态 |
| GetArtifactHandler | 读取指定阶段产出物 |

### State Machine（Lambda 内嵌逻辑，不是 Step Functions）
- 管理 Job 在各阶段间的转移
- 执行 Gate 校验逻辑
- 写状态变更到 DynamoDB

> **为什么不用 Step Functions？**
> G2 的等待时间不确定（分钟～小时），Step Functions 等待回调支持这个场景，
> 但引入了额外复杂度。当前规模下，DynamoDB 存状态 + Lambda 轮询更简单。
> 如果 Job 量增大或需要可视化监控，再迁移到 Step Functions。

### DynamoDB（单表）
存三类数据：Job 元信息、各阶段产出物、Gate 记录
详见基础设施设计文档。

### Bedrock（Claude）
仅在 UNDERSTAND 阶段调用。
输入：题目文本
输出：`problem_type`、`known_conditions`、`solve_goal`、`confidence`

---

## 数据流

### 主流程（G1/G3/G4 自动通过）

```
1. POST /jobs
   CreateJobHandler → 写 DynamoDB(JOB#META, status=running, stage=UNDERSTAND)
   → 调 Bedrock 理解题目
   → 写 DynamoDB(ARTIFACT#UNDERSTAND)
   → 返回 Job

2. POST /jobs/{id}/advance  (stage=UNDERSTAND)
   AdvanceHandler → 读 ARTIFACT#UNDERSTAND
   → 校验 G1（goal非空 + confidence≥0.8）
   → 通过：写 GATE#G1(passed)，更新 stage=ORIENT, status=running
   → 返回 Job

3. POST /jobs/{id}/advance  (stage=ORIENT)
   AdvanceHandler → 接收 OrientPayload
   → 写 ARTIFACT#ORIENT
   → G2 是人工Gate，不校验，直接更新 status=waiting_approval
   → 返回 Job

4. POST /jobs/{id}/approve
   ApproveHandler → 读 ARTIFACT#ORIENT
   → 写 GATE#G2(passed/failed)
   → 通过：更新 stage=SOLVE, status=running
   → 拒绝：更新 status=running（留在ORIENT，等修订）
   → 返回 Job

5. POST /jobs/{id}/advance  (stage=SOLVE)
   AdvanceHandler → 接收 SolvePayload
   → 写 ARTIFACT#SOLVE
   → 校验 G3（每步reason非空 + intuition_explanation非空）
   → 通过：写 GATE#G3(passed)，更新 stage=VERIFY
   → 返回 Job

6. POST /jobs/{id}/advance  (stage=VERIFY)
   AdvanceHandler → 接收 VerifyPayload
   → 写 ARTIFACT#VERIFY
   → 校验 G4（所有验证passed + has_intuition=true）
   → 通过：写 GATE#G4(passed)，更新 stage=DONE, status=done
   → 返回 Job
```

### G1 失败流程

```
POST /jobs/{id}/advance (stage=UNDERSTAND)
  → confidence=0.63 < 0.8
  → 写 GATE#G1(failed)，更新 status=blocked
  → 返回 409 + GateFailure
  → 人工介入，确认题目理解后重新提交
```

---

## 并发和一致性

- 每个 Job 是独立的状态机，Job 间无共享状态
- 同一个 Job 的操作通过 DynamoDB 条件写（ConditionExpression）保证顺序
  - 例：advance 时校验 `current_stage = expected_stage`，防止重复提交

---

## 扩展点

| 当前 | 未来可扩展为 |
|------|-------------|
| Lambda 内嵌 State Machine | AWS Step Functions（Job 量大后） |
| 同步调 Bedrock | SQS + 异步调用（高并发后） |
| API Key 鉴权 | Cognito / JWT（多用户后） |
| G2 人工通过 API 审批 | 审批通知（SNS → 邮件/消息）|
