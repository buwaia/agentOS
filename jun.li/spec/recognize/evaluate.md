# Evaluate Artifact — 数学解题引擎

**任务**: 构建数学解题 Delivery Engine（UNDERSTAND→ORIENT→SOLVE→VERIFY→DONE）
**Profile**: feature
**日期**: 2026-06-28

## Acceptance Criteria

- [ AC-1 ] 提交题目后，Bedrock 自动完成 UNDERSTAND，返回 problem_type / known_conditions / solve_goal / confidence
- [ AC-2 ] G1 门禁：confidence < 0.8 时 Job 进入 BLOCKED，不继续推进
- [ AC-3 ] G2 门禁：人工审批路径选择，通过后进入 SOLVE
- [ AC-4 ] G3 门禁：SOLVE 产出物必须有 intuition_explanation（非空）且每步有 reason
- [ AC-5 ] G4 门禁：所有验证用例 passed=true 且 has_intuition=true
- [ AC-6 ] 每次 Gate 事件写入 DynamoDB DISTILL# 分区，/drishti 可扫描
- [ AC-7 ] shortanswer 题型跳过 ORIENT/G2，直接 SOLVE

## 不可逆决策

| 决策 | 理由 | 不可逆原因 |
|------|------|-----------|
| DynamoDB 单表 | 读多写少，按 PK/SK 访问模式清晰 | 迁移 = 重写数据模型 |
| 异步状态机 | G2 是人工 Gate，无法同步等待 | API 设计与状态机深度耦合 |
| DISTILL# 分区 | Gate 事件与 Job 数据隔离，便于扫描 | 已有 50+ 条生产数据 |

## 风险识别

| 风险 | 缓解 |
|------|------|
| Bedrock 超时 | 最多重试 3 次，超时后 Job 进入 BLOCKED |
| Union 无 discriminator | Pydantic 按顺序匹配，需用 stage 字段区分 |
| G3 whitespace 绕过 | min_length=1 允许空白字符，check_g3 用 `not str.strip()` 修复（待） |
