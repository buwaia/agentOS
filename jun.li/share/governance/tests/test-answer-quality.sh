#!/bin/bash
# 测试 check-answer-quality.sh
# 验证 Rule R001: 解答必须包含直觉性描述

GATE="$(dirname "$0")/../gates/check-answer-quality.sh"
PASS=0
FAIL=0

run_case() {
  local label="$1"
  local input="$2"
  local expect="$3"  # "pass" or "fail"

  result=$(bash "$GATE" "$input" 2>&1)
  exit_code=$?

  if [ "$expect" = "pass" ] && [ $exit_code -eq 0 ]; then
    echo "✅ PASS [$label]"
    PASS=$((PASS+1))
  elif [ "$expect" = "fail" ] && [ $exit_code -ne 0 ]; then
    echo "✅ PASS [$label] (正确拦截)"
    PASS=$((PASS+1))
  else
    echo "❌ FAIL [$label] 期望=$expect 实际=$([ $exit_code -eq 0 ] && echo pass || echo fail)"
    echo "   输出: $result"
    FAIL=$((FAIL+1))
  fi
}

echo "=== R001 解答质量 Gate 测试 ==="
echo ""
echo "--- 正例（应通过）---"
run_case "半圆几何类比" \
  "在直径为 a+b 的半圆里，垂线长度 = √(ab)，垂线不超过半径，几何事实直接给出结论" \
  "pass"

run_case "ASCII 图示" \
  "画出坐标轴：│ ← 这条垂线就是 √(ab)，半径是 (a+b)/2" \
  "pass"

run_case "想象类比" \
  "想象一根绳子，两端固定，中点永远比端点低——这就是凹函数的本质" \
  "pass"

echo ""
echo "--- 反例（应拦截）---"
run_case "纯符号推导" \
  "f''(x) = -1/x^2 < 0，由 Jensen 不等式，f((a+b)/2) >= (f(a)+f(b))/2，两边取 exp 得结论" \
  "fail"

run_case "纯文字无类比" \
  "因为函数是凹函数，所以由定义可知中点函数值大于等于端点函数值的平均，得证" \
  "fail"

echo ""
echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
