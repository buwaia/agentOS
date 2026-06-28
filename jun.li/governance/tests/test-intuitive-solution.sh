#!/bin/bash
# 测试 check-intuitive-solution.sh
# 验证 Rule R003: 解答必须通俗易懂

GATE="$(dirname "$0")/../gates/check-intuitive-solution.sh"
PASS=0; FAIL=0

run_case() {
  local label="$1"; local input="$2"; local expect="$3"
  result=$(bash "$GATE" "$input" 2>&1); exit_code=$?
  if [ "$expect" = "pass" ] && [ $exit_code -eq 0 ]; then
    echo "✅ PASS [$label]"; PASS=$((PASS+1))
  elif [ "$expect" = "fail" ] && [ $exit_code -ne 0 ]; then
    echo "✅ PASS [$label] (正确拦截)"; PASS=$((PASS+1))
  else
    echo "❌ FAIL [$label] 期望=$expect 实际=$([ $exit_code -eq 0 ] && echo pass || echo fail)"
    echo "   输出: $result"; FAIL=$((FAIL+1))
  fi
}

echo "=== R003 通俗易懂 Gate 测试 ==="
echo ""
echo "--- 正例（应通过）---"
run_case "生活类比" \
  "想象一条一直往上爬的山路，x³+2x 就是这样，x 越大值越大" \
  "pass"

run_case "先给直觉" \
  "直觉上很明显：这个函数一直在涨，简单说就是斜率永远为正" \
  "pass"

run_case "画面感描述" \
  "可以理解为一根弹簧，越拉越长，从不回头" \
  "pass"

echo ""
echo "--- 反例（应拦截）---"
run_case "纯符号推导" \
  "f(x₁)-f(x₂)=(x₁-x₂)(x₁²+x₁x₂+x₂²+2)，因x₁<x₂故差<0" \
  "fail"

run_case "纯教材语言" \
  "由单调递增定义，取x₁<x₂，作差后因式分解，判断符号即可得证" \
  "fail"

echo ""
echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
