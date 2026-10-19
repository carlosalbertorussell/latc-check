#!/bin/sh
# watch_long.sh PID LABEL PCT_START PCT_END NEXT CAP_S: sample the JVM RSS every 60 s into
# $LIVE/<label>.rss.tsv (default /home/user/work; progress.sh copies it into raw/) and push a PROGRESS.md line every ~9 min until PID exits.
PID=$1; LABEL=$2; P0=$3; P1=$4; NEXT=$5; CAP=$6
HERE=$(cd "$(dirname "$0")" && pwd); OUT=${LIVE:-/home/user/work}/$LABEL.rss.tsv; START=${START:-$(date +%s)}; n=0
[ -f "$OUT" ] || printf 'utc\telapsed_s\tjava_rss_mb\tjava_cpu_pct\n' > "$OUT"
while kill -0 "$PID" 2>/dev/null; do
  J=$(pgrep -n -x java); E=$(( $(date +%s) - START ))
  if [ -n "$J" ]; then ps -o rss=,pcpu= -p "$J" | awk -v t="$(date -u +%H:%M:%S)" -v e="$E" '{printf "%s\t%d\t%.0f\t%s\n", t, e, $1/1024, $2}' >> "$OUT"; fi
  n=$((n+1))
  if [ $((n % 9)) -eq 0 ]; then
    R=$(tail -1 "$OUT" | cut -f3); M=$(( E / 60 )); P=$(( P0 + (P1 - P0) * E / CAP ))
    ETA=$(date -u -d "@$(( START + CAP ))" +%H:%M)
    "$HERE/progress.sh" "$P" "$LABEL still running, ${M} min in, JVM RSS ${R} MB" "$NEXT" "cap at ${ETA} UTC"
  fi
  sleep 60
done
