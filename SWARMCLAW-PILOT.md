# FRAIME Social Lab — SwarmClaw pilot

This branch is an **isolated replacement experiment**, not a patch to YSocial. Its root `compose.yaml` deploys the official SwarmClaw image. No source build or fork is needed.

## Dokploy installation (Surface Pro 9)

1. In Dokploy, create a **NEW Compose application**. Do not reuse the running YSocial service/project until the pilot is validated.
2. Git source: `domonkos-szabo/fraime-ysocial`; branch: `swarmclaw-pilot`; Compose path: `compose.yaml`.
3. Set two separate, randomly generated secrets in Dokploy **Environment**:
   - `ACCESS_KEY` (strong unique key for the web UI/API)
   - `CREDENTIAL_SECRET` (strong stable encryption secret; **never rotate without a recovery plan**)
   Generate individually with `openssl rand -hex 32` on a trusted machine. Do not commit the values.
4. Deploy. The image is `ghcr.io/swarmclawai/swarmclaw:latest`; the persistent named volume maps to `/app/data`.
5. Add a Dokploy domain pointing to **service `swarmclaw`, internal port `3456`**. Use the existing Cloudflare Tunnel / HTTPS routing approach, and restrict public access if possible.
6. Check `/api/healthz` and load the UI. Do not publish port 3456 directly to the host or internet.
7. Start with **one** agent only. Keep autonomous heartbeat, schedules and social posting disabled during setup.

## Local LLM (OlliteRT on Beam Pro)

We have tested this endpoint **from the Ubuntu host**:
- OpenAI-compatible base URL: `http://192.168.68.61:8000/v1`
- Exact current model ID: `Gemma-4-E2B-it`
- `GET /v1/models` returned the model, and a synthetic `comment` tool call succeeded.
- The model has **not yet been tested through SwarmClaw**.

In SwarmClaw settings, add an **OpenAI-compatible custom/local provider** with the exact base URL and model ID. If the UI insists on an API key, use a non-secret placeholder only if OlliteRT accepts it. Keep the URL as configured; check the logs for doubled/missing `/v1`. Do not use `localhost` — inside the container that means the container, **not** the Beam Pro.

No cloud model/API key, cloud fallback, web-search tool or remote embeddings should be configured. Use the platform's local/native memory mode initially.

## Acceptance test

1. Create Giulia Conti (English-speaking Italian sommelier) with a personality prompt and local Gemma.
2. Disable dangerous/default tools: shell, filesystem modification, browser, unattended external messaging and unrestricted network access.
3. Send a harmless chat prompt and verify the reply via Beam Pro logs.
4. Enable only a harmless test tool; verify one tool call and inspect SwarmClaw activity / error logs.
5. Repeat a few **sequential** requests; monitor Beam Pro app stability and container RAM.
6. Only after that, consider connecting a **private, federation-disabled** social platform (Friendica/HumHub/etc.) using separate least-privilege credentials per agent.

## Operations and caveats

- `latest` tracks upstream updates. After the first successful test, pin an **actually published GHCR image tag/digest**, not an assumed version string.
- OlliteRT is an Android app; Android background limits or memory pressure may kill it, especially with Gemma 4 E2B. Use one request at a time initially.
- Native tool calling was observed in a single direct OlliteRT API test; end-to-end agent reliability is not yet known.
- The deployment volume contains agent conversations, memory and credentials. Back it up along with a secure copy of `CREDENTIAL_SECRET`.
- Keep access gated and external capabilities disabled until tested. Check `docker logs`, Dokploy metrics and the built-in SwarmClaw task/agent UI.
- No guaranteed RAM target is claimed for SwarmClaw or the Android model.

## Original YSocial

The YSocial experiment and original Compose/Docker files remain on `main` untouched. This pilot branch replaces only the root Compose specification; it does not delete the YSocial runtime, volumes or its Docker deployment.
