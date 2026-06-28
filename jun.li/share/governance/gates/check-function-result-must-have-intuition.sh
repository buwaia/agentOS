#!/bin/bash
# Gate: 函数解答结果必须有直觉性解释
# 追溯: Principle P1（洞见优先于推导）
# 毕业条件: 连续 30 天不触发后退休

INPUT="${1:-$(cat)}"

if echo "$INPUT" | grep -qE '因为|所以|相当于|可以理解为|图像|可以看出|即.*表示|意味着'; then
  echo "✅ Gate passed: 包含直觉性解释"
  exit 0
fi

echo "❌ GATE BLOCKED: 函数解答缺少直觉性解释（需包含"因为/所以/相当于/可以理解为/图像/可以看出"等解释性结构）"
exit 1
