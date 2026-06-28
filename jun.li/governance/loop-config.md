# Loop 配置

控制 Delivery Engine 的重试、熔断和成本治理。

## 停止条件

| 条件 | 默认值 | 说明 |
|------|--------|------|
| `max_retries_per_stage` | 3 | 同一阶段最多重新提交 3 次 |
| `max_g2_rejections` | 2 | G2 被拒绝超过 2 次后 Job 进入 BLOCKED |
| `max_total_advance_calls` | 10 | 单个 Job 总 advance 次数上限 |

## Circuit Breaker

当以下条件触发时，自动停止并告警：

| 触发条件 | 行为 |
|---------|------|
| 同一 Job 连续 3 次 G1_FAILED | Job 进入 BLOCKED，distill 写入 `CIRCUIT_OPEN` 事件 |
| 同一 Job G2 被拒 `max_g2_rejections` 次 | Job 进入 BLOCKED |
| 当日 G3_FAILED 率 > 50%（超过 10 个 Job 样本）| 写入 `SYSTEM_DEGRADED` distill 事件，/drishti 下次扫描时优先报告 |

## 成本治理

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `bedrock_max_tokens` | 1024 | UNDERSTAND 阶段 Bedrock 最大 token |
| `bedrock_timeout_seconds` | 30 | 超时后 Job 进入 BLOCKED |
| `bedrock_max_retries` | 3 | 指数退避：1s → 2s → 4s |

## 配置文件位置

运行时配置读取顺序：
1. 环境变量（`MAX_RETRIES_PER_STAGE`、`MAX_G2_REJECTIONS`）
2. DynamoDB `CONFIG#LOOP` 分区（热更新，不需重启）
3. 代码默认值（上表所列）

## DynamoDB CONFIG# 分区格式

```json
{
  "PK": "CONFIG#LOOP",
  "SK": "v1",
  "max_retries_per_stage": 3,
  "max_g2_rejections": 2,
  "max_total_advance_calls": 10,
  "bedrock_timeout_seconds": 30,
  "updated_at": "2026-06-28T00:00:00Z"
}
```
