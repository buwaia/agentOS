# Delivery Engine — 完整设计文档

> 日期：2026-06-28 | 模块：Module 07

---

## 一句话定义

数学解题引擎，独立服务部署在 AWS。输入一道题，经过四个阶段和四道门禁，输出一份经过直觉验证的解答。

---

## 为什么不是同步接口

最直觉的设计：`POST /solve` → 直接返回答案。

这个设计在 G2 处失败。G2（ORIENT 出口）是人工门禁——"选定路径是否有直觉性依据"无法自动化（P1: 洞见优先），必须有人来裁。

因此引擎是**异步状态机**：每道题是一个 Job，按阶段推进，G2 处等待人工审批。

---

## 阶段序列

```
题目输入
    │
    ▼
UNDERSTAND ──G1失败(confidence < 0.8)──→ blocked，等待人工
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
done，解答可交付
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
失败 → Job 进入 `blocked`，等待人工确认题目理解

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

> 已知限制：G2 无法自动化。"洞见"本身是人类判断。
> 干跑验证（2026-06-28）：G2 在琴生不等式题中成功拦截纯公式路径，接受半圆几何路径。

---

### SOLVE
**目的**：沿选定路径推导，不做方向性决策

| 字段 | 说明 |
|------|------|
| `steps` | 推导步骤，每步必须有 `expression`（表达式）和 `reason`（为什么这一步）|
| `final_result` | 最终结论 |
| `intuition_explanation` | "为什么是这个答案" |

**出口 G3（半自动）**：`intuition_explanation` 非空 且 每步 `reason` 非空（对应 R5）

---

### VERIFY
**目的**：主动破坏，用反例/特殊值/边界检验结论

| 字段 | 说明 |
|------|------|
| `verification_cases` | 验证用例，至少 1 个，方法：特殊值/边界/反向 |
| `quality_check.has_intuition` | 解析是否有直觉描述（R001）|
| `quality_check.all_verifications_passed` | 所有用例是否通过 |

**出口 G4（自动）**：所有验证 `passed = true` 且 `has_intuition = true`
通过 → Job 进入 `done`

---

## 门禁汇总

| 门禁 | 阶段出口 | 类型 | 触发 | 失败处理 |
|------|----------|------|------|---------|
| G1 | UNDERSTAND→ORIENT | 自动 | POST /advance | Job → blocked |
| G2 | ORIENT→SOLVE | **人工** | POST /approve | 退回 ORIENT |
| G3 | SOLVE→VERIFY | 半自动 | POST /advance | 409，修改重提 |
| G4 | VERIFY→DONE | 自动 | POST /advance | 409，修改重提 |

---

## API 接口

```
POST   /jobs                              提交题目，创建 Job
GET    /jobs/{job_id}                     查询 Job 状态和当前阶段
POST   /jobs/{job_id}/advance             提交阶段产出物，触发自动门禁（G1/G3/G4）
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

## 系统组件

```
┌──────────────────────────────────────────────────────┐
│                    外部调用者                          │
│        学生端（提交题目）    老师端（G2 审批）           │
└─────────────┬──────────────────────┬─────────────────┘
              ▼                      ▼
┌─────────────────────────────────────────────────────┐
│                   API Gateway（门卫）                  │
│  唯一入口，只做路由 + API Key 鉴权，不处理业务逻辑      │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
│CreateJob │ │GetJob  │ │Advance │ │Approve  │  Lambda（工人）
│Handler   │ │Handler │ │Handler │ │Handler  │  无状态，跑完销毁
└────┬─────┘ └───┬────┘ └───┬────┘ └────┬────┘
     └───────────┴──────────┴───────────┘
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
  ┌─────────────────┐     ┌──────────────────────┐
  │  State Machine   │     │  DynamoDB（记事本）    │
  │  Gate 校验逻辑   │     │  存 Job 状态、产出物、  │
  │  阶段转移逻辑    │     │  Gate 记录            │
  └────────┬────────┘     └──────────────────────┘
           │ (仅 UNDERSTAND 阶段)
           ▼
  ┌─────────────────┐
  │  Bedrock（AI）   │
  │  题目理解 + 置信度│
  └─────────────────┘
```

**三个组件各司其职：**
- **API Gateway**：门卫，路由转发
- **Lambda**：工人，无状态，状态全靠 DynamoDB 传递
- **DynamoDB**：记事本，持久化 Job 全部状态
- **Bedrock**：AI 大脑，仅调用一次（UNDERSTAND 阶段）

---

## AWS 运行流程

