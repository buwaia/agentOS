---
trigger: "开始任务" OR "run engine" OR 任务下发时
---

# Delivery Engine — 执行技能

## 执行流程

1. 读 `engine/STATE.md` 确定当前位置
2. 如果是新任务：
   a. 根据题目类型判断 Profile（读 `governance/profiles.md`）
   b. 更新 STATE.md（任务 + Profile + 当前阶段 = UNDERSTAND）
   c. 进入 UNDERSTAND 阶段
3. 如果是续做：
   a. 读 STATE.md 确认当前阶段
   b. 继续该阶段的工作
4. 每个阶段结束时：
   a. 产出 artifact（保存到 `spec/` 目录）
   b. 执行出口 Gate（读 `governance/gates.md`）
   c. Gate 通过 → 更新 STATE.md → 进入下一阶段
   d. Gate 失败（L1）→ 原地修复；同一 Gate 失败 3 次 → 回退上一阶段
   e. Gate 警告（L2）→ 记录 distill 事件 → 继续推进

## Profile 路径

| Profile | 路径 | 适用场景 |
|---------|------|---------|
| proof | UNDERSTAND→ORIENT(G2)→SOLVE→VERIFY→DONE | 证明题、不等式 |
| calculation | UNDERSTAND→ORIENT(G2)→SOLVE→VERIFY→DONE | 计算题、函数极值 |
| shortanswer | UNDERSTAND→SOLVE→VERIFY→DONE | 简答题，跳过 G2 |

## Gate 执行要点

- **G1**（UNDERSTAND 出口）：confidence ≥ 0.8，否则 BLOCKED
- **G2**（ORIENT 出口）：人工审批，判断路径是否有直觉性依据（P1）
- **G3**（SOLVE 出口）：intuition_explanation 非空，每步有 reason
- **G4**（VERIFY 出口）：所有验证用例 passed=true，has_intuition=true

## 蒸馏自动触发

每次 Gate 通过/失败均写入 DynamoDB `DISTILL#{date}` 分区。
`/drishti` 扫描时自动分析 pattern，发现系统性问题时建议 `/sara` 生成 Rule。
