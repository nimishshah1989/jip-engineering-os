#!/bin/bash
INPUT=$(cat)
if echo "$INPUT" | grep -qiE "drop table|truncate table|delete from .{0,60} where 1=1"; then
  echo "🛑 SECURITY: Destructive SQL blocked. Confirm explicitly." >&2; exit 1
fi
if echo "$INPUT" | grep -qiE "rm -rf /|rm -rf ~|> .+\.env$|chmod 777 /"; then
  echo "🛑 SECURITY: Dangerous file op blocked." >&2; exit 1
fi
if echo "$INPUT" | grep -qiE "terminate-instance|delete-db-instance|s3.*rb --force"; then
  echo "🛑 SECURITY: Infrastructure destruction HARD STOP." >&2; exit 1
fi
exit 0
