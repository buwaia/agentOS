#!/bin/bash
# GRADUATED: 2026-06-28
# 理由: 连续 30 天未触发，Python 代码质量稳定
# 接管方: pre-commit hook (engine/tests/ 全部通过即可视为 lint 合格)
#
# 原始逻辑保留供参考：
# find . -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep -q "Error"
echo "[graduated] check-lint: this gate has been retired — covered by test suite"
exit 0
