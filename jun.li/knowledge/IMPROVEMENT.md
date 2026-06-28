# 数学解题引擎 — 改进方向

## 优先级
1. 解析通俗性：每步必须有直觉解释，不能只堆公式
2. Bedrock 真实调用：当前 UNDERSTAND 为 mock，需接入真实 Claude 调用
3. ORIENT 路径生成：AI 自动提出多条解题路径，人工从中选有直觉依据的那条

## 已知 Tech Debt
- 错误处理不统一
- 测试覆盖率未知
- ORIENT 阶段当前跳过 AI 生成，直接进入人工审批（路径内容为空）

## 禁止事项
- 不要添加 ORM（与 DynamoDB 单表设计冲突）
- SOLVE 步骤不允许无 reason 的纯符号跳跃

## AI 解析通俗化（核心要求）
- 来源：本项目的核心目标——通俗易懂，讲清楚"为什么"
- 已蒸馏治理规则：
  - R003：解析包含通俗类比或生活化描述即合格，纯符号推导链不合格
  - R004：解析包含叙事感（故事/场景）即合格，全公式不合格
- 改进方向：
  1. Bedrock prompt 加入"用生活类比或故事描述，不要只给公式"
  2. 解析输出接入 check-intuitive-solution.sh + check-story-in-solution.sh 做运行时质量门控
  3. 不通过 Gate → 自动重新生成，加强 prompt 约束

## AI 输出质量门控
- confidence < 0.8 的解析不流出，标记待确认
- VERIFY 不通过不输出
- 解析质量评估维度：准确性、可读性、直觉感

## 验收标准（2026-06-28 确认）
完整验收需看四样：
1. job status = DONE
2. Gate History：G1→G2→G3→G4 全部 passed（UI 可见）
3. SOLVE artifact：每步有非空 reason + intuition_explanation 说清楚为什么
4. VERIFY artifact：all_verifications_passed=true，有具体验证方法
当前 SOLVE steps 只有一步（把整个推导压成一行）——合格的应拆成 4-5 步，每步一个动作加理由

## ORIENT 阶段当前空洞（2026-06-28）
- ORIENT artifact 不存在：G2 通过后没有保存路径选择内容
- 需补：AI 提出 ≥2 条路径 → 人工从中选 → 选定路径写入 ORIENT artifact
