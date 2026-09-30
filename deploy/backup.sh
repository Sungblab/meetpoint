#!/usr/bin/env bash
# DB를 backups/ 에 덤프하고 7일 넘은 백업을 지운다.
# cron 예: 0 * * * * /home/ubuntu/apps/meetpoint/deploy/backup.sh >> /home/ubuntu/apps/meetpoint/backups/backup.log 2>&1
set -euo pipefail
# 덤프에는 참가자 연락처가 들어 있다. 서버의 다른 사용자가 읽지 못하게 파일과 폴더를 나만 읽게 만든다.
umask 077
cd "$(dirname "$0")/.."
mkdir -p backups
ts=$(date +%Y%m%d-%H%M%S)
out="backups/meetpoint-$ts.dump"
docker compose exec -T db pg_dump -U meetpoint -d meetpoint --format=custom > "$out.tmp"
mv "$out.tmp" "$out"
find backups -name 'meetpoint-*.dump' -mtime +7 -delete
echo "$(date -Is) backup ok: $out"
