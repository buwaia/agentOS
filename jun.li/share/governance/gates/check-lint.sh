#!/bin/bash
# Gate: 代码必须通过 lint 检查
# 追溯: Principle P1 "洞见优先于推导 — 完成 = 不主动破坏"
# 毕业条件: 连续 60 天不触发

# 检查 Python 文件的基本格式
if find . -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep -q "Error"; then
  echo "❌ GATE BLOCKED: Python 语法错误"
  exit 1
fi

echo "✅ Gate passed: lint check"
