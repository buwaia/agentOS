# 30/60/90 Action Plan — AgentOS 数学解题引擎

## 30 Days: 运行 + 积累

- [ ] 将 AgentOS 接入真实数学课辅导场景
- [ ] 跑 20+ 道真实题目（证明题、计算题各半）
- [ ] 积累 50+ corrections.log 条目
- [ ] 做 2 次蒸馏（每 15 条 correction 一次）
- [ ] 每周跑 eval/run-eval.sh 追踪得分
- [ ] 修复 G3 whitespace 绕过问题（check_g3 改用 strip()）

**成功指标**: principles ≤ 5 条，rules 有退休记录，eval score ≥ 80%

## 60 Days: 渐进 + Loop

- [ ] G1/G3/G4 降为全自动 L1（观察 2 周无误报后）
- [ ] 实现真实 Bedrock 调用（替换 mock）
- [ ] 第一次 shortanswer profile loop 实验（全自动，无 G2）
- [ ] DynamoDB CONFIG# 分区实现热更新 loop-config
- [ ] DISTILL 事件触发 /drishti 自动扫描（定时任务或 webhook）

**成功指标**: shortanswer 类题目可全自动 loop，无需人工介入

## 90 Days: 进化 + 投产

- [ ] SAM 部署到 AWS Lambda + API Gateway（template.yaml 已就绪）
- [ ] 前端编译上传 S3 + CloudFront（替换本地 Vite dev server）
- [ ] Governance 总量 < Day 30 的 70%（蒸馏使文件变短）
- [ ] 新增 Profile：`exam`（考试模式，时间限制 + 简化 VERIFY）
- [ ] 跨题型 Principle 复用验证（同一套 governance 管所有题型）

**成功指标**: 生产环境稳定运行，G4 通过率 > 90%，每题平均成本 < $0.05

## 明天第一件事

修复 G3 whitespace 绕过：

```python
# engine/src/state_machine.py check_g3
if not payload.intuition_explanation.strip():
    return GateFailure(gate="G3", reason="intuition_explanation 为空或纯空白", ...)
```
