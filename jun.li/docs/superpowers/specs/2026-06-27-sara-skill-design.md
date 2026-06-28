# Sara Skill 设计文档

**日期**：2026-06-27
**Skill 名称**：`/sara`
**触发方式**：`/sara <事件描述>`
**状态**：已确认，待实现

---

## 背景

Drishti（知识库自动维护 Hook）解决了"洞见跨 session 持久化"的问题。
Sara 解决的是上游问题：**如何把一次业务事件蒸馏成三层治理结构**。

两者关系：
- Drishti：看见信号 → 写入知识库（自动）
- Sara：事件 → Principles + Rules + Gates（引导式）

---

## 交互设计

### 输入
```
/sara <事件描述>
```
`$ARGUMENTS` 直接作为蒸馏起点，无需额外操作。

### 三问三答流程

```
问 1：这件事背后，什么原则被违反了？
      给出 2-3 个候选 Principle，用户选择或自定义
          ↓
问 2：下次遇到同样情况，判断"合格/不合格"的标准是什么？
      引导用户用一句话描述人可执行的判断标准
          ↓
问 3：这个判断能让机器自动检查吗？检查什么信号？
      引导用户描述可被 grep/脚本检测的具体信号
          ↓
生成 + 验证
```

### 编号规则
- 读取现有 principles.md 中最大 Pn，新增 P(n+1)
- 读取现有 rules/ 中最大 Rn，新增 R(n+1)-\<slug\>.md
- Gate 和测试文件以 \<slug\> 命名，与 Rule 对应

---

## 生成物

```
governance/
├── principles.md                  ← 追加新 Principle
├── rules/R{n}-{slug}.md           ← 新 Rule 文件
├── gates/check-{slug}.sh          ← 可执行 Gate 脚本
└── tests/test-{slug}.sh           ← 正例 + 反例测试用例
```

### Rule 文件模板
```markdown
# Rule R{n}: {标题}

## 追溯
- **Principle**: P{n}（{Principle 名称}）
- **Evidence**: {日期}，{事件描述}

## 判定标准
{人可直接执行的一句话标准}

## 违规示例
{反例}

## 满足示例
{正例}

## 过期条件
- 当 Gate `check-{slug}.sh` 稳定运行 {N} 天后退休
```

### Gate 脚本模板
```bash
#!/bin/bash
# Gate: {Rule 描述}
# 追溯: Principle P{n}
# 毕业条件: {退休条件}

INPUT="${1:-$(cat)}"
# 检测逻辑
[ 命中条件 ] && echo "✅ Gate passed" && exit 0
echo "❌ GATE BLOCKED: {原因}" && exit 1
```

### 测试文件模板
```bash
#!/bin/bash
GATE="$(dirname "$0")/../gates/check-{slug}.sh"
PASS=0; FAIL=0

run_case() { ... }  # 标准 run_case 函数

# 正例（应通过）
run_case "正例描述" "正例内容" "pass"

# 反例（应拦截）
run_case "反例描述" "反例内容" "fail"

echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

---

## 验证流程

生成四个文件后，自动执行：
```bash
bash governance/tests/run-all.sh
```

- 绿灯（全通过）：输出"蒸馏完成 ✅"
- 红灯：自动修复 Gate 脚本，直到测试通过

---

## 文件位置

Skill 文件：`~/.claude/commands/sara.md`

---

## 与现有框架的关系

| 组件 | 职责 |
|------|------|
| `/sara` | 事件 → 三层治理文件（引导式） |
| `run-all.sh` | 验证所有 Gate 正确性 |
| Drishti Stop hook | 捕获对话关键字 → 写回知识库 |
| `/test-hooks` | 验证 Drishti 链路 |
