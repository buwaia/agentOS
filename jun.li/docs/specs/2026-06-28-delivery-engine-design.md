# Delivery Engine — 设计文档

> 日期：2026-06-28
> 模块：Module 07

---

## 一句话定义

数学解题引擎。输入一道题，经过四个阶段和四道 Gate，输出一份经过直觉验证的解答。

---

## 为什么不是同步接口

最直觉的设计：`POST /solve` → 直接返回答案。

这个设计在 G2 处失败。

G2（ORIENT 出口）是人工 Gate——判断"选定路径是否有直觉性依据"无法自动化（P1: 洞见优先）。纯公式推导路径必须被拦截，只有人能做这个判断。

因此引擎必须是**异步状态机**：每道题是一个 Job，按阶段推进，G2 处等待人工审批。

---

## 阶段序列

```
题目输入
    │
    ▼
UNDERSTAND ──G1失败(confidence < 0.8)──→ BLOCKED，等待人工
    │ G1通过
    ▼
ORIENT ────────────────────────────────→ waiting_approval，等待 G2
    │ G2通过（人工审批）
    │ G2拒绝 ──────────────────────────→ 回 ORIENT，修订路径
    ▼
SOLVE ──G3失败──→ 修改后重新提交
    │ G3通过
    ▼
VERIFY ──G4失败──→ 修改后重新提交
    │ G4通过
    ▼
DONE，解答可交付
```

---

## 四个阶段

### UNDERSTAND
**目的**：读懂题目，不推导，不解题

| 字段 | 说明 |
|------|------|
| `problem_type` | 题目类型（代数/几何/函数/不等式证明/组合…）|
| `known_conditions` | 已知条件列表，至少 1 条 |
| `solve_goal` | 求解目标，用一句话说清楚 |
| `confidence` | AI 理解置信度，[0, 1] |

**出口 G1（自动）**：`solve_goal` 非空 且 `confidence ≥ 0.8`
G1 失败 → Job 进入 `blocked` 状态，等待人工确认题目理解

---

### ORIENT
**目的**：选择解题路径，在不可逆决策前停下来

| 字段 | 说明 |
|------|------|
| `candidate_paths` | 候选路径列表，至少 2 条，每条必须有 `intuition_basis` |
| `selected_path_id` | 选定路径 ID |
| `selection_rationale` | 选定理由，必须有直觉性描述 |

**出口 G2（人工）**：审批人判断 `selection_rationale` 是否满足 P1
- 通过 → 推进到 SOLVE
- 拒绝 → 退回 ORIENT，修订路径

典型通过：「半圆垂线 ≤ 半径，几何事实直接给出结论」
典型拒绝：「令 f(x)=ln x，f''(x)<0，调用 Jensen 不等式」（机械，无直觉）

> **已知限制**：G2 目前无法自动化。"洞见"本身是人类判断，这是设计约束，不是 bug。
> 干跑验证（2026-06-28）：G2 在琴生不等式题中成功拦截了纯公式路径，接受了半圆几何路径。

---

### SOLVE
**目的**：沿选定路径推导，不做方向性决策

| 字段 | 说明 |
|------|------|
| `steps` | 推导步骤列表，每步必须有 `expression`（表达式）和 `reason`（为什么这一步）|
| `final_result` | 最终结论 |
| `intuition_explanation` | 结果的直觉解释——"为什么是这个答案" |

**出口 G3（半自动）**：`intuition_explanation` 非空 且 每步 `reason` 非空
对应 R5：函数结果必须有直觉解释

---

### VERIFY
**目的**：主动破坏，用反例/特殊值/边界检验结论

| 字段 | 说明 |
|------|------|
| `verification_cases` | 验证用例列表，至少 1 个；方法：特殊值/边界/反向 |
| `quality_check.has_intuition` | 解析是否有直觉描述（R001）|
| `quality_check.all_verifications_passed` | 所有用例是否通过 |

**出口 G4（自动）**：所有 `verification_cases.passed = true` 且 `has_intuition = true`
G4 通过 → Job 进入 `done`，解答可交付

---

## Gate 汇总

| Gate | 阶段出口 | 类型 | 触发方式 | 失败处理 |
|------|----------|------|----------|----------|
| G1 | UNDERSTAND→ORIENT | 自动 | POST /jobs/{id}/advance | Job → blocked |
| G2 | ORIENT→SOLVE | **人工** | POST /jobs/{id}/approve | 退回 ORIENT |
| G3 | SOLVE→VERIFY | 半自动 | POST /jobs/{id}/advance | 409，修改重提 |
| G4 | VERIFY→DONE | 自动 | POST /jobs/{id}/advance | 409，修改重提 |

---

## API 接口

```
POST   /jobs                              提交题目，创建 Job
GET    /jobs/{job_id}                     查询 Job 状态和当前阶段
POST   /jobs/{job_id}/advance             提交阶段产出物，触发自动 Gate
POST   /jobs/{job_id}/approve             人工审批 G2（ORIENT 专用）
GET    /jobs/{job_id}/artifacts/{stage}   读取指定阶段产出物
```

### Job 状态

| 状态 | 含义 |
|------|------|
| `running` | 当前阶段处理中，等待 advance |
| `waiting_approval` | ORIENT 完成，等待 G2 人工审批 |
| `blocked` | G1 confidence < 0.8，等待人工确认 |
| `done` | G4 通过，解答可交付 |

---

## AWS 部署映射

```
API Gateway
    ├── POST   /jobs                  → Lambda: CreateJobHandler
    ├── GET    /jobs/{id}             → Lambda: GetJobHandler
    ├── POST   /jobs/{id}/advance     → Lambda: AdvanceStageHandler
    ├── POST   /jobs/{id}/approve     → Lambda: ApproveOrientHandler
    └── GET    /jobs/{id}/artifacts/* → Lambda: GetArtifactHandler

状态持久化
    └── DynamoDB（单表，job_id 为 PK，stage 为 SK）
         ↑ 符合 ADR-001：单表设计，读多写少

AI 推理（UNDERSTAND 阶段）
    └── AWS Bedrock (Claude)
         ↑ 符合 ADR-002：不自建模型，用服务买时间
```

每个 Lambda 无状态，Job 状态全在 DynamoDB。

---

## 与 Governance 的对应关系

| 设计决策 | 对应治理 |
|----------|----------|
| G2 拦截无直觉路径 | P1 洞见优先 + R001 解答必须有直觉描述 |
| `intuition_explanation` 必填 | R5 函数结果必须有直觉解释 |
| `has_intuition` 作为 G4 条件 | P1 + R003 解析包含通俗类比即合格 |
| confidence < 0.8 → blocked | P2 AI 输出质量是产品底线 |
| `CandidatePath.intuition_basis` 必填 | R001 防止 schema 层绕过 P1 |

---

## 已知约束和未解决问题

1. **G2 无法自动化**：直觉判断需要人工，ORIENT 阶段是流程瓶颈
2. **G3 半自动**：`reason` 非空可脚本校验，但"有没有直觉"仍需人确认
3. **Bedrock 延迟**：UNDERSTAND 阶段 AI 调用是异步的，客户端需轮询 GET /jobs/{id}
