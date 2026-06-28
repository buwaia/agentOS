#!/bin/bash
GATE="$(dirname "$0")/../gates/check-story-in-solution.sh"
PASS=0; FAIL=0

run_case() {
  local label="$1"; local input="$2"; local expect="$3"
  result=$(echo "$input" | bash "$GATE" 2>&1); exit_code=$?
  if [ "$expect" = "pass" ] && [ $exit_code -eq 0 ]; then
    echo "✅ PASS [$label]"; PASS=$((PASS+1))
  elif [ "$expect" = "fail" ] && [ $exit_code -ne 0 ]; then
    echo "✅ PASS [$label] (正确拦截)"; PASS=$((PASS+1))
  else
    echo "❌ FAIL [$label] — 期望 $expect，实际退出码 $exit_code，输出：$result"; FAIL=$((FAIL+1))
  fi
}

echo "=== R4 解析必须包含故事或场景描述 Gate 测试 ==="

# 正例：包含叙事词汇，应通过
run_case "含故事描述" "想象你有两根绳子，一根长a一根长b，它们围成的矩形面积是ab，但正方形面积更大，这就是AM-GM的直觉。" "pass"

# 正例：包含类比词汇，应通过
run_case "含类比描述" "就像水往低处流，电流也总是沿着阻力最小的路径走，这就是为什么并联电路中电流分配不均。" "pass"

# 反例：连续4行纯公式，应被拦截
run_case "连续公式超3行" "a + b >= 2*sqrt(ab)
(a+b)^2 >= 4ab
a^2 + 2ab + b^2 >= 4ab
a^2 - 2ab + b^2 >= 0
(a-b)^2 >= 0" "fail"

# 反例：无叙事词汇也无连续公式，应被拦截
run_case "纯文字但无叙事" "根据定理可得结论成立。证明如下：条件满足时命题为真。" "fail"

echo "结果：$PASS 通过 / $FAIL 失败"
[ $FAIL -eq 0 ] && exit 0 || exit 1
