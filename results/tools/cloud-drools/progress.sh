#!/bin/sh
# Append a progress line and push: progress.sh PCT "done" "next" "ETA"
cd "$(dirname "$0")/../../.." || exit 1
F=results/tools/cloud-drools/PROGRESS.md
[ -f "$F" ] || printf '# Cloud Drools/KIE re-run progress\n\n' > "$F"
echo "$(date -u '+%Y-%m-%d %H:%M UTC') — $1% — $2 — next: $3 — ETA $4" >> "$F"
git add results/tools/cloud-drools
git commit -q -m "cloud-drools: progress $1%" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VuRqbbJaACiHsRRWtQTsTc"
for i in 2 4 8 16; do git push -q -u origin cloud-drools-runs && break; sleep $i; done
