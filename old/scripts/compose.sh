#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker_compose() {
  if docker info >/dev/null 2>&1; then
    docker compose "$@"
    return
  fi

  echo "docker daemon needs sudo on this machine. Falling back to sudo docker compose..." >&2
  sudo -E docker compose "$@"
}

cd "$ROOT_DIR"
docker_compose "$@"
