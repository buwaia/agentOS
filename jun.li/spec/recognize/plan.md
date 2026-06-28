# Plan Artifact — 数学解题引擎

**G1 通过时间**: 2026-06-28
**Profile**: feature

## 方案概述

FastAPI 异步状态机，DynamoDB 单表存储，Bedrock 处理 UNDERSTAND 阶段。

## AC → 实现映射

| AC | 实现位置 |
|----|---------|
| AC-1 Bedrock UNDERSTAND | `engine/src/handlers/create_job.py` + `bedrock_client.py` |
| AC-2 G1 门禁 | `engine/src/state_machine.py::check_g1` |
| AC-3 G2 人工审批 | `engine/src/handlers/approve.py` |
| AC-4 G3 门禁 | `engine/src/state_machine.py::check_g3` |
| AC-5 G4 门禁 | `engine/src/state_machine.py::check_g4` |
| AC-6 DISTILL# 写入 | `engine/src/db.py::put_distill_event` |
| AC-7 shortanswer 路由 | `engine/src/state_machine.py::g1_next_stage` |

## ADR

### ADR-001 GateLevel 枚举
- **决策**: L1/L2/L3 三级，不用 boolean
- **理由**: 未来可扩展降级路径，L2 警告继续比 L1 阻断更细粒度
- **代价**: 调用方需处理 level 字段

### ADR-002 DISTILL# 独立分区
- **决策**: Gate 事件写 `DISTILL#{date}` 而不是塞进 JOB# 分区
- **理由**: /drishti 扫描时可以不知道 job_id，直接按日期查
- **代价**: 需要额外的 PutItem 调用

### ADR-003 Profile 决定阶段路径
- **决策**: problem_type 映射到 profile，profile 决定 g1_next_stage
- **理由**: shortanswer 跳 G2 是业务逻辑，不是配置
- **代价**: 新增 problem_type 需要更新 PROFILE_MAP

## 风险缓解

- Pydantic Union discriminator 问题：前端提交时必须带 `stage` 字段，后端依赖字段顺序匹配
- G4 L2 降级：has_story=false 时警告继续，distill 写 G4_WARNING 事件
