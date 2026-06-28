# Sara Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 `/sara` slash command，通过三问引导用户把业务事件蒸馏成 Principle + Rule + Gate + 测试用例，并自动验证通过。

**Architecture:** Skill 文件落在 `/workshop/jun.li/.claude/commands/sara.md`，用 `$ARGUMENTS` 接收事件描述，引导三轮对话后生成四个文件，最后调用 `run-all.sh` 验证，红灯自动修复 Gate 直到绿灯。

**Tech Stack:** Bash（Gate 脚本）、Markdown（Rule 文件）、Claude Code slash command

## Global Constraints

- 所有文件落在 `/workshop/jun.li/` 下，不使用 `~/.claude/commands/`
- Skill 文件路径：`/workshop/jun.li/.claude/commands/sara.md`
- governance 文件命名规则：Principle 追加到 `principles.md`，Rule 文件 `R{n}-{slug}.md`，Gate `check-{slug}.sh`，测试 `test-{slug}.sh`
- Gate 脚本必须可执行（`chmod +x`）
- `run-all.sh` 必须自动发现并运行 `tests/` 下所有 `test-*.sh`

---

### Task 1: 升级 run-all.sh，支持自动发现新测试文件

**Files:**
- Modify: `/workshop/jun.li/governance/tests/run-all.sh`

**Interfaces:**
- Produces: `bash run-all.sh` 自动运行 `tests/test-*.sh` 下所有文件，无需手动注册

- [ ] **Step 1: 查看现有 run-all.sh**

```bash
cat /workshop/jun.li/governance/tests/run-all.sh
```

- [ ] **Step 2: 修改为自动发现模式**

将固定的两个 `run_suite` 调用替换为：

```bash
#!/bin/bash
DIR="$(dirname "$0")"
TOTAL_PASS=0
TOTAL_FAIL=0
SUITES=0

run_suite() {
  local name="$1"
  local script="$2"
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  bash "$script"
  local code=$?
  SUITES=$((SUITES+1))
  if [ $code -eq 0 ]; then
    TOTAL_PASS=$((TOTAL_PASS+1))
    echo "→ Suite [$name]: 全部通过 ✅"
  else
    TOTAL_FAIL=$((TOTAL_FAIL+1))
    echo "→ Suite [$name]: 存在失败 ❌"
  fi
}

echo "╔══════════════════════════════════════╗"
echo "║   Drishti 治理层测试套件              ║"
echo "╚══════════════════════════════════════╝"

for f in "$DIR"/test-*.sh; do
  name=$(basename "$f" .sh | sed 's/^test-//')
  run_suite "$name" "$f"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "总结：$TOTAL_PASS/$SUITES 个套件通过"
[ $TOTAL_FAIL -eq 0 ] && echo "✅ 所有治理 Gate 验证通过" && exit 0
echo "❌ $TOTAL_FAIL 个套件存在失败" && exit 1
```

- [ ] **Step 3: 验证现有测试仍通过**

```bash
bash /workshop/jun.li/governance/tests/run-all.sh
```

期望输出：`✅ 所有治理 Gate 验证通过`

---

### Task 2: 实现 sara.md slash command

**Files:**
- Create: `/workshop/jun.li/.claude/commands/sara.md`

**Interfaces:**
- Consumes: `$ARGUMENTS`（事件描述字符串）
- Produces: 引导三轮对话 → 4 个文件 → `run-all.sh` 绿灯

- [ ] **Step 1: 创建 commands 目录**

```bash
mkdir -p /workshop/jun.li/.claude/commands
```

- [ ] **Step 2: 写入 sara.md**

完整内容见下方，包含：
1. 事件接收与展示
2. 三问引导逻辑
3. 文件生成（Principle 追加 + Rule + Gate + 测试）
4. 自动运行 `run-all.sh` 验证
5. 红灯时自动修复 Gate

