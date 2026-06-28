# 解题 Profile

Profile 决定 Job 走哪个阶段路径。在创建 Job 时通过 `problem_type` 自动推断，也可显式指定。

## 内置 Profiles

### proof — 证明题

适用于：不等式证明、数论证明、几何证明

| 阶段 | 是否必须 | 说明 |
|------|---------|------|
| UNDERSTAND | ✅ | G1 置信度检查 |
| ORIENT | ✅ | G2 人工审批（证明路径至关重要）|
| SOLVE | ✅ | G3 必须有 intuition_explanation |
| VERIFY | ✅ | G4 所有用例必须 passed |

Gate 最低要求: G4 必须有 `has_story=true`（否则升为 L1）

### calculation — 计算题

适用于：函数求值、极值、积分

| 阶段 | 是否必须 | 说明 |
|------|---------|------|
| UNDERSTAND | ✅ | G1 置信度检查 |
| ORIENT | ✅ | G2 人工审批 |
| SOLVE | ✅ | G3 步骤 + reason |
| VERIFY | ✅ | G4 数值验证 |

Gate 最低要求: G4 `has_story` 为 L2 警告（不升 L1）

### shortanswer — 简答题

适用于：判断题、选择题、直接给出结论的题

| 阶段 | 是否必须 | 说明 |
|------|---------|------|
| UNDERSTAND | ✅ | G1 置信度检查 |
| ORIENT | ❌ | 跳过，无需路径选择 |
| SOLVE | ✅ | 允许 steps 只有 1 条 |
| VERIFY | ✅ | 允许 verification_cases 只有 1 条 |

G2 跳过，不需要人工审批。UNDERSTAND 完成后直接进入 SOLVE。

## problem_type → Profile 映射

```python
PROFILE_MAP = {
    "inequality_proof": "proof",
    "combinatorics":    "proof",
    "geometry":         "proof",
    "algebra":          "calculation",
    "function":         "calculation",
    "other":            "calculation",  # 默认走 calculation
}
```

## Profile 对 state_machine 的影响

`shortanswer` Profile 的 `next_stage_after_advance` 逻辑：
- UNDERSTAND → SOLVE（跳过 ORIENT 和 G2）
- SOLVE → VERIFY
- VERIFY → DONE
