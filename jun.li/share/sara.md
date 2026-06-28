# Sara — 三层治理蒸馏

> Sara（सार）：梵文"精华"。把事件蒸馏成可执行的治理结构。

用法：`/sara <事件描述>`

---

## 执行步骤

**读取事件**

用户输入的事件是：`$ARGUMENTS`

如果 `$ARGUMENTS` 为空，告知用户：请使用 `/sara <事件描述>` 的格式，并停止执行。

---

**第一步：给出蒸馏草稿**

先读取现有 Principles 和已有 Rules 编号：

```bash
cat /workshop/jun.li/governance/principles.md
ls /workshop/jun.li/governance/rules/
```

基于事件，**直接给出一个完整的蒸馏草稿**，用自然对话的语气呈现，不要用表单格式。格式如下：

---

我理解了。这件事本质是——**[用一句话说清楚问题本质]**

我的蒸馏草稿：

**原则**：[复用已有 P1/P2/P3，或提出新原则——说清楚是哪条以及为什么]

**规则**：[一句话判定标准，人拿着能直接判断合格/不合格]

**检查点**：[脚本能自动检测的信号——正向词或负向结构]

这个方向对吗？还是你想调整哪里？

---

等待用户确认或修改。

- 用户说"对"/"可以"/"没问题" → 进入第二步生成文件
- 用户说"改一下......" → 按用户意见更新草稿，再次确认
- 用户只调整某一层 → 保留其他层，只改对应部分

---

**第二步：生成文件**

用户确认草稿后，执行以下操作：

**2.1 确定编号和 slug**

```bash
last_n=$(ls /workshop/jun.li/governance/rules/R*.md 2>/dev/null | grep -oE 'R[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
n=$(( ${last_n:-0} + 1 ))
```

从规则标题生成 kebab-case 英文 slug（例如："解析必须有故事" → `story-first-solution`）。

**2.2 追加 Principle**（仅当是新原则时）

在 `/workshop/jun.li/governance/principles.md` 末尾追加：

```
## P{n}: {Principle 标题}
**{一句话核心}**

- **描述**：{详细描述}
- **来源**：{事件来源，含日期}
- **判定标准**：{判定标准}
```

**2.3 创建 Rule 文件**

创建 `/workshop/jun.li/governance/rules/R{n}-{slug}.md`：

```markdown
# Rule R{n}: {标题}

## 追溯
- **Principle**: P{p}（{Principle 名称}）
- **Evidence**: {日期}，{事件描述}

## 判定标准
{草稿中确认的规则，一句话}

## 违规示例
{基于事件构造的反例}

## 满足示例
{基于事件构造的正例}

## 过期条件
- 当 Gate `check-{slug}.sh` 稳定运行 30 天后退休
```

**2.4 创建 Gate 脚本**

创建 `/workshop/jun.li/governance/gates/check-{slug}.sh`：

```bash
#!/bin/bash
# Gate: {Rule 描述}
# 追溯: Principle P{p}（{Principle 名称}）
# 毕业条件: 连续 30 天不触发后退休

INPUT="${1:-$(cat)}"
# {草稿中确认的检测逻辑}
[ 命中条件 ] && echo "✅ Gate passed: {描述}" && exit 0
echo "❌ GATE BLOCKED: {原因}" && exit 1
```

```bash
chmod +x /workshop/jun.li/governance/gates/check-{slug}.sh
```

**2.5 创建测试文件**

创建 `/workshop/jun.li/governance/tests/test-{slug}.sh`：

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
    echo "❌ FAIL [$label] — 期望 $expect，实际 $exit_code"; FAIL=$((FAIL+1))
  fi
}

echo "=== R{n} {标题} Gate 测试 ==="
run_case "正例" "{正例内容}" "pass"
run_case "反例" "{反例内容}" "fail"

echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

```bash
chmod +x /workshop/jun.li/governance/tests/test-{slug}.sh
```

---

**第三步：验证**

```bash
bash /workshop/jun.li/governance/tests/run-all.sh
```

- **绿灯**：输出蒸馏完成摘要：
  ```
  ✅ Sara 蒸馏完成！

  本次新增：
  - 原则：[复用/新增]
  - 规则：R{n}-{slug}.md
  - 检查点：check-{slug}.sh
  - 测试：test-{slug}.sh（X 个用例全通过）
  ```

- **红灯**：分析失败原因 → 修复 `check-{slug}.sh` → 重新运行 → 直到绿灯
