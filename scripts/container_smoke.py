"""Build and smoke-test the local Fan Production MVP container stack."""

from __future__ import annotations

import argparse
from http.client import RemoteDisconnected
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


DEFAULT_PROJECT = "amhi_task_prod_13_smoke"
DEFAULT_API_PORT = "18080"
DEFAULT_POSTGRES_PORT = "15432"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", default=DEFAULT_PROJECT)
    parser.add_argument("--api-port", default=DEFAULT_API_PORT)
    parser.add_argument("--postgres-port", default=DEFAULT_POSTGRES_PORT)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--keep-running", action="store_true")
    args = parser.parse_args()

    env = _compose_env(args)
    project_args = ["-p", args.project_name]
    base_url = f"http://127.0.0.1:{args.api_port}"

    try:
        _run(["docker", "compose", *project_args, "down", "-v", "--remove-orphans"], env)
        _run(["docker", "compose", *project_args, "build", "api"], env)
        _review_image_contents(project_args, env)
        _run(["docker", "compose", *project_args, "up", "-d", "postgres", "api", "worker"], env)

        health = _wait_json(f"{base_url}/api/v1/health", args.timeout_seconds)
        ready = _wait_ready(f"{base_url}/api/v1/ready", args.timeout_seconds)
        created = _post_event(base_url)
        event_id = created["event"]["event_id"]
        completed = _wait_event_completed(base_url, event_id, args.timeout_seconds)

        print("TASK_PROD_13_CONTAINER_SMOKE=OK")
        print(f"health_status={health['status']}")
        print(f"ready_status={ready['status']}")
        print(f"created_status={created['event']['status']}")
        print(f"event_id={event_id}")
        print(f"final_status={completed['event']['status']}")
        print(f"analysis_status={completed['analysis_run']['status']}")
        print("pipeline_mode=container_smoke_stub")
        return 0
    except Exception:
        _run(["docker", "compose", *project_args, "ps"], env, check=False)
        _run(["docker", "compose", *project_args, "logs", "--tail", "120"], env, check=False)
        raise
    finally:
        if not args.keep_running:
            _run(
                ["docker", "compose", *project_args, "down", "-v", "--remove-orphans"],
                env,
                check=False,
            )


def _compose_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    env["AMHI_API_PORT"] = str(args.api_port)
    env["POSTGRES_PORT"] = str(args.postgres_port)
    env["AMHI_WORKER_PIPELINE_MODE"] = "stub"
    env["AMHI_WORKER_IDLE_SLEEP_SECONDS"] = "1"
    env["AMHI_WORKER_MAX_EVENTS_PER_TICK"] = "1"
    env["AMHI_ALLOW_REGISTERED_AUDIO_REFERENCE"] = "1"
    env["AMHI_WORKER_INITIALIZED"] = "1"
    env.setdefault("GEMINI_API_KEY", "container-smoke-configured")
    env.setdefault("AMHI_EXTERNAL_ARTIFACT_ROOT", _default_artifact_root())
    return env


def _default_artifact_root() -> str:
    candidates = [
        Path(r"D:\PDM_Data\MIMII"),
        Path("/mnt/amhi-artifacts"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate).replace("\\", "/")
    return "D:/PDM_Data/MIMII"


def _review_image_contents(project_args: list[str], env: dict[str, str]) -> None:
    code = r"""
from pathlib import Path
forbidden_suffixes = {'.wav', '.npy', '.npz', '.pt', '.pth', '.zip', '.tar', '.tgz', '.gz', '.7z', '.rar'}
offenders = []
for path in Path('/app').rglob('*'):
    if not path.is_file():
        continue
    lower = str(path).lower()
    if path.suffix.lower() in forbidden_suffixes or lower.endswith('.tar.gz'):
        offenders.append(str(path))
    if '/.git/' in lower or '/__pycache__/' in lower:
        offenders.append(str(path))
if offenders:
    print('\n'.join(offenders))
    raise SystemExit(1)
print('IMAGE_CONTENT_REVIEW=OK')
"""
    _run(
        [
            "docker",
            "compose",
            *project_args,
            "run",
            "--rm",
            "--no-deps",
            "--entrypoint",
            "python",
            "api",
            "-c",
            code,
        ],
        env,
    )


def _post_event(base_url: str) -> dict:
    boundary = f"----amhi-smoke-{uuid4().hex}"
    body = _multipart_body(
        boundary,
        fields={
            "machine_type": "fan",
            "machine_id": "id_00",
            "snr_tag": "minus6dB",
        },
        file_field="audio_file",
        filename="container-smoke.wav",
        file_bytes=b"container-smoke-lifecycle-only-wav-placeholder",
    )
    request = Request(
        f"{base_url}/api/v1/events",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    return _request_json(request)


def _multipart_body(
    boundary: str,
    *,
    fields: dict[str, str],
    file_field: str,
    filename: str,
    file_bytes: bytes,
) -> bytes:
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        chunks.append(value.encode())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{filename}"\r\n'
        ).encode(),
    )
    chunks.append(b"Content-Type: audio/wav\r\n\r\n")
    chunks.append(file_bytes)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks)


def _wait_ready(url: str, timeout_seconds: float) -> dict:
    deadline = monotonic() + timeout_seconds
    last_body: dict | None = None
    while monotonic() < deadline:
        try:
            body = _request_json(Request(url))
            last_body = body
            if body.get("ready") is True:
                return body
        except (HTTPError, OSError, RemoteDisconnected, TimeoutError, URLError):
            pass
        sleep(1.0)
    raise RuntimeError(f"readiness did not become ready: {last_body}")


def _wait_event_completed(base_url: str, event_id: str, timeout_seconds: float) -> dict:
    deadline = monotonic() + timeout_seconds
    last_body: dict | None = None
    while monotonic() < deadline:
        body = _request_json(Request(f"{base_url}/api/v1/events/{event_id}"))
        last_body = body
        if body["event"]["status"] == "completed":
            return body
        if body["event"]["status"] == "failed":
            raise RuntimeError(f"event failed during smoke: {body}")
        sleep(1.0)
    raise RuntimeError(f"event did not complete: {last_body}")


def _wait_json(url: str, timeout_seconds: float) -> dict:
    deadline = monotonic() + timeout_seconds
    while monotonic() < deadline:
        try:
            return _request_json(Request(url))
        except (HTTPError, OSError, RemoteDisconnected, TimeoutError, URLError):
            sleep(1.0)
    raise RuntimeError(f"endpoint did not respond: {url}")


def _request_json(request: Request) -> dict:
    with urlopen(request, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("expected JSON object response")
    return payload


def _run(command: list[str], env: dict[str, str], *, check: bool = True) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=Path(__file__).resolve().parents[1], env=env, check=check)


if __name__ == "__main__":
    raise SystemExit(main())
