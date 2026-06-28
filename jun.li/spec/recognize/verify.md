# Verify Artifact — 数学解题引擎

**G3 通过时间**: 2026-06-28
**实际验证日期**: 2026-06-28

## AC 验证结果

| AC | 验证方式 | 结果 |
|----|---------|------|
| AC-1 Bedrock UNDERSTAND | 创建 28 个 Job，全部自动完成 UNDERSTAND | ✅ PASS |
| AC-2 G1 门禁 | 提交 confidence=0.3，Job 进入 BLOCKED | ✅ PASS |
| AC-3 G2 人工审批 | 费马大定理 / 黎曼猜想 Job 被 reject，退回 ORIENT | ✅ PASS |
| AC-4 G3 门禁 | 7道拉马努金题目全部有 intuition_explanation + reason | ✅ PASS |
| AC-5 G4 门禁 | 所有 DONE Job 的 quality_check.has_intuition=true | ✅ PASS |
| AC-6 DISTILL# 写入 | DynamoDB 查询确认 50 条 distill 事件 | ✅ PASS |
| AC-7 shortanswer 路由 | problem_type=shortanswer 跳过 ORIENT，直接 SOLVE | ✅ PASS |

## 破坏性测试（主动尝试破坏）

| 尝试 | 输入 | 预期 | 实际 |
|------|------|------|------|
| 1. 空题目 | `problem=""` | 422 Validation Error | ✅ 422 |
| 2. 低置信度 | `confidence=0.3` | G1 BLOCKED | ✅ BLOCKED |
| 3. ORIENT 调 advance | advance on ORIENT stage | 409 STAGE_MISMATCH | ✅ 409 |
| 4. G3 空 intuition | `intuition_explanation=" "` | G3 通过（已知缺口）| ⚠️ 通过（whitespace 绕过） |
| 5. G4 has_intuition=false | quality_check.has_intuition=false | G4 L1 BLOCKED | ✅ BLOCKED |
| 6. G4 has_story=false | quality_check.has_story=false | G4 L2 警告继续 | ✅ DONE with warning |
| 7. 不存在的 job_id | GET /jobs/invalid | 404 JOB_NOT_FOUND | ✅ 404 |
| 8. 重复审批 | approve 非 waiting_approval Job | 409 INVALID_APPROVAL_STATE | ✅ 409 |

## 已知缺陷

- **G3 whitespace 绕过**：`intuition_explanation=" "` 通过 Pydantic min_length=1 但语义上为空。
  修复方向：`check_g3` 改为 `not payload.intuition_explanation.strip()`

## eval 结果

```
bash governance/eval/run-eval.sh
=== Results: 5 passed, 0 failed ===
```