```
1. POST /jobs
   API Gateway → CreateJobHandler
   → 写 DynamoDB(JOB#META: running, UNDERSTAND)
   → 调 Bedrock，得到 problem_type/known_conditions/solve_goal/confidence
   → 写 DynamoDB(ARTIFACT#UNDERSTAND)
   → 返回 Job

2. POST /jobs/{id}/advance (stage=UNDERSTAND)
   API Gateway → AdvanceHandler
   → 校验 G1（confidence ≥ 0.8？）
   → 通过：写 GATE#G1(passed)，更新 stage=ORIENT, status=waiting_approval
   → 失败：写 GATE#G1(failed)，更新 status=blocked，返回 409

3. POST /jobs/{id}/approve (G2 人工审批)
   API Gateway → ApproveHandler
   → approved=true：写 GATE#G2(passed)，更新 stage=SOLVE, status=running
   → approved=false：写 GATE#G2(failed)，留在 ORIENT

4. POST /jobs/{id}/advance (stage=SOLVE)
   API Gateway → AdvanceHandler
   → 校验 G3（每步 reason 非空 + intuition_explanation 非空）
   → 通过：写 GATE#G3(passed)，更新 stage=VERIFY

5. POST /jobs/{id}/advance (stage=VERIFY)
   API Gateway → AdvanceHandler
   → 校验 G4（所有验证 passed + has_intuition=true）
   → 通过：写 GATE#G4(passed)，更新 stage=DONE, status=done
```

---

## DynamoDB 表设计

**表名**：`delivery-engine-jobs` | **计费**：PAY_PER_REQUEST | **单表设计**

```
Job 元信息        PK: JOB#{job_id}   SK: META
阶段产出物        PK: JOB#{job_id}   SK: ARTIFACT#{stage}
门禁记录          PK: JOB#{job_id}   SK: GATE#{gate}
```

一次 `Query PK=JOB#{id}` 取回一个 Job 的所有数据，无需 GSI。

---

## Lambda 配置

| Handler | 内存 | 超时 | 说明 |
|---------|------|------|------|
| create-job | 128MB | 30s | 需调 Bedrock，额外有 Bedrock IAM 权限 |
| get-job | 128MB | 10s | 只读 |
| advance | 256MB | 60s | Gate 校验逻辑较重 |
| approve | 128MB | 10s | 写入审批结果 |
| get-artifact | 128MB | 10s | 只读 |

- **运行时**：Python 3.12，ARM64（Graviton2，成本低约 20%）
- **鉴权**：API Key
- **IAM**：最小权限，create-job 多一条 `bedrock:InvokeModel`

---

## Bedrock Prompt 设计

```
你是一个数学解题助手。请理解下面这道数学题，并以 JSON 格式返回分析结果。

题目：{problem}

请返回以下 JSON，不要返回任何其他内容：
{
  "problem_type": "algebra | geometry | function | inequality_proof | combinatorics | other",
  "known_conditions": ["已知条件1", ...],
  "solve_goal": "用一句话说清楚要求什么",
  "confidence": 0.95,
  "confidence_reason": "简短说明"
}

confidence 评分标准：
- 0.9-1.0：题目清晰，条件完整，目标明确
- 0.7-0.9：基本清晰，个别条件模糊
- 0.5-0.7：有歧义或关键条件缺失
- 0.0-0.5：严重残缺或无法理解
```

**调用配置**：`temperature=0`（确定性输出），`max_tokens=1024`
**重试策略**：最多 3 次，指数退避（1s→2s→4s），全失败 → Job 进入 blocked

---

## 错误处理

| 场景 | HTTP 状态码 | 处理 |
|------|------------|------|
| 请求体格式不合法 | 422 | 返回字段校验详情 |
| job_id 不存在 | 404 | ErrorResponse |
| advance 的 stage 与当前不符 | 409 | STAGE_MISMATCH |
| 自动 Gate 校验不通过 | 409 | GATE_FAILED + 具体原因 |
| approve 时 Job 不在 waiting_approval | 409 | INVALID_APPROVAL_STATE |
| Bedrock 超时/返回异常 | 503 | Job → blocked，error_reason 附带原因 |
| DynamoDB 写入失败 | 503 | 原子操作失败不改变状态，客户端重试 |

**并发保护**：每次写 DynamoDB 带 `ConditionExpression`，校验 `current_stage = expected_stage`，防重复提交。

---

## 部署

**工具**：AWS SAM

```
engine/
├── template.yaml           SAM 模板（所有 AWS 资源定义）
├── src/
│   ├── handlers/
│   │   ├── create_job.py
│   │   ├── get_job.py
│   │   ├── advance.py
│   │   ├── approve.py
│   │   └── get_artifact.py
│   ├── state_machine.py    Gate 校验 + 状态转移逻辑
│   └── bedrock_client.py   Bedrock 调用封装
└── openapi.yaml            API 契约
```

```bash
sam build
sam deploy --guided   # 首次
sam deploy            # 后续
```

---

## 成本估算（初期）

| 资源 | 月成本 |
|------|-------|
| Lambda + DynamoDB + API Gateway | ~$0（免费额度内）|
| Bedrock（1,000 次 UNDERSTAND）| ~$3 |
| **合计** | **~$3/月** |

Bedrock 是唯一有实际成本的组件。

---

## 不可逆决策

