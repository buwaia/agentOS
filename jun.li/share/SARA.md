# Sara — 三层治理蒸馏 Skill

> Sara（सार）：梵文"精华"。拉马努金把数学现象蒸馏成一行结论；Sara 把业务事件蒸馏成可执行的治理结构。

---

## 是什么

Sara 是一个 Claude Code slash command。

你把一件刚发生的事告诉它，它通过三个问题引导你，蒸馏出三层治理文件：

```
事件描述
    ↓ 三个问题
Principle  — 违反了什么原则？
Rule       — 下次怎么判断合不合格？
Gate       — 机器能自动检查什么信号？
    ↓ 自动生成 + 验证
四个文件，测试绿灯
```

---

## 设计原理

### 三问对应三层

| 问题 | 对应层 | 输出 |
|------|--------|------|
| 这件事背后违反了什么原则？ | Principles | 追加到 principles.md |
| 下次怎么判断合格/不合格？ | Rules | 创建 R{n}-{slug}.md |
| 脚本能自动检查什么信号？ | Gates | 创建 check-{slug}.sh |

第三问之后自动生成测试用例（test-{slug}.sh），并立刻跑验证。

### 为什么是三问，不是一步生成

因为三层的质量取决于**你对事件的理解**，不是 AI 的推断。

- 第一问：强迫你问"这件事背后是什么"，而不是停留在现象
- 第二问：强迫你把原则翻译成人可执行的判断标准
- 第三问：强迫你把人的判断翻译成机器可检查的信号

三个问题问完，三层自然成型。AI 负责生成代码，你负责提供洞见。

### 验证闭环

生成后立即跑 `run-all.sh`：
- 绿灯 = 蒸馏完成，Gate 行为符合 Rule 定义
- 红灯 = 自动修复 Gate 直到通过，保证"生成即可用"

---

## 使用方式

### 安装

Sara skill 文件位于：
```
/workshop/jun.li/.claude/commands/sara.md
```

Claude Code 会自动发现 `.claude/commands/` 下的所有 `.md` 文件作为 slash command。

### 调用

```
/sara <事件描述>
```

**示例：**

```
/sara 今天上线后支付模块报错，schema 变更没人审就合并了

/sara 用户反馈 AI 解析的答案没有图示，看不懂

/sara 测试覆盖率不知道多少，上线前没有强制检查
```

### 交互流程

```
你：/sara 今天支付模块 schema 变更没人审就上线了

Sara：这件事背后，违反了哪条原则？
     A. 变更必须经过评审（代码安全底线）
     B. 上线前必须有检查点（质量门控）
     C. 已有原则：P1 洞见优先 / P2 AI质量底线 / P3 规则有生命周期
     D. 自定义

你：B

Sara：下次遇到同样情况，怎么判断"合格"还是"不合格"？
     用一句话描述，人拿着这句话就能直接判断。

你：schema 变更文件必须有对应的 review comment 或 ADR 记录

Sara：这个判断能让脚本自动检查吗？
     脚本应该检查什么信号？

你：检查 PR 里有没有 schema 相关文件变更，如果有，验证 commit message 包含 "reviewed" 或 "ADR"

Sara：[生成四个文件]
     [运行 run-all.sh]
     ✅ Sara 蒸馏完成！新洞见已写入治理层。
```

### 生成物

```
/workshop/jun.li/governance/
├── principles.md              ← 追加新 Principle（如复用已有则跳过）
├── rules/R003-{slug}.md       ← 新 Rule 文件
├── gates/check-{slug}.sh      ← 可执行 Gate 脚本
└── tests/test-{slug}.sh       ← 正例 + 反例测试用例
```

---

## 与 Drishti 的关系

| 工具 | 触发时机 | 做什么 |
|------|---------|--------|
| **Drishti** | 每次 session 自动 | 捕获对话关键字 → 追加洞见到知识库 |
| **Sara** | 手动调用 | 把事件蒸馏 → 生成三层治理文件 |

两者互补：Drishti 负责"看见"，Sara 负责"提炼"。

---

## 验证治理层

任何时候都可以一键验证所有 Gate：

```bash
bash /workshop/jun.li/governance/tests/run-all.sh
```

run-all.sh 自动发现 `tests/test-*.sh` 下所有测试，每次 Sara 添加新 Gate，下次验证自动包含。

---

## 文件结构

```
/workshop/jun.li/
├── .claude/
│   └── commands/
│       ├── sara.md          ← Sara skill（本文件）
│       └── test-hooks.md    ← Drishti 验证命令
├── governance/
│   ├── principles.md        ← 所有 Principles
│   ├── rules/               ← 所有 Rules（Sara 追加）
│   ├── gates/               ← 所有 Gates（Sara 追加）
│   └── tests/               ← 所有测试（Sara 追加 + run-all.sh）
├── knowledge/               ← Drishti 知识库
└── share/
    ├── SARA.md              ← 本文档
    └── DRISHTI.md           ← Drishti 文档
```

---

## 设计理念

拉马努金从不记推导过程，他的笔记本里只有洞见。

Sara 遵循同样的原则：

- **事件是原材料**，不是结论
- **三问是过滤器**，去掉现象留下本质
- **Gate 是终态**，洞见变成可执行的检查
- **退休是目标**，Gate 稳定后消亡，治理层越来越干净

> 蒸馏的终点不是更多规则，而是规则的消亡。
