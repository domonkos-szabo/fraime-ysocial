# Beam Pro / YPhotoSharing OpenAI-compatible LLM fix

## Confirmed diagnosis
The Beam Pro at `http://192.168.68.61:8000/v1/chat/completions` returned HTTP 200 and generated Italian text from `Qwen2.5-1.5B-Instruct`. However the pinned YPhotoSharing v2.1.0 `LLMService` unconditionally instantiated `ChatOllama` and ignored `llm.base_url`/API key, so the OpenAI-compatible endpoint was not used.

The existing 48-round experiment has photos with captions `#general` or empty strings and rule-based stories. **Do not edit, reset, or delete this experiment.**

## Image patch
`scripts/patch-photo-llm.py` patches only the installed YPhotoSharing LLM module. It supports explicit `backend: openai_compatible`, `openai`, or `openai-compatible`; old configs with `backend: ollama` and a `/v1` base URL are also detected automatically. True Ollama endpoints remain supported.

It logs LLM success, empty results and failures without logging API keys or raw prompts. It is idempotent, fails on unexpected upstream code, and preserves a `.fraime-original.bak` of the old plugin file. The image contains `langchain-openai`. The entrypoint patches existing persistent plugin installations in `/data/external/YPhotoSharing` rather than replacing the plugin directory.

## Activation (requires explicit deployment)
1. Confirm that the latest **Build and optionally publish CPU-only YSocial lab image** GitHub Actions run passed.
2. Use its immutable `sha-<commit>` GHCR image tag in `compose.yaml`, then deploy via Dokploy. No image tag is updated automatically.
3. Keep the `ysocial-data` named volume. Never execute `docker compose down -v`.
4. After deployment, confirm `ChatOpenAI` import works inside the container, and that the file `/data/external/YPhotoSharing/YPhotoSharing/YClient/LLM_interactions/llm_service.py` contains `FRAIME LLM success template=`.
5. Create a **fresh experiment** and select five wine pilot agents. An old completed client won't rerun from the beginning without changing its state; do not reset the old state.
6. For a fresh, unstarted experiment, use `python scripts/prepare-wine-pilot.py <experiment-dir>` first as a dry-run and repeat with `--apply` to back up and set agent interests explicitly. The script refuses an experiment with any client state JSON.
7. Configure the new client to use `Qwen2.5-1.5B-Instruct` at `http://192.168.68.61:8000/v1`, with `llm.backend=openai_compatible`. Run only a short test.
8. Verify non-empty, topic-specific captions in the new experiment SQLite `photos.caption` and verify the client/Ray logs contain `FRAIME LLM success` and no `FRAIME LLM failed`.

Note: changing the agent population JSON after agents have already been imported does not retroactively update the existing users in the database. New topics should be tested in a newly created experiment.

## Security
Do not commit API credentials or print entire client configurations. The Beam Pro server should remain reachable only from the intended LAN. Avoid storing raw generated prompts and replies unless necessary for diagnostic consent.
