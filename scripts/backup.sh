#!/bin/bash
# 使い方: backup.sh <S3バケット名>
# DBをpg_dump(custom形式)で取得し、S3へ保存する。
set -euo pipefail

APP_DIR="/home/ec2-user/inquiry-management"
TMP_FILE=""

cleanup() {
  [ -n "$TMP_FILE" ] && rm -f "$TMP_FILE"
  return 0
}

main() {
  local bucket="${1:?使い方: backup.sh <S3バケット名>}"
  local ts key

  ts=$(date -u +%Y-%m-%dT%H%MZ)
  key="db/${ts}.dump"
  TMP_FILE=$(mktemp /tmp/backup.XXXXXX)
  trap cleanup EXIT

  cd "$APP_DIR"
  local compose=(docker compose --env-file .env.docker -f compose.prod.yaml)

  # DBコンテナ内でpg_dumpを実行し、標準出力(-Fc: custom形式)をファイルへ
  "${compose[@]}" exec -T db \
    pg_dump -U inquiry_app -d inquiry_management -Fc > "$TMP_FILE"

  # ダンプが読めるか検査(復元はしない)
  "${compose[@]}" exec -T db pg_restore --list < "$TMP_FILE" > /dev/null

  aws s3 cp "$TMP_FILE" "s3://${bucket}/${key}" --only-show-errors
  echo "backup OK: s3://${bucket}/${key}"
}

main "$@"