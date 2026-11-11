# Experimental CPU-only YPhotoSharing image

This is a **non-production build experiment**. Current Dokploy `compose.yaml` intentionally continues running the known-working upstream image `ghcr.io/ysocialtwin/ysocial:v4.0.0`.

## Why
YPhotoSharing v2.1.0's standard install currently pulls PyTorch with CUDA wheels, causing multi-GB container writable growth; Python modules in the writable layer can disappear on re-create. The plugin code itself is already persistent under `/data/external/YPhotoSharing`.

## Design
- Dockerfile.lab installs CPU PyTorch/Torchvision first, then the plugin's full pinned-release requirement list.
- Ship a plugin copy under `/opt/fraime-plugins/YPhotoSharing`.
- At startup seed `/data/external/YPhotoSharing` only if missing, preserving existing plugin data.
- Github Actions builds and smoke-tests without pushing or deploying.
- This does NOT enable local Stable Diffusion and does NOT include any API keys.

## Promotion checklist
1. GitHub Actions build and import smoke checks pass.
2. Review image size, CPU memory behaviour, and `pip check` output.
3. Verify all relevant YPhotoSharing modules import in isolation.
4. Test on a disposable `/data` volume with a *separate* Docker Compose project and port/domain, ensuring no shared SQLite.
5. Check plugin's admin validation and 5-agent experimental run using external LLM, measure spend.
6. Build/push a digest-pinned image, snapshot current named volume before switching main Dokploy Compose.
7. Only then change `compose.yaml` image. Never do `docker compose down -v`.

## Caveat
`Detoxify` is imported eagerly by `YPhotoSharing/YClient/text_support/annotations.py`. Removing it without code changes can break startup. The experimental build therefore keeps it and its CPU-only torch dependency. Any extra optional dependency may still be needed; CI must show this.
