# AgentOS — 数学解题 Delivery Engine

> 一个把「提交题目→通俗解法」做成异步流水线的 AgentOS 工程实践成果。

## 是什么

用 AgentOS 三层治理（Principles → Rules → Gates）驱动的数学解题引擎。
不是同步 API，是**异步状态机**：每道题是一个 Job，四个阶段逐步推进，每个阶段出口有 Gate 把关。

```
UNDERSTAND → ORIENT → SOLVE → VERIFY → DONE
               ↑
          G2: 人工审批（路径有直觉性依据吗？）
```

Gate 事件自动写入 DynamoDB → `/drishti` 扫描 → `/sara` 蒸馏成 Rule → 治理持续进化。

## 核心 Principles

1. **P1 洞见优先**：解题路径必须有直觉性依据，纯公式推导不够
2. **P2 数据质量是底线**：宁可 BLOCKED 也不放低置信度的理解通过
3. **P3 完成 = 主动破坏且失败**：VERIFY 阶段必须有破坏性测试记录

## 快速启动

```bash
# 后端
cd engine && python3 run_local.py

# 前端
cd engine-frontend && npx vite
```

访问：http://localhost:3000（或 CloudFront 代理地址）

## 健康检查

```bash
bash knowledge/health.sh
```

## 行为验证

```bash
bash governance/eval/run-eval.sh   # 行为契约（5项）
bash ci/verify.sh                  # 业务 schema 验证
```

## Engine 使用

| Profile | 路径 | 适用 |
|---------|------|------|
| proof | UNDERSTAND→ORIENT(G2)→SOLVE→VERIFY | 证明题 |
| calculation | UNDERSTAND→ORIENT(G2)→SOLVE→VERIFY | 计算题 |
| shortanswer | UNDERSTAND→SOLVE→VERIFY | 简答题（跳过G2） |

## 蒸馏节奏

每积累 10-15 条 `corrections.log` 做一次蒸馏：
- 3+ 条同类 correction → 上提为 Principle 或下沉为 Gate
- Gate 30 天未触发 → 毕业到 `_graduated/`
- Rule 被 Gate 覆盖 → 退休到 `_retired/`

## 目录结构

```
├── knowledge/          # DDD 四文档 + health.sh
├── governance/         # Principles + Rules + Gates + Profiles + Loop Config
│   ├── rules/_retired/ # 已退休的 Rules
│   └── gates/_graduated/ # 已毕业的 Gates
├── engine/             # FastAPI 后端 + State Machine
│   └── src/
├── engine-frontend/    # React + Vite 前端
├── spec/recognize/     # Engine 运行 artifacts（evaluate/plan/verify）
├── eval/               # golden-set + run-eval.sh（行为契约）
├── ci/                 # verify.sh（业务验证）
├── hooks/              # SessionStart/End hooks
├── docs/               # 设计文档 + 实施计划
└── corrections.log     # 蒸馏原料
```
