# Sara — 三层治理蒸馏

> Sara（सार）：梵文"精华"。把事件蒸馏成可执行的治理结构。

用法：`/sara <事件描述>`

---

## 执行步骤

**读取事件**

用户输入的事件是：`$ARGUMENTS`

如果 `$ARGUMENTS` 为空，告知用户：请使用 `/sara <事件描述>` 的格式，并停止执行。

---

**第一步：蒸馏 Principle**

先读取现有 Principles：

```bash
cat /workshop/jun.li/governance/principles.md
```

基于事件描述和现有 Principles，向用户提问（一次只问这一个问题，等待用户回答后再继续）：

> 这件事背后，违反了哪条原则？
>
> 候选（可选其一，或自己描述）：
> A. [基于事件内容生成的候选原则1——一句话描述]
> B. [基于事件内容生成的候选原则2——一句话描述]
> C. 已有原则中的某条（列出 P1/P2/P3 的标题供参考）
> D. 自定义（请描述你的原则）

等待用户回答。根据用户回答，确定：
- 如果复用现有 Principle：记录对应编号（如 P1）和标题，不追加 principles.md
- 如果是新 Principle：确定新编号（P4、P5……），准备追加内容

---

**第二步：定义 Rule**

基于用户对 Principle 的回答，向用户提问（一次只问这一个问题，等待用户回答后再继续）：

> 下次遇到同样情况，怎么判断"合格"还是"不合格"？
> 用一句话描述，人拿着这句话就能直接判断。

等待用户回答。将用户答案提炼为 Rule 的判定标准（一句话，人可直接执行）。

---

**第三步：设计 Gate**

基于 Rule 的判定标准，向用户提问（一次只问这一个问题，等待用户回答后再继续）：

> 这个判断能让脚本自动检查吗？
> 脚本应该检查什么信号？（比如：关键词存在与否、文件是否存在、特定格式、命令退出码）

等待用户回答。根据用户描述的检测逻辑，设计 Gate 脚本的具体实现。

---

**第四步：生成文件**

收集三轮回答后，执行以下操作：

**4.1 确定编号和 slug**

```bash
# 获取下一个 Rule 编号
last_n=$(ls /workshop/jun.li/governance/rules/R*.md 2>/dev/null | grep -oE 'R[0-9]+' | grep -oE '[0-9]+' | sort -n | tail -1)
n=$(( ${last_n:-0} + 1 ))
```

从 Rule 标题生成 kebab-case 英文 slug（例如："检查遗留调试代码" → `no-debug-leftovers`）。

**4.2 追加 Principle**（仅当是新 Principle 时）

在 `/workshop/jun.li/governance/principles.md` 末尾追加：

```
## P{n}: {Principle 标题}
**{一句话核心}**

- **描述**：{详细描述}
- **来源**：{事件来源，含日期}
- **判定标准**：{判定标准}
```

**4.3 创建 Rule 文件**

创建 `/workshop/jun.li/governance/rules/R{n}-{slug}.md`，内容为：

```markdown
# Rule R{n}: {标题}

## 追溯
- **Principle**: P{p}（{Principle 名称}）
- **Evidence**: {日期}，{事件描述}

## 判定标准
{用户在第二步给出的标准，一句话}

## 违规示例
{基于事件构造的反例}

## 满足示例
{基于事件构造的正例}

## 过期条件
- 当 Gate `check-{slug}.sh` 稳定运行 30 天后退休
```

**4.4 创建 Gate 脚本**

创建 `/workshop/jun.li/governance/gates/check-{slug}.sh`，内容为：

```bash
#!/bin/bash
# Gate: {Rule 描述}
# 追溯: Principle P{p}（{Principle 名称}）
# 毕业条件: 连续 30 天不触发后退休

INPUT="${1:-$(cat)}"

# {根据第三步用户描述实现的检测逻辑}
# 示例结构：
# if <检测条件命中>; then
#   echo "✅ Gate passed: {描述}"
#   exit 0
# else
#   echo "❌ GATE BLOCKED: {原因}"
#   exit 1
# fi
```

然后执行：
```bash
chmod +x /workshop/jun.li/governance/gates/check-{slug}.sh
```

**4.5 创建测试文件**

创建 `/workshop/jun.li/governance/tests/test-{slug}.sh`，内容为：

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
    echo "❌ FAIL [$label] — 期望 $expect，实际退出码 $exit_code"; FAIL=$((FAIL+1))
  fi
}

echo "=== R{n} {标题} Gate 测试 ==="

# 正例（应通过 Gate）
run_case "正例" "{正例输入内容}" "pass"

# 反例（应被 Gate 拦截）
run_case "反例" "{反例输入内容}" "fail"

echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

然后执行：
```bash
chmod +x /workshop/jun.li/governance/tests/test-{slug}.sh
```

---

**第五步：验证**

运行完整测试套件：

```bash
bash /workshop/jun.li/governance/tests/run-all.sh
```

**如果全部绿灯（exit 0）：**

输出：
```
✅ Sara 蒸馏完成！新洞见已写入治理层。

生成的文件：
- /workshop/jun.li/governance/principles.md （已更新）
- /workshop/jun.li/governance/rules/R{n}-{slug}.md
- /workshop/jun.li/governance/gates/check-{slug}.sh
- /workshop/jun.li/governance/tests/test-{slug}.sh
```

**如果存在红灯（exit 非0）：**

1. 查看失败的测试输出，定位哪个 Gate 测试失败
2. 分析原因：是 Gate 脚本逻辑有误，还是测试用例不匹配 Gate 行为？
3. 修复 `check-{slug}.sh` 的检测逻辑（保持 Gate 语义不变，只修复实现）
4. 重新运行 `bash /workshop/jun.li/governance/tests/run-all.sh`
5. 重复直到全部绿灯
