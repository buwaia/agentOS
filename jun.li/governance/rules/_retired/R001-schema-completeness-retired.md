<!-- RETIRED: 被 Gate check-api-contract.sh 吸收 (2026-06-28) -->

# Rule: 识别接口必须返回完整 schema

## 追溯
- Principle: P2（数据质量是底线）
- Evidence: corrections.log — "gate_history 始终为空"、"moto 数据丢失"

## 判定标准
- API 返回 JSON 包含 `confidence: number`，取值 [0, 1]
- 包含 `job_id`、`status`、`current_stage` 字段（非空）

## 退休原因
已下沉为 Gate `check-api-contract.sh`，代码层面阻断，无需 Rule 重复声明。
连续 7 个 Job 通过验证，Gate 覆盖稳定。
