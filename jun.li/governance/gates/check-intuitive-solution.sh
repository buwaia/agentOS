#!/bin/bash
# Gate: 解答必须通俗易懂
# 追溯: Principle P2（AI 输出质量是产品底线）
# 蒸馏自: R003-intuitive-solution
# 毕业条件: 连续 30 天不触发后退休

INPUT="${1:-$(cat)}"

# 检测通俗化信号：生活类比词、画面感词、先给结论的句式
has_analogy=$(echo "$INPUT" | grep -cE '想象|就像|好比|类比|本质是|其实就是|可以理解为|生活中|举个例子|画面|直觉')

# 检测拉马努金/高斯风格：先说结论/现象，再验证
has_intuition_first=$(echo "$INPUT" | grep -cE '先看|首先感受|直觉上|显然|一句话|简单说|核心是')

if [ "$has_analogy" -gt 0 ] || [ "$has_intuition_first" -gt 0 ]; then
  echo "✅ Gate passed: 解答包含通俗类比或直觉性描述"
  exit 0
else
  echo "❌ GATE BLOCKED: 解答缺乏通俗类比，疑似纯符号推导（P2 违规）"
  echo "   建议：加入生活类比、画面感描述，或先说直觉再给证明"
  exit 1
fi
