#!/usr/bin/env bash
# Inspect the FRAIME HPC experiment even if the app container is stopped.
# Starts ONLY a short-lived, network-disabled Python diagnostic process.
set -euo pipefail

container="${1:-fraime-ysocial-4wc0zu-ysocial-1}"
stage="${2:-prestart}"
experiment_dir="${3:-/data/y_web/experiments/4ac21989_0e3e_400d_989d_11d2b2d71048}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
image="$(docker inspect "$container" --format '{{.Image}}')"

echo "=== Container (no changes) ==="
docker inspect "$container" --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}} RestartCount={{.RestartCount}}'
echo "=== Host memory ==="
free -h
echo "=== Last container log lines ==="
docker logs --tail 70 "$container" 2>&1 || true
echo "=== Experiment preflight ==="
docker run --rm --network none --read-only --memory 128m --pids-limit 32 \
  --volumes-from "$container":ro \
  -v "$script_dir/hpc-preflight.py:/tmp/fraime-hpc-preflight.py:ro" \
  --entrypoint python "$image" /tmp/fraime-hpc-preflight.py \
  --root "$experiment_dir" --stage "$stage"
