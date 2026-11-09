#!/bin/bash
# 使い方: deploy.sh [イメージタグ]   (省略時は latest)
set -euo pipefail

APP_DIR="/home/ec2-user/inquiry-management"
REGION="ap-northeast-1"

main() {
  local tag="${1:-latest}"

  # 同時実行を防ぐ(起動時のデプロイとActionsのデプロイが重なる場合など)
  exec 9>/tmp/deploy.lock
  flock 9

  cd "$APP_DIR"
  git pull --ff-only

  set_env IMAGE_TAG "$tag"
  local registry
  registry=$(grep '^ECR_REGISTRY=' .env.docker | cut -d= -f2)

  aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin "$registry"

  local compose=(docker compose --env-file .env.docker -f compose.prod.yaml)
  "${compose[@]}" pull
  "${compose[@]}" up -d

  # 起動確認(db, backend, web の3つが running か)
  sleep 10
  local running
  running=$("${compose[@]}" ps --status running --services | wc -l)
  if [ "$running" -lt 3 ]; then
    echo "ERROR: コンテナが3つ起動していません" >&2
    "${compose[@]}" ps >&2
    exit 1
  fi

  docker image prune -f
  echo "deploy OK: tag=$tag"
}

set_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" .env.docker; then
    sed -i "s|^${key}=.*|${key}=${val}|" .env.docker
  else
    echo "${key}=${val}" >> .env.docker
  fi
}

main "$@"
exit