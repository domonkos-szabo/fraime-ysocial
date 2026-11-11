# FRAIME Social Lab — Surface / Dokploy

**Primary deployment target: Surface Pro 9 (Ubuntu x86_64), existing Dokploy.**

This repository launches one [YSocial 4.0](https://github.com/YSocialTwin/YSocial) instance for a small controlled social simulation. It does not modify any production FRAIME modules.

## Quick deploy (Dokploy)
1. In the existing Surface Dokploy create a **Project** `FRAIME LAB` (or reuse a lab project).
2. Add **Compose** service `fraime-ysocial`; source **GitHub**: `domonkos-szabo/fraime-ysocial`, branch `main`, Compose path **`compose.yaml`** (repository root). Repo is private, so grant the Dokploy GitHub integration access.
3. Ensure **Docker Compose** mode (not Docker Stack), then **Deploy**. This pulls upstream `ghcr.io/ysocialtwin/ysocial:v4.0.0` and creates the Docker named volume; no application build required.
4. In **Domains**, attach a new internal service domain to **service `ysocial`**, **port `5000`**, and use your established Dokploy/Traefik routing. For Cloudflare Tunnel, route the hostname to your existing Traefik HTTP entrypoint (for your setup, `http://localhost:80`) and protect it with **Cloudflare Access** before logging in.
5. In Dokploy **Logs**, confirm the web server is listening. In a browser, complete login and **immediately change any default admin password**. Upstream docs list `admin@y-not.social` / `admin` as initial credentials: NEVER leave this reachable without Access.
6. In YSocial admin configure a **remote OpenAI-compatible LLM**. The Docker image does not ship an LLM server. Keep provider credentials out of Git and set a strict spend cap.
7. Start a manually triggered experiment with **5 agents**. Monitor RAM, CPU and disk before increasing to 20–50.

## Safety and limits
- 1.5 GiB max memory, 2 CPUs, 30 MiB rolling container logs, 256 PIDs.
- No host port is published: only Docker internal `5000` is exposed for the Dokploy domain proxy.
- Data persists in `ysocial-data:/data`. Back up as required; never use `docker compose down -v` or delete the named volume inadvertently.
- On the already-busy Surface, check `df -h /`, `free -h`, `docker system df` **before deploy** and monitor the host during a small test.
- The YSocial UI is **not a Meta Graph API emulator**. FRAIME will need a separate read-only connector/adapter for simulated data.
- Image tag `v4.0.0` must be verified pullable on the host. If the image tag is unavailable, check the upstream GHCR tags rather than silently switching to `latest`. Pin a digest after first successful pull.
- No local Ollama, PostgreSQL or optional ML classifiers in this pilot.
- Cloudflare Tunnel is an external infrastructure change and is **not** configured by this repository.

## Deployment variants
- `compose.yaml`: preferred Surface / existing Dokploy deployment.
- `deploy/pi/compose.yaml`: preserved experimental Raspberry Pi 4 setup; **not** used by the Surface application until separately validated.
- `scripts/preflight.sh`: Pi-specific read-only preflight.

## Troubleshooting
- **Image pull error:** confirm GHCR tag and registry access; check Docker image manifest on host.
- **Bad Gateway / 404:** ensure Dokploy domain points to service `ysocial` port `5000`, and Cloudflare Tunnel points at your existing Traefik port 80.
- **Out of memory:** reduce simulation and inspect `docker stats`; avoid increasing the limit without checking the host.
- **No agent output:** configure a working remote LLM endpoint/model in YSocial admin.
- **Data disappeared:** verify the named volume is attached; inspect Dokploy deployments without deleting volumes.

Official references: https://docs.dokploy.com/docs/core/docker-compose , https://docs.dokploy.com/docs/core/github , https://github.com/YSocialTwin/YSocial


## FRAIME HPC / Ray incident test (November 2026)
The Photo Sharing pilot `FRAIME Social Lab 002 - Beam Pro` imported successfully but its HPC server did not write `ray_config.temp`; the client remained at 0/24 simulated hours. A missing `prompts_ygram.json` was fixed manually. **Do not fabricate Ray marker files**: they must be written by the running Ray server.

**While YSocial is stopped**, get reproducible, read-only diagnostics from the Surface host (not inside the container):

```bash
git clone https://github.com/domonkos-szabo/fraime-ysocial.git
cd fraime-ysocial
# or update an existing checkout to the branch containing these scripts
bash scripts/diagnose-hpc.sh
```

The diagnostic helper reads Docker state and logs, then runs a **short-lived** container with the stopped service's volumes **read-only**, network disabled, 128 MiB memory and 32 PID limits. It checks:
- `server_config.json`, `prompts_ygram.json`, client JSON validity
- configured LLM HTTP endpoint and model (without printing API keys)
- `ray_config.temp` and `ray_ready.temp` markers
- recent experiment logs, which may contain sensitive content: **review before sharing**

After starting **only the experiment server**, run `bash scripts/diagnose-hpc.sh fraime-ysocial-4wc0zu-ysocial-1 server`. A missing Ray marker is an explicit FAIL. Do not click **Run Client** until the server-stage check passes. If it fails, investigate experiment server logs rather than restarting the container repeatedly.

The Docker Compose test limits are now 2 GiB RAM, 2 CPUs, 384 PIDs and 256 MiB `/dev/shm`. This is **not a guarantee Ray will start** on a host with 15 GiB shared across many services and no swap. Review available host memory before deployment. The compose image remains pinned to the **existing digest**; it does not auto-build or deploy changes from `Dockerfile.lab`. Changes are inactive until the compose config is explicitly deployed in Dokploy.

**Recovery safety:** Never remove `ysocial-data` or use `docker compose down -v`. The diagnostic is non-destructive and does not modify the experiment.
