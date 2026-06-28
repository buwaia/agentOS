# Gate 定义与级别

每个 Gate 有三个级别，控制失败时的行为：

| Level | 含义 | 失败时行为 |
|-------|------|-----------|
| L1 | 硬阻断 | Job 进入 BLOCKED，必须人工介入才能继续 |
| L2 | 软警告 | 记录警告，Job 继续推进，但 distill 事件标记 `warning=true` |
| L3 | 人工介入 | Job 进入 WAITING_APPROVAL，等待人工审批后继续 |

## G1 — 理解置信度门禁

- **Level**: L1（置信度过低时阻断）
- **触发条件**: `confidence < CONFIDENCE_THRESHOLD`（默认 0.8）
- **降级路径**: 置信度在 [0.6, 0.8) 时降为 L2（警告继续），< 0.6 保持 L1
- **Script**: `gates/check-intuitive-solution.sh`

## G2 — 解题路径人工审批

- **Level**: L3（始终人工介入）
- **触发条件**: UNDERSTAND 完成后，进入 ORIENT 前等待人工确认
- **审批者**: 任意有 reviewer_id 的用户
- **拒绝行为**: Job 回到 ORIENT 阶段重新选路

## G3 — 解题过程质量门禁

- **Level**: L1（缺少直觉解释时阻断）
- **触发条件**:
  - `intuition_explanation` 为空或纯空白
  - 任意步骤的 `reason` 为空
- **Script**: `gates/check-function-result-must-have-intuition.sh`

## G4 — 验证完整性门禁

- **Level**: L1（有验证用例失败时阻断）
- **L2 降级**: 所有用例通过但 `has_story=false` 时降为 L2 警告
- **触发条件**:
  - 任意 `verification_cases` 的 `passed=false`
  - `quality_check.has_intuition=false`
- **Script**: `gates/check-answer-quality.sh`
