#!/bin/bash
# 触发时机：Claude Code session 结束时
# 做什么：提取 corrections，追加到 log

AGENTOS_DIR="$(dirname "$(dirname "$0")")"

claude --print "Review this session transcript.
Extract:
1. Any corrections the user made (format: CORRECTION: ...)
2. Any decisions made with rationale (format: DECISION: ...)
3. Any new facts discovered (format: DISCOVERY: ...)
Output ONLY the extracted items, one per line.
If none found, output NONE." \
>> "$AGENTOS_DIR/corrections.log"