```markdown
# Sara — 三层治理蒸馏

> Sara（सार）：梵文"精华"。把事件蒸馏成可执行的治理结构。

用法：`/sara <事件描述>`

---

## 执行步骤

**读取事件**

用户输入的事件是：`$ARGUMENTS`

如果 `$ARGUMENTS` 为空，告知用户：`/sara <事件描述>`，停止执行。

---

**第一步：蒸馏 Principle**

先读取现有 Principles：
```bash
cat /workshop/jun.li/governance/principles.md
```

基于事件描述和现有 Principles，向用户提问：

> 这件事背后，违反了哪条原则？
>
> 候选（可选其一，或自己描述）：
> A. [基于事件生成的候选1]
> B. [基于事件生成的候选2]
> C. 已有原则中的某条（列出现有 P1/P2/P3）
> D. 自定义

等待用户回答后，确定 Principle 内容和编号（新增或复用已有）。

---

**第二步：定义 Rule**

基于用户对 Principle 的回答，向用户提问：

> 下次遇到同样情况，怎么判断"合格"还是"不合格"？
> 用一句话描述，人拿着这句话就能直接判断。

等待用户回答后，提炼成 Rule 的判定标准。

---

**第三步：设计 Gate**

基于 Rule，向用户提问：

> 这个判断能让脚本自动检查吗？
> 脚本应该检查什么信号？（比如：关键词、文件存在、格式、退出码）

等待用户回答后，设计 Gate 的检测逻辑。

---

**第四步：生成文件**

收集三轮回答后，执行以下操作：

1. **确定编号**
```bash
# 获取下一个 Rule 编号
last_n=$(ls /workshop/jun.li/governance/rules/R*.md 2>/dev/null | grep -oE 'R[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
n=$(( ${last_n:-0} + 1 ))
slug="<从Rule标题生成的kebab-case英文slug>"
```

2. **追加 Principle**（如果是新 Principle）
在 `/workshop/jun.li/governance/principles.md` 末尾追加：
```
## P{n}: {Principle 标题}
**{一句话核心}**

- **描述**：{详细描述}
- **来源**：{事件来源}
- **判定标准**：{判定标准}
```

3. **创建 Rule 文件**
`/workshop/jun.li/governance/rules/R{n}-{slug}.md`：
```markdown
# Rule R{n}: {标题}

## 追溯
- **Principle**: P{n}（{Principle 名称}）
- **Evidence**: {日期}，{事件描述}

## 判定标准
{用户在第二步给出的标准}

## 违规示例
{反例}

## 满足示例
{正例}

## 过期条件
- 当 Gate `check-{slug}.sh` 稳定运行 30 天后退休
```

4. **创建 Gate 脚本**
`/workshop/jun.li/governance/gates/check-{slug}.sh`：
```bash
#!/bin/bash
# Gate: {Rule 描述}
# 追溯: Principle P{n}（{Principle 名称}）
# 毕业条件: 连续 30 天不触发后退休

INPUT="${1:-$(cat)}"
# {根据第三步用户描述的检测逻辑}
[ 命中条件 ] && echo "✅ Gate passed: {描述}" && exit 0
echo "❌ GATE BLOCKED: {原因}" && exit 1
```
然后：`chmod +x /workshop/jun.li/governance/gates/check-{slug}.sh`

5. **创建测试文件**
`/workshop/jun.li/governance/tests/test-{slug}.sh`：
```bash
#!/bin/bash
GATE="$(dirname "$0")/../gates/check-{slug}.sh"
PASS=0; FAIL=0

run_case() {
  local label="$1"; local input="$2"; local expect="$3"
  result=$(bash "$GATE" "$input" 2>&1); exit_code=$?
  if [ "$expect" = "pass" ] && [ $exit_code -eq 0 ]; then
    echo "✅ PASS [$label]"; PASS=$((PASS+1))
  elif [ "$expect" = "fail" ] && [ $exit_code -ne 0 ]; then
    echo "✅ PASS [$label] (正确拦截)"; PASS=$((PASS+1))
  else
    echo "❌ FAIL [$label]"; FAIL=$((FAIL+1))
  fi
}

echo "=== R{n} {标题} Gate 测试 ==="
# 正例（应通过）
run_case "正例" "{正例内容}" "pass"
# 反例（应拦截）
run_case "反例" "{反例内容}" "fail"

echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```
然后：`chmod +x /workshop/jun.li/governance/tests/test-{slug}.sh`

---

**第五步：验证**

```bash
bash /workshop/jun.li/governance/tests/run-all.sh
```

- 全部绿灯：输出"✅ Sara 蒸馏完成！新洞见已写入治理层。"，并列出生成的四个文件路径
- 存在红灯：检查失败的 Gate，分析原因，修复 `check-{slug}.sh` 的检测逻辑，重新运行直到绿灯
```

- [ ] **Step 3: 验证文件创建成功**

```bash
ls /workshop/jun.li/.claude/commands/
```

期望输出包含 `sara.md`

---

### Task 3: 端到端验证 sara 链路

**Files:**
- 无新文件，验证整个链路

**Interfaces:**
- Consumes: sara.md + governance/ 完整结构
- Produces: 一次完整 `/sara` 调用的预演，确认所有步骤可执行

- [ ] **Step 1: 确认 commands 目录被 Claude Code 识别**

```bash
ls /workshop/jun.li/.claude/commands/sara.md
```

- [ ] **Step 2: 确认 run-all.sh 自动发现模式正常**

```bash
bash /workshop/jun.li/governance/tests/run-all.sh
```

期望：`2/2 个套件通过 ✅`

- [ ] **Step 3: 确认 governance 目录结构完整**

```bash
find /workshop/jun.li/governance -type f | sort
```

期望包含：principles.md、rules/R00*.md、gates/check-*.sh、tests/test-*.sh、tests/run-all.sh
