#!/usr/bin/env bash
# 사용법: deploy/restore.sh backups/meetpoint-YYYYmmdd-HHMMSS.dump
# 현재 DB 내용을 백업 내용으로 덮어쓴다. 앱을 멈춘 뒤 실행한다.
set -euo pipefail
cd "$(dirname "$0")/.."
dump="${1:?복원할 덤프 파일을 지정하세요}"
docker compose stop app
docker compose exec -T db pg_restore -U meetpoint -d meetpoint --clean --if-exists < "$dump"
docker compose start app
echo "restored from $dump"
