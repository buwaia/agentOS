# Drishti 三层治理设计文档

**日期**：2026-06-27  
**蒸馏自**：数学解题 AI 幻觉事件  
**状态**：已实现

---

## 背景

### 原始事件
1. 用户请求 Claude 证明琴生不等式
2. Claude 用纯符号推导作答 → 用户判定"AI幻觉"
3. Claude 改用半圆几何类比重新解答 → 用户认可
4. Drishti 关键字捕获因正则过窄（`ai幻觉` 漏匹配 `ai觉`）未触发
5. 修复正则后回溯验证通过，洞见写入 `IMPROVEMENT.md`

### 问题
- **解题质量问题**：Claude 倾向机械推导，缺乏形象化洞见
- **捕获机制问题**：Drishti 关键字正则对用户输入容错性不足

---

## 三层治理架构

```
原始事件
    ↓ 蒸馏
Principles  ← 为什么重要（不变）
    ↓ 细化
Rules       ← 怎么做（人工判断，有生命周期）
    ↓ 自动化
Gates       ← 机器检查（Rule 成熟后毕业，Gate 稳定后退休）
```

---

## Layer 1: Principles

文件：`governance/principles.md`

| 编号 | 原则 | 判定标准 |
|------|------|---------|
| P1 | 洞见优先于推导 | 解答包含图示、类比或直觉性描述之一 |
| P2 | AI 输出质量是产品底线 | confidence < 0.8 标记待确认；低质量解析触发复核 |
| P3 | 规则有生命周期 | 每条 Rule 必须有"过期条件"；每个 Gate 必须有"毕业条件" |

---

## Layer 2: Rules

文件：`governance/rules/`

### R001: 解答必须包含直觉性描述
- **追溯**：P1
- **判定**：包含几何图示 / 自然语言类比 / 直觉先于推导，三者之一
- **反例**：`f''(x) = -1/x² < 0，由 Jensen 不等式得结论`（纯符号链）
- **正例**：`半圆里垂线长度 = √(ab)，几何事实直接给出结论`
- **过期条件**：Gate `check-answer-quality.sh` 稳定 30 天后退休

### R002: AI 幻觉信号必须被 Drishti 捕获
- **追溯**：P2
- **判定**：用户表达"ai幻觉"、"ai觉"、"幻觉"等变体，均能命中关键字正则
- **正则**：`(ai|AI).{0,5}(幻觉|觉)|幻觉`
- **过期条件**：Gate `check-drishti-keywords.sh` 稳定 60 天后退休

---

## Layer 3: Gates

文件：`governance/gates/`

### check-answer-quality.sh
- **追溯**：R001 → P1
- **检测**：解答是否含图示关键词（`│─┼↑`）或类比关键词（`半圆`、`类比`、`想象`等）
- **已知局限**：纯正则无法判断语义，R001 人工判断作为补位（符合 P3）
- **毕业条件**：连续 30 天不触发，或解析 prompt 内置形象化要求并验证有效

### check-drishti-keywords.sh
- **追溯**：R002 → P2
- **检测**：对 5 个已知测试用例全部命中
- **测试用例**：`你产生了ai觉` / `你有AI幻觉` / `这是幻觉` / `confidence阈值需要调整` / `识别准确率太低`
- **毕业条件**：连续 60 天无漏捕获事件

---

## 生命周期流转

```
事件发生 → Rule 记录（人工判断）
         → Gate 实现（自动化）
         → Gate 稳定 → Rule 退休
         → Gate 60天不触发 → Gate 退休
         → 治理目标达成，该维度完结
```

---

## 文件结构

```
/workshop/jun.li/governance/
├── principles.md
├── rules/
│   ├── R001-answer-must-have-intuition.md
│   └── R002-ai-hallucination-must-be-captured.md
└── gates/
    ├── check-answer-quality.sh
    └── check-drishti-keywords.sh
```

---

## 与 Drishti Hook 的关系

| Drishti 组件 | 治理层 | 作用 |
|-------------|--------|------|
| UserPromptSubmit 关键字正则 | Gate (check-drishti-keywords) | 验证捕获覆盖度 |
| Stop agent prompt | Rule R001/R002 | 定义写入标准 |
| IMPROVEMENT.md 内容 | Principles 的落地证据 | 事件 → 洞见沉淀 |

---

## 设计理念

拉马努金不写推导，只写洞见。这套治理系统的设计原则相同：

- **Principles** 是永久洞见，不随时间过期
- **Rules** 是当下最佳实践，应该被自动化取代
- **Gates** 是自动化检查，应该因稳定而退休

**治理的终点不是更多规则，而是规则的消亡。**
