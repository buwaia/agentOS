#!/bin/bash
# Gate: 解析必须包含故事或场景描述，纯公式连续超过3行不合格
# 追溯: Principle P2（AI 输出质量是产品底线）
# 毕业条件: 连续 30 天不触发后退休

INPUT="${1:-$(cat)}"

# 负向检测：连续超过3行以公式符号为主的行
formula_line_pattern='[=+\-^\/\\][^a-zA-Z一-鿿]{0,}$|\\frac|\\sqrt|\\sum|\\int|[0-9][=+\-^][0-9]'
consecutive=0
max_consecutive=0
while IFS= read -r line; do
  if echo "$line" | grep -qE '[=+^\\]|\\frac|\\sqrt|\\sum|\\int' && ! echo "$line" | grep -qE '[，。？！、]|[a-zA-Z]{4,}'; then
    consecutive=$((consecutive + 1))
    [ $consecutive -gt $max_consecutive ] && max_consecutive=$consecutive
  else
    consecutive=0
  fi
done <<< "$INPUT"

if [ $max_consecutive -gt 3 ]; then
  echo "❌ GATE BLOCKED: 连续 $max_consecutive 行纯公式，超过3行上限"
  exit 1
fi

# 正向检测：是否包含叙事性词汇
narrative_pattern='想象|比如|有一天|故事|场景|就像|好比|举个例子|假设你|想一想|试想|类比|形象'
if echo "$INPUT" | grep -qE "$narrative_pattern"; then
  echo "✅ Gate passed: 解析包含故事或场景描述"
  exit 0
fi

echo "❌ GATE BLOCKED: 解析缺少故事或场景描述（未找到叙事性词汇）"
exit 1
