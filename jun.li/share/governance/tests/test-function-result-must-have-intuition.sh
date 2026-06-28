#!/bin/bash
GATE="$(dirname "$0")/../gates/check-function-result-must-have-intuition.sh"
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

echo "=== R5 函数解答结果必须有直觉性解释 Gate 测试 ==="
run_case "有因为/所以" "因为斜率为零，所以这是最大值 3" "pass"
run_case "有可以理解为" "可以理解为图像到达山顶，最大值是 3" "pass"
run_case "有图像" "从图像上看，f(x) 在 x=1 处取到最大值 3" "pass"
run_case "只有结论" "f(x) 的最大值为 3" "fail"
run_case "纯公式推导" "令 f'(x)=0，解得 x=1，代入得 f(1)=3" "fail"

echo ""
echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
