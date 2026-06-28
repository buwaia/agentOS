# Engine 蒸馏闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Engine 运行产生的 Gate 事件（失败/通过）写入 DynamoDB，再由 /drishti 扫描后提炼模式，经 /sara 生成新 Rule + Gate 脚本，形成完整蒸馏闭环。

**Architecture:** Engine 每次 Gate 判断后额外写一条 `DISTILL#{date}` / `{job_id}#{event}` 记录；/drishti skill 增加第 0 步扫描近期蒸馏事件，发现系统性模式后输出 /sara 事件描述；/sara 生成 Rule + Gate 脚本 + 测试；SessionStart hook 已自动注入 knowledge/*.md，无需改动。

**Tech Stack:** Python FastAPI, boto3, DynamoDB, bash, /drishti skill, /sara skill

## Global Constraints

- 测试用 moto mock，不打真实 DynamoDB
- 新增代码遵循现有 `src/` 模块结构
- Gate 脚本放 `governance/gates/`，Rule 文件放 `governance/rules/`，测试放 `governance/tests/`
- 日期格式统一 `YYYY-MM-DD`，ISO 时间戳用 UTC

---

### Task 1: db.py 加 put_distill_event / query_distill_events

**Files:**
- Modify: `engine/src/db.py`
- Test: `engine/tests/test_db.py`

**Interfaces:**
- Produces:
  - `put_distill_event(date: str, job_id: str, event: str, payload: dict) -> None`
    - PK = `DISTILL#{date}`，SK = `{job_id}#{event}`
  - `query_distill_events(date: str) -> list[dict]`
    - query PK = `DISTILL#{date}`，返回当天所有蒸馏事件

- [ ] **Step 1: 写失败测试**

在 `engine/tests/test_db.py` 末尾追加：

```python
def test_put_and_query_distill_events(dynamodb_table):
    from src.db import put_distill_event, query_distill_events
    put_distill_event("2026-06-28", "job-abc", "G3_FAILED", {
        "problem_type": "proof",
        "failed_field": "intuition_explanation",
    })
    events = query_distill_events("2026-06-28")
    assert len(events) == 1
    assert events[0]["event"] == "G3_FAILED"
    assert events[0]["payload"]["problem_type"] == "proof"
```

- [ ] **Step 2: 运行验证失败**

```bash
cd /workshop/jun.li/engine
python3 -m pytest tests/test_db.py::test_put_and_query_distill_events -v
```

期望：`ImportError` 或 `FAILED`

- [ ] **Step 3: 在 db.py 末尾追加实现**

```python
def put_distill_event(date: str, job_id: str, event: str, payload: dict) -> None:
    from datetime import datetime, timezone
    _table().put_item(Item={
        "PK": f"DISTILL#{date}",
        "SK": f"{job_id}#{event}",
        "job_id": job_id,
        "event": event,
        "payload": _to_decimal(payload),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })


def query_distill_events(date: str) -> list[dict]:
    result = _table().query(
        KeyConditionExpression=Key("PK").eq(f"DISTILL#{date}")
    )
    return result.get("Items", [])
```

- [ ] **Step 4: 运行验证通过**

```bash
python3 -m pytest tests/test_db.py::test_put_and_query_distill_events -v
```

期望：`PASSED`

- [ ] **Step 5: 提交**

```bash
git add engine/src/db.py engine/tests/test_db.py
git commit -m "feat: add put_distill_event and query_distill_events to db"
```

---

### Task 2: advance.py / approve.py 调用 put_distill_event

**Files:**
- Modify: `engine/src/handlers/advance.py`
- Modify: `engine/src/handlers/approve.py`
- Test: `engine/tests/test_handlers.py`

**Interfaces:**
- Consumes: `put_distill_event(date, job_id, event, payload)` from Task 1

- [ ] **Step 1: 写失败测试**

在 `engine/tests/test_handlers.py` 末尾追加：

```python
def test_advance_writes_distill_event_on_g3_pass(client, dynamodb_table):
    from src.db import query_distill_events
    from datetime import datetime, timezone
    # 先建一个处于 SOLVE 阶段的 job
    job_id = "job-distill-test"
    from src.db import put_job_meta, put_artifact
    now = datetime.now(timezone.utc).isoformat()
    put_job_meta(job_id, "test problem", "running", "SOLVE", now)
    put_artifact(job_id, "UNDERSTAND", {"confidence": 0.95, "problem_type": "proof",
        "known_conditions": [], "solve_goal": "test", "stage": "UNDERSTAND"}, now)

    resp = client.post(f"/jobs/{job_id}/advance", json={
        "stage": "SOLVE",
        "payload": {
            "stage": "SOLVE",
            "steps": [{"step": 1, "expression": "x=1", "reason": "because"}],
            "final_result": "done",
            "intuition_explanation": "key insight here",
        }
    })
    assert resp.status_code == 200

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = query_distill_events(today)
    g3_events = [e for e in events if "G3_PASSED" in e["SK"]]
    assert len(g3_events) == 1
    assert g3_events[0]["payload"]["problem_type"] == "proof"


def test_approve_writes_distill_event_on_g2(client, dynamodb_table):
    from src.db import query_distill_events
    from datetime import datetime, timezone
    job_id = "job-g2-distill"
    from src.db import put_job_meta
    now = datetime.now(timezone.utc).isoformat()
    put_job_meta(job_id, "prove something", "waiting_approval", "ORIENT", now)

    resp = client.post(f"/jobs/{job_id}/approve", json={
        "approved": True,
        "comment": "good intuition",
    })
    assert resp.status_code == 200

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    events = query_distill_events(today)
    g2_events = [e for e in events if "G2_PASSED" in e["SK"]]
    assert len(g2_events) == 1
```

- [ ] **Step 2: 运行验证失败**

```bash
python3 -m pytest tests/test_handlers.py::test_advance_writes_distill_event_on_g3_pass tests/test_handlers.py::test_approve_writes_distill_event_on_g2 -v
```

期望：`FAILED`

- [ ] **Step 3: 修改 advance.py**

在 `engine/src/handlers/advance.py` 的 import 行加：

```python
from datetime import date as _date
from src.db import get_job, put_artifact, update_job_stage, put_gate_record, put_distill_event
```

在 `put_gate_record(...)` 之后追加（`advance_stage` 函数末尾，return 之前）：

```python
    # 写蒸馏事件
    understand_artifact = None
    try:
        from src.db import get_artifact
        ua = get_artifact(job_id, "UNDERSTAND")
        if ua:
            understand_artifact = ua.get("payload", {})
    except Exception:
        pass

    distill_event = f"{gate}_PASSED" if gate else f"{current}_DONE"
    put_distill_event(
        date=_date.today().isoformat(),
        job_id=job_id,
        event=distill_event,
        payload={
            "problem_type": (understand_artifact or {}).get("problem_type", "unknown"),
            "stage": current,
            "gate": gate,
        },
    )
```

- [ ] **Step 4: 修改 approve.py**

在 import 行加：

```python
from datetime import date as _date
from src.db import get_job, update_job_stage, put_gate_record, put_distill_event
```

在 `put_gate_record(...)` 之后追加（return 之前）：

```python
    put_distill_event(
        date=_date.today().isoformat(),
        job_id=job_id,
        event=f"G2_{'PASSED' if req.approved else 'REJECTED'}",
        payload={
            "approved": req.approved,
            "comment": req.comment or "",
            "problem": item.get("problem", "")[:100],
        },
    )
```

- [ ] **Step 5: 运行验证通过**

```bash
python3 -m pytest tests/test_handlers.py::test_advance_writes_distill_event_on_g3_pass tests/test_handlers.py::test_approve_writes_distill_event_on_g2 -v
```

期望：`PASSED`

- [ ] **Step 6: 全量测试确认不回归**

```bash
python3 -m pytest tests/ -v
```

期望：全部 PASSED

- [ ] **Step 7: 提交**

```bash
git add engine/src/handlers/advance.py engine/src/handlers/approve.py engine/tests/test_handlers.py
git commit -m "feat: write distill events to DynamoDB on gate pass/reject"
```

---

### Task 3: /drishti skill 增加扫描蒸馏事件步骤

**Files:**
- Modify: `/workshop/jun.li/.claude/commands/drishti.md`

**Interfaces:**
- Consumes: `aws dynamodb query` 查询 `DISTILL#{today}` 分区
- Produces: 在 /drishti 输出末尾追加"蒸馏事件分析"段落，列出发现的模式，并给出 /sara 调用建议

- [ ] **Step 1: 读当前 drishti.md**

```bash
cat /workshop/jun.li/.claude/commands/drishti.md
```

- [ ] **Step 2: 在 drishti.md 的 Steps 列表最前面插入 Step 0**

在 `## Steps` 下的 `1. **Scan the conversation**` 之前插入：

```markdown
0. **扫描 Engine 蒸馏事件**（在读对话之前先做）

   查询今天和昨天的蒸馏事件：

   ```bash
   TODAY=$(date -u +%Y-%m-%d)
   YESTERDAY=$(date -u -d "yesterday" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d)
   aws dynamodb query \
     --table-name DeliveryEngineLocal \
     --region us-east-1 \
     --key-condition-expression "PK = :pk" \
     --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${TODAY}\"}}" \
     --output json 2>/dev/null
   aws dynamodb query \
     --table-name DeliveryEngineLocal \
     --region us-east-1 \
     --key-condition-expression "PK = :pk" \
     --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${YESTERDAY}\"}}" \
     --output json 2>/dev/null
   ```

   分析事件，寻找以下模式：
   - 同一 `event` 出现 ≥ 3 次 → 系统性问题
   - `G2_REJECTED` 集中在某个 `problem` 关键词 → 该类题路径质量差
   - `G3_PASSED` 的 `problem_type` 分布 → 了解使用场景
   - Gate 失败事件（`G3_FAILED`、`G4_FAILED`）→ 优先蒸馏

   如果发现系统性模式，在报告末尾追加：

   ```
   ## Engine 蒸馏建议
   发现模式：[描述]
   建议运行：/sara [事件描述，供 sara 蒸馏成 Rule]
   ```
```

- [ ] **Step 3: 手动验证**

```bash
TODAY=$(date -u +%Y-%m-%d)
aws dynamodb query \
  --table-name DeliveryEngineLocal \
  --region us-east-1 \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${TODAY}\"}}" \
  --output json | python3 -m json.tool | head -30
```

期望：返回今天 advance/approve 产生的蒸馏事件 JSON

- [ ] **Step 4: 提交**

```bash
git add /workshop/jun.li/.claude/commands/drishti.md
git commit -m "feat: drishti scans Engine distill events before knowledge update"
```

---

### Task 4: /sara 验证——用真实蒸馏事件跑一遍

**Files:**
- 不新增文件，验证现有 /sara skill 能接收 Engine 产生的事件描述

**Goal:** 确认从"Engine 蒸馏事件 → /sara → Rule + Gate 脚本"这条链路完整可走。

- [ ] **Step 1: 触发一个真实的 G3 失败**

```bash
# 提交一个 reason 为空的 SOLVE，触发 G3 失败
JOB=$(curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"problem":"Prove sqrt(2) is irrational"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "job: $JOB"

# approve G2
curl -s -X POST "http://localhost:8000/jobs/$JOB/approve" \
  -H "Content-Type: application/json" \
  -d '{"approved":true,"comment":"test"}' | python3 -m json.tool | grep current_stage

# 提交 reason 为空的 SOLVE（触发 G3 失败）
curl -s -X POST "http://localhost:8000/jobs/$JOB/advance" \
  -H "Content-Type: application/json" \
  -d '{"stage":"SOLVE","payload":{"stage":"SOLVE","steps":[{"step":1,"expression":"p^2=2q^2","reason":""}],"final_result":"irrational","intuition_explanation":""}}' \
  | python3 -m json.tool | head -10
```

期望：返回 409，`"gate":"G3"`

- [ ] **Step 2: 确认蒸馏事件已写入**

```bash
TODAY=$(date -u +%Y-%m-%d)
aws dynamodb query \
  --table-name DeliveryEngineLocal \
  --region us-east-1 \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${TODAY}\"}}" \
  --output json | python3 -m json.tool
```

期望：看到 `G3_PASSED` 或已写入的事件记录

- [ ] **Step 3: 运行 /drishti 看蒸馏建议**

在 Claude Code 里运行：
```
/drishti
```

期望：输出末尾出现"## Engine 蒸馏建议"段落

- [ ] **Step 4: 把建议交给 /sara**

把 /drishti 输出的建议描述传给 /sara，例如：
```
/sara proof类题SOLVE阶段intuition_explanation频繁为空，说明用户不清楚这个字段的重要性，需要在Gate层面强化提示
```

期望：/sara 生成新 Rule 文件 + Gate 脚本 + 测试，`run-all.sh` 绿灯

- [ ] **Step 5: 提交**

```bash
git add governance/rules/ governance/gates/ governance/tests/
git commit -m "feat: first engine-driven sara distillation complete"
```

---

## Self-Review

**Spec coverage:**
- ✅ Engine 写蒸馏事件（Task 1 + 2）
- ✅ /drishti 扫描事件（Task 3）
- ✅ 发现模式 → /sara 调用（Task 4）
- ✅ SessionStart hook 注入 knowledge（已有，无需改动）

**Gaps:**
- Gate 失败时（GateFailedException）目前 advance.py 不写蒸馏事件（因为抛异常直接返回了）。Task 2 的实现写的是 Gate passed 事件；G3_FAILED / G4_FAILED 事件需要在 `except GateFailedException` 里单独写。补充在 Task 2 Step 3 里已说明写的是 passed 事件——**需要额外补**：

在 `advance.py` 的 `except GateFailedException as e:` 块里追加：

```python
    except GateFailedException as e:
        # 写失败蒸馏事件
        try:
            from src.db import get_artifact as _ga
            ua = _ga(job_id, "UNDERSTAND")
            put_distill_event(
                date=_date.today().isoformat(),
                job_id=job_id,
                event=f"{GATE_MAP.get(current, current)}_FAILED",
                payload={
                    "problem_type": (ua.get("payload", {}) if ua else {}).get("problem_type", "unknown"),
                    "gate": GATE_MAP.get(current),
                    "reason": e.failure.reason,
                },
            )
        except Exception:
            pass
        raise HTTPException(status_code=409, detail=e.failure.model_dump())
```

**Placeholder scan:** 无 TBD / TODO。

**Type consistency:** `put_distill_event(date, job_id, event, payload)` 在 Task 1 定义，Task 2 调用一致。