| ADR | 决策 | 原因 | 代价 |
|-----|------|------|------|
| ADR-004 | HTTP API 而非 REST API | 成本低 70%，功能够用 | 缺少高级验证功能 |
| ADR-005 | Lambda 内嵌 State Machine 而非 Step Functions | 当前规模小，DynamoDB 存状态足够 | 状态转移逻辑分散，调试不直观 |

---

## 扩展点

| 当前 | 未来 |
|------|------|
| Lambda 内嵌 State Machine | Step Functions（Job 量大后）|
| 同步调 Bedrock | SQS + 异步（高并发后）|
| API Key 鉴权 | Cognito / JWT（多用户后）|
| G2 通过 API 审批 | SNS 通知 → 邮件/消息 |

---

## 前端设计

### 定位

单页应用（SPA），无路由，无鉴权。所有人用同一个页面：提题、看进度、做 G2 审批。

### 技术栈

React 19 + Tailwind（与 shopping-cart 保持一致），Vite 构建，部署到 S3 + CloudFront。

### 页面布局

```
┌──────────────────────────────────────────────┐
│  提题区                                        │
│  ┌────────────────────────────────────────┐  │
│  │ textarea: 输入题目文本                   │  │
│  └────────────────────────────────────────┘  │
│  [提交题目]                                    │
├──────────────────────────────────────────────┤
│  Job 列表                                      │
│  job-abc123  ORIENT  🟡 waiting_approval  [选]│
│  job-def456  DONE    ✅ done              [选]│
│  job-ghi789  VERIFY  🔵 running           [选]│
├──────────────────────────────────────────────┤
│  选中 Job 详情                                 │
│                                               │
│  阶段进度条：UNDERSTAND → ORIENT → SOLVE → VERIFY → DONE
│                                               │
│  当前阶段产出物（按阶段展示不同内容）            │
│  操作区（按状态展示不同按钮）                    │
└──────────────────────────────────────────────┘
```

### 各阶段详情展示

| 阶段 | 显示内容 | 操作 |
|------|---------|------|
| UNDERSTAND | problem_type / known_conditions / solve_goal / confidence | 无（等系统处理）|
| ORIENT（waiting_approval）| 候选路径列表 + 选定路径 + selection_rationale | **[审批通过] [拒绝]** + reviewer_id 输入框 |
| SOLVE | 推导步骤列表（每步 expression + reason）+ intuition_explanation | 无 |
| VERIFY | 验证用例列表 + quality_check | 无 |
| DONE | 完整解答（SOLVE + VERIFY 产出物合并展示）| 无 |
| BLOCKED | 错误原因（confidence 不足 / Bedrock 失败）| 无 |

### 状态颜色

| 状态 | 颜色 | 含义 |
|------|------|------|
| `running` | 🔵 蓝色 | 处理中 |
| `waiting_approval` | 🟡 黄色 | 等待 G2 审批 |
| `blocked` | 🔴 红色 | 需要人工介入 |
| `done` | 🟢 绿色 | 解答完成 |

### 轮询机制

- 选中一个 Job 后，每 3 秒调用 `GET /jobs/{id}` 刷新状态
- 状态变为 `done` 或 `blocked` 后停止轮询
- 轮询结果变化时自动重新读取产出物

### 文件结构

```
engine-frontend/
├── index.html
├── vite.config.js
├── src/
│   ├── main.jsx                入口
│   ├── App.jsx                 单页根组件（三块布局）
│   ├── components/
│   │   ├── SubmitForm.jsx      提题区
│   │   ├── JobList.jsx         Job 列表
│   │   ├── JobDetail.jsx       选中 Job 详情（含阶段切换）
│   │   ├── StageProgress.jsx   阶段进度条
│   │   ├── ApprovePanel.jsx    G2 审批操作区
│   │   └── StatusBadge.jsx     状态颜色标签
│   ├── hooks/
│   │   └── useJobPoller.js     轮询 hook
│   └── services/
│       └── api.js              API 调用封装（与 backend 对接）
└── .env.example                VITE_API_URL=https://...
```

### API 调用封装（api.js）

```js
const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const createJob    = (problem, problemType) =>
  request('/jobs', { method: 'POST', body: JSON.stringify({ problem, problem_type: problemType }) });

export const getJob       = (jobId) => request(`/jobs/${jobId}`);
export const getArtifact  = (jobId, stage) => request(`/jobs/${jobId}/artifacts/${stage}`);
export const approveOrient = (jobId, approved, reviewerId, comment) =>
  request(`/jobs/${jobId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved, reviewer_id: reviewerId, comment }),
  });
```

---

## 与 Governance 的对应

| 设计决策 | 治理依据 |
|----------|---------|
| G2 拦截无直觉路径 | P1 洞见优先 + R001 解答必须有直觉描述 |
| `intuition_explanation` 必填 | R5 函数结果必须有直觉解释 |
| `has_intuition` 作为 G4 条件 | P1 + R003 解析包含通俗类比即合格 |
| confidence < 0.8 → blocked | P2 AI 输出质量是产品底线 |
| `intuition_basis` schema 层必填 | R001 防止在数据层绕过 P1 |
