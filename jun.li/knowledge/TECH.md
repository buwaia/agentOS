# 错题本 — 技术知识

## 技术栈
- 前端：React 19 + Tailwind
- 后端：Python FastAPI
- 数据库：DynamoDB
- AI：AWS Bedrock (Claude) — 图片识别
- 部署：AWS Lambda + API Gateway

## 不可逆决策（Architecture Decision Records）

### [ADR-001] DynamoDB 而非 RDS
- **理由**: 单表设计适合题目的读多写少模式
- **代价**: 复杂查询能力受限
- **不可逆原因**: 数据模型完全不同，迁移 = 重写

### [ADR-002] Bedrock 而非自建模型
- **理由**: 不投入 ML 团队，用服务买时间
- **代价**: 成本随调用量线性增长
- **不可逆原因**: prompt 设计和后处理与 Claude API 耦合

## 接口契约
- 识别接口返回 JSON schema
- confidence 字段永远存在，取值 [0, 1]
- 解析内容字段必须通过解析质量 Gate（check-intuitive-solution.sh）

### [ADR-003] Claude Code Hook 知识库集成
- **内容**: 使用 Claude Code 的 SessionStart/Stop hook 实现知识库自动同步
  - SessionStart hook (command): 每个 session 开始时读入四个知识库文档 → 注入作为 Claude 上下文
  - Stop hook (agent): 每个 session 结束时分析改动 → 自动更新知识库
- **理由**: 解决知识库"单向信息流"问题；使知识库成为活的、不断迭代的工作记录
- **代价**: 需要维护 hook 配置，且 Stop hook 本身是异步行为
- **收益**: 无需手动维护，形成自动闭环；过去的决策自动沉淀到文档

## API 数据格式验证问题（2026-06-27 上线事件）
- **事件**: 上线前没有人检查 API 返回的数据格式，导致前端直接崩溃
- **根本原因**: 缺乏结构化的 API 契约验证流程，依赖人工记忆
- **影响范围**: 识别接口的数据格式变化会直接导致前端故障
- **改进方向**:
  1. 在 API Gateway 或 FastAPI middleware 中添加响应数据格式校验
  2. 上线前建立 API 契约检查步骤（脚本或验证用例）
  3. 将 API 数据格式变更纳入发布清单，要求显式验证
