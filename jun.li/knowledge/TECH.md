# 数学解题引擎 — 技术知识

## 技术栈
- 前端：React 19 + Tailwind（Vite）
- 后端：Python FastAPI
- 数据库：DynamoDB
- AI：AWS Bedrock (Claude) — 题目理解与通俗解析生成
- 部署：AWS Lambda + API Gateway（SAM）

## 不可逆决策（Architecture Decision Records）

### [ADR-001] DynamoDB 而非 RDS
- **理由**: 单表设计适合 Job 状态机的读多写少模式
- **代价**: 复杂查询能力受限
- **不可逆原因**: 数据模型完全不同，迁移 = 重写

### [ADR-002] Bedrock 而非自建模型
- **理由**: 不投入 ML 团队；Claude 的语言能力适合生成通俗、有直觉感的解释
- **代价**: 成本随调用量线性增长
- **不可逆原因**: prompt 设计和后处理与 Claude API 耦合

### [ADR-003] 异步状态机而非同步接口
- **理由**: G2（ORIENT 出口）是人工门禁，必须等待人工审批"路径是否有直觉依据"
- **代价**: 前端需要轮询；调用方不能同步等结果
- **不可逆原因**: 整个 Job 模型基于此设计，改同步 = 重写

### [ADR-004] Claude Code Hook 知识库集成（Drishti 系统）
- **内容**: SessionStart hook 自动注入知识库；/drishti 命令手动触发知识提炼
- **理由**: agent 类型钩子在 Stop/PreCompact 不支持，改为手动触发
- **代价**: 知识提炼需主动运行 /drishti，非全自动

## 接口契约
- 所有接口返回 JSON，confidence 字段取值 [0, 1]
- SOLVE 每个 step 必须包含 expression + reason（非空，禁止纯符号跳跃）
- VERIFY 必须包含 verification_cases 和 quality_check
- confidence < 0.8 的解析不流出，标记待确认
- 解析输出须通过 Gate 脚本（check-intuitive-solution.sh）才可流出

## API 数据格式验证（2026-06-27 上线事件）
- 事件：上线前未检查 API 数据格式，前端直接崩溃
- 根本原因：缺乏 API 契约验证流程
- 已加入：governance/gates/check-api-contract.sh + R6 规则

## 本地存储迁移（2026-06-28）
- 从 moto mock 改为真实 DynamoDB（us-east-1，表名 DeliveryEngineLocal）
- run_local.py 去掉 mock_aws()，直接用 IAM 实例角色鉴权
- 数据持久化，重启后端/刷新页面历史不丢

## GET /jobs 列表接口补充（2026-06-28）
- 原设计只有 GET /jobs/{job_id}，无列表接口
- 新增 db.list_jobs()（scan + FilterExpression SK=META）+ handlers/list_jobs.py
- 前端 App.jsx useEffect 挂载时调用 api.listJobs() 拉取历史

## gate_history 修复（2026-06-28）
- 问题：get_job 只读 SK=META，GATE# 记录不在其中，gate_history 永远空
- 修复：db.get_gate_records()（query begins_with GATE#）+ get_job_handler 拼入
- 前端 JobDetail 新增 Gate History 区块，显示每个 gate 的结果/类型/时间

## Vite HMR CloudFront 兼容（2026-06-28）
- 问题：HMR WebSocket 写死 localhost:3000，CloudFront 域名访问时 JS 阻塞
- 修复：vite.config.js 设置 hmr: false，禁用热更新，页面正常加载
