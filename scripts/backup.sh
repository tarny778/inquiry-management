#!/bin/bash
# 使い方: backup.sh <S3バケット名>
# DBをpg_dump(custom形式)で取得し、S3へ保存する。
set -euo pipefail

APP_DIR="/home/ec2-user/inquiry-management"

main() {
  local bucket="${1:?使い方: backup.sh <S3バケット名>}"
  local ts key tmp

  ts=$(date -u +%Y-%m-%dT%H%MZ)
  key="db/${ts}.dump"
  tmp=$(mktemp /tmp/backup.XXXXXX)
  trap 'rm -f "$tmp"' EXIT

  cd "$APP_DIR"
  local compose=(docker compose --env-file .env.docker -f compose.prod.yaml)

  # DBコンテナ内でpg_dumpを実行し、標準出力(-Fc: custom形式)をファイルへ
  "${compose[@]}" exec -T db \
    pg_dump -U inquiry_app -d inquiry_management -Fc > "$tmp"

  # ダンプが読めるか検査(復元はしない)
  "${compose[@]}" exec -T db pg_restore --list < "$tmp" > /dev/null

  aws s3 cp "$tmp" "s3://${bucket}/${key}" --only-show-errors
  echo "backup OK: s3://${bucket}/${key}"
}

main "$@"