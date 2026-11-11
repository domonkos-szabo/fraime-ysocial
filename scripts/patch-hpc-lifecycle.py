#!/usr/bin/env python3
"""Patch exactly the pinned YSocial 4.0.0 package at image build time.

Refuse to build if upstream code changes, to avoid silent invalid runtime edits.
Only modifies files inside this experimental image, never the host or /data.
"""
from importlib.util import find_spec
from pathlib import Path
import py_compile

spec = find_spec("y_web")
if not spec or not spec.origin:
    raise SystemExit("Cannot locate installed y_web package")
root = Path(spec.origin).parent
print("[FRAIME] patching installed YSocial at", root)

def patch(path, needle, replacement):
    target = root / path
    original = target.read_text(encoding="utf-8")
    count = original.count(needle)
    if count != 1:
        raise RuntimeError(f"Unexpected YSocial version in {path}: marker count={count}")
    updated = original.replace(needle, replacement, 1)
    target.write_text(updated, encoding="utf-8")
    py_compile.compile(str(target), doraise=True)
    print("[FRAIME] patched", path)

server = "src/hpc/server.py"
# The upstream process is detached but inherits an unreliable parent stdout/stderr.
# Persist Python traceback and all Ray bootstrap output in the experiment's volume.
patch(server,
'''                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    env=env,
                )
            print(f"Server process started with PID: {process.pid}")
        except Exception as e:
            # Fallback: try to use the current Python implicitly''',
'''                bootstrap_path = os.path.join(exp_folder, "logs", "hpc_server_bootstrap.log")
                os.makedirs(os.path.dirname(bootstrap_path), exist_ok=True)
                # Keep one previous bootstrap log to avoid filling the disk.
                if os.path.exists(bootstrap_path) and os.path.getsize(bootstrap_path) > 5 * 1024 * 1024:
                    os.replace(bootstrap_path, bootstrap_path + ".1")
                # Appends across starts; survives an app/container crash.
                with open(bootstrap_path, "ab", buffering=0) as bootstrap_log:
                    bootstrap_log.write(
                        (f"\\n=== FRAIME HPC server start: {time.strftime('%Y-%m-%dT%H:%M:%S%z')} "
                         f"experiment={exp.idexp} ===\\n").encode()
                    )
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.DEVNULL,
                        stdout=bootstrap_log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                        env={**env, "PYTHONUNBUFFERED": "1"},
                    )
                print(f"[FRAIME HPC] bootstrap_log={bootstrap_path} pid={process.pid}", flush=True)
            print(f"Server process started with PID: {process.pid}")
        except Exception as e:
            # Fallback: try to use the current Python implicitly''')

# Client startup must not wait 180s for Ray when the server PID already died.
client = "src/hpc/client.py"
patch(client,
'''    # Validate ray_config.temp exists (required for HPC client startup).
    # Local Ray bootstrap can exceed a minute on some machines, so keep the''',
'''    # FRAIME guard: a stale UI/database running flag is NOT Ray readiness.
    # Block clients until real Ray markers exist and the HPC server PID is alive.
    from y_web.src.hpc.server import _is_hpc_server_process
    if not (
        getattr(exp, "server_pid", None)
        and _is_hpc_server_process(exp.server_pid)
        and Path(exp_folder, "ray_config.temp").is_file()
        and Path(exp_folder, "ray_ready.temp").is_file()
    ):
        raise RuntimeError(
            "HPC server not ready: verify run_server.py is alive and both "
            "ray_config.temp and ray_ready.temp exist. "
            "Inspect logs/hpc_server_bootstrap.log before starting clients."
        )

    # Validate ray_config.temp exists (required for HPC client startup).
    # Local Ray bootstrap can exceed a minute on some machines, so keep the''')

# Refresh display after crashes (stale PID); an initializing-but-alive server remains running.
data = "routes/admin/sub/experiments/_data.py"
patch(data,
'''    # get experiment populations along with population names and ids
    experiment_populations = (''',
'''    # FRAIME: reconcile HPC state against the actual process on every details view.
    if experiment.simulator_type == "HPC" and experiment.running == 1:
        from y_web.src.hpc.server import _is_hpc_server_process
        pid = getattr(experiment, "server_pid", None)
        if not pid or not _is_hpc_server_process(pid):
            experiment.running = 0
            experiment.server_pid = None
            experiment.exp_status = "stopped"
            db.session.commit()
            flash("HPC server process exited. See logs/hpc_server_bootstrap.log.", "warning")
        else:
            from y_web.src.hpc.server import _resolve_hpc_experiment_folder
            root = pathlib.Path(_resolve_hpc_experiment_folder(experiment))
            if not (root / "ray_config.temp").is_file() or not (root / "ray_ready.temp").is_file():
                flash("HPC server is starting but Ray is NOT ready; do not run clients.", "warning")

    # get experiment populations along with population names and ids
    experiment_populations = (''')

crud = "routes/admin/sub/experiments/_crud.py"
patch(crud,
'''    start_server_for_experiment(exp)

    return experiment_details(uid)


@experiments.route("/admin/stop_experiment/<int:uid>")''',
'''    try:
        start_server_for_experiment(exp)
    except Exception as exc:
        exp.running = 0
        exp.server_pid = None
        exp.exp_status = "stopped"
        db.session.commit()
        current_app.logger.exception("HPC experiment server start failed")
        flash(f"Server start failed: {exc}", "error")

    return experiment_details(uid)


@experiments.route("/admin/stop_experiment/<int:uid>")''')

print("[FRAIME] HPC lifecycle patch OK")
