#!/bin/bash
# Gate: 解答必须包含直觉性描述
# 追溯: Principle P1 "洞见优先于推导"
# 蒸馏自: R001-answer-must-have-intuition
# 毕业条件: 连续 30 天不触发，或解析 prompt 内置形象化要求后退休

# 用法: echo "解答内容" | bash check-answer-quality.sh
# 或:   bash check-answer-quality.sh "解答内容"

ANSWER="${1:-$(cat)}"

# 检测几何图示（仅 box-drawing 字符和箭头，排除数学公式中的 / \ |）
has_diagram=$(echo "$ANSWER" | grep -cE '[│─┼↑←→↗]|[┌┐└┘├┤┬┴┼]')

# 检测自然语言类比（排除纯数学术语"几何均值"等）
has_analogy=$(echo "$ANSWER" | grep -cE '就像|想象|本质是|看见|直觉|类比|形象|半圆|圆|弦|垂线')

# 检测直觉先于推导（结论句在前）
has_intuition_first=$(echo "$ANSWER" | grep -cE '因此|所以|答案是|结论' | head -1)

if [ "$has_diagram" -gt 0 ] || [ "$has_analogy" -gt 0 ]; then
  echo "✅ Gate passed: 解答包含直觉性描述"
  exit 0
else
  echo "❌ GATE BLOCKED: 解答缺乏图示或类比，疑似机械推导（P1 违规）"
  echo "   建议：添加几何图示、自然语言类比、或直觉性结论"
  exit 1
fi
