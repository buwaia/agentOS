#!/bin/bash
# 业务验证：检查 Delivery Engine API 输出 schema

set -uo pipefail

BASE="${BASE_URL:-http://localhost:8000}"
PASS=0
FAIL=0

check() {
  local name="$1" result="$2" expected="$3"
  if echo "$result" | grep -q "$expected" 2>/dev/null; then
    echo "  PASS: $name"; PASS=$((PASS+1))
  else
    echo "  FAIL: $name (expected '$expected')"; FAIL=$((FAIL+1))
  fi
}

echo "=== Business Verification: Delivery Engine ==="
echo "Target: $BASE"
echo ""

# 1. API 健康检查
echo "--- Schema Verification ---"
JOBS=$(curl -s "$BASE/jobs")
check "GET /jobs returns array" "$JOBS" '"job_id"'

# 2. Job schema 字段检查
FIRST=$(echo "$JOBS" | python3 -c "import sys,json; jobs=json.load(sys.stdin); print(json.dumps(jobs[0]) if jobs else '{}')" 2>/dev/null)
check "Job has status field"        "$FIRST" '"status"'
check "Job has current_stage field" "$FIRST" '"current_stage"'
check "Job has problem field"       "$FIRST" '"problem"'
check "Job has gate_history field"  "$FIRST" '"gate_history"'

# 3. confidence 字段 [0,1]
echo ""
echo "--- Confidence Contract ---"
ARTIFACTS=$(curl -s "$BASE/jobs/$(echo "$FIRST" | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)/artifacts/UNDERSTAND" 2>/dev/null)
CONF=$(echo "$ARTIFACTS" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    c=d.get('payload',{}).get('confidence',None)
    print('ok' if c is not None and 0<=float(c)<=1 else 'fail')
except: print('skip')
" 2>/dev/null)
check "UNDERSTAND artifact confidence in [0,1]" "$CONF" "ok"

# 4. DISTILL# 事件存在
echo ""
echo "--- Distill Events ---"
TODAY=$(date -u +%Y-%m-%d)
DISTILL=$(aws dynamodb query \
  --table-name DeliveryEngineLocal \
  --region us-east-1 \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values "{\":pk\":{\"S\":\"DISTILL#${TODAY}\"}}" \
  --output json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Count'])" 2>/dev/null || echo "0")
check "DISTILL events exist today ($DISTILL)" "$DISTILL" "[1-9]"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ $FAIL -eq 0 ] && exit 0 || exit 1
