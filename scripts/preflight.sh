#!/usr/bin/env bash
set -euo pipefail
echo "=== FRAIME LAB Pi preflight (read-only) ==="
uname -a
echo "--- OS ---"; cat /etc/os-release | head -n 6
echo "--- Architecture ---"
arch="$(uname -m)"; echo "$arch"
if [[ "$arch" != "aarch64" ]]; then echo "STOP: 64-bit ARM userspace/kernel required"; exit 1; fi
echo "--- RAM ---"; free -h
echo "--- Root filesystem ---"; df -h /
echo "--- Persistent storage candidates ---"; lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL
echo "--- IP addresses ---"; hostname -I || true
echo "--- Ports 80, 443, 3000, 5001 ---"; sudo ss -ltnp | grep -E ':(80|443|3000|5001)\b' || true
echo "--- Docker ---"
if command -v docker >/dev/null 2>&1; then
  docker version --format 'Server={{.Server.Version}}' || true
  echo "--- Published YSocial image platforms (requires Docker buildx + network) ---"
  docker buildx imagetools inspect ghcr.io/ysocialtwin/ysocial:latest || true
else
  echo 'Docker not installed yet; image check pending'
fi
echo "=== Preflight completed; check image contains linux/arm64 before deploy. ==="
