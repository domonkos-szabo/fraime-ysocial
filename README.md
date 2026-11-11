# FRAIME Social Lab — Raspberry Pi 4 (4 GB RAM)

**Status: prepared; NOT deployed.** This repo provides a minimal YSocial 4.x Docker Compose pilot for a *separate* LAB Dokploy on a Raspberry Pi 4, with remote LLM inference. It does not configure cloud credentials or Cloudflare DNS.

## Design decisions
- 64-bit OS (`aarch64`), ideally Ubuntu Server 24.04 LTS ARM64.
- Prefer USB 3 SSD; do not place the Docker data root on an SD card for sustained operation.
- 4 GB RAM is tight: reserve capacity for OS, Dokploy/Traefik and tunnel; YSocial limited to 1.5 GiB/2 CPUs.
- Use the upstream GHCR image **only after verifying that its manifest includes linux/arm64**. An ARM64 AppImage does NOT guarantee an ARM64 Docker image.
- SQLite named volume `ysocial-data`, bound only to `127.0.0.1:5001` on the Pi. No direct public port.
- External OpenAI-compatible LLM configured inside YSocial's admin UI, with provider-side hard spend caps.
- No GPU, Ollama, PostgreSQL, local toxicity model, or continuous high-volume simulation in v0.1.

## Step 1: Pi health check (no changes)
On the Pi via SSH:
```bash
git clone https://github.com/domonkos-szabo/fraime-ysocial.git
cd fraime-ysocial
bash scripts/preflight.sh
```
Because this repository may be private, use your authenticated GitHub access or download the files separately. Paste back output of `uname -m`, `free -h`, `df -h /`, `lsblk`, and the image manifest. **Do not paste secrets**.

## Step 2: Dokploy (only after preflight)
Official installation guide: https://docs.dokploy.com/docs/core/installation
- Dokploy's documented minimum is 2 GB RAM / 30 GB disk; Pi 4 4 GB leaves limited headroom.
- Verify ports 80/443/3000 free and accessible only as intended.
- Use the official install script after inspecting it, and preferably set the Docker data root on SSD first.
- In a separate Dokploy instance, create project `LAB` and compose app `fraime-social-lab` from this repo's `compose.yaml`.
- Configure a Cloudflare Tunnel separately with access control to `http://localhost:5001`. If tunnel is in Docker, point it at the host appropriately; localhost inside its container is not the Pi host.

## Step 3: ARM64 image verification
After Docker is installed:
```bash
docker buildx imagetools inspect ghcr.io/ysocialtwin/ysocial:latest
```
Look for `linux/arm64`. **If absent, stop.** The documented alternative is a reviewed ARM64 build of YSocial 4.x, not forced amd64 emulation on 4 GB hardware.

## Step 4: YSocial pilot
- Start UI first, verify persistence over one restart.
- Configure a *remote* LLM endpoint using the admin settings; never commit API keys.
- Begin with 5 agents and a short, manually triggered experiment. Monitor `docker stats`, `free -h`, disk, CPU temperature/throttling.
- Increase to 20–50 agents only after measuring memory, latency, token spend, and Docker health.
- Keep the real FRAIME connectors untouched until a separate read-only adapter is tested.

## Cautions
- Verify upstream 4.x release behavior against this Compose file before deployment, and pin the validated image digest instead of `latest`.
- The image is configured by upstream to persist files in `/data`; validate the actual contents and restore procedure.
- Back up the Docker volume when experiments matter (prefer quiesced or application-consistent backup).
- Avoid exposing the UI publicly without Cloudflare Access or equivalent authentication.
- This lab does **not** emulate Meta Graph API behavior. It produces simulated social activity for a FRAIME adapter.
