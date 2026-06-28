# Golden Set — 行为基准用例

每个用例定义「给定题目时，Engine 应产出什么」。用于 `run-eval.sh` 回归测试。

## GS-001: sqrt(2) 无理数证明

**Profile**: proof  
**Input problem**: `Prove sqrt(2) is irrational`

**Expected UNDERSTAND output**:
```json
{
  "problem_type": "inequality_proof",
  "solve_goal": "证明 sqrt(2) 不能表示为最简分数 p/q",
  "confidence": ">= 0.8",
  "known_conditions": ["包含'最简分数'或'有理数'相关条件"]
}
```

**Expected SOLVE output**:
```json
{
  "intuition_explanation": "包含'偶数传播'或'矛盾'关键词",
  "final_result": "包含'无理数'或'irrational'"
}
```

**Expected VERIFY output**:
```json
{
  "quality_check": {
    "has_intuition": true,
    "all_verifications_passed": true
  }
}
```

**Gate expectations**:
- G1: PASSED (confidence >= 0.8)
- G2: human review required
- G3: PASSED
- G4: PASSED

---

## GS-002: 简单计算题 (shortanswer profile)

**Profile**: shortanswer  
**Input problem**: `What is 2 + 2?`

**Expected behavior**:
- ORIENT 阶段跳过（G2 不触发）
- UNDERSTAND → SOLVE → VERIFY → DONE

**Expected SOLVE output**:
```json
{
  "final_result": "4",
  "intuition_explanation": "非空字符串"
}
```

---

## GS-003: G1 BLOCKED 场景

**Profile**: calculation  
**Input problem**: `?????` (无意义输入)

**Expected behavior**:
- G1 FAILED: confidence < 0.8
- Job 进入 BLOCKED
- distill 写入 `G1_FAILED` 事件

---

## 行为契约 (Behavioral Contract)

任何通过 G4 的 Job 必须满足：

| 契约 | 检查方式 |
|------|---------|
| `has_intuition = true` | `quality_check.has_intuition` 字段 |
| `intuition_explanation` 非空 | SOLVE artifact 字段长度 > 0 |
| 至少 1 个验证用例 | `verification_cases` 长度 >= 1 |
| 所有验证用例 passed | `all_verifications_passed = true` |
| 每个推导步骤有 reason | SolveStep.reason 非空 |

违反任意一条 → G4 阻断，Job 不能进入 DONE。
