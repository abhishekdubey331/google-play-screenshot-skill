#!/usr/bin/env python3
"""Enhance a screenshot scaffold with Atlas Cloud image editing."""

from __future__ import annotations

import argparse
import io
import json
import mimetypes
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError


DEFAULT_BASE_URL = "https://api.atlascloud.ai"
DEFAULT_MODEL = "google/nano-banana-pro/edit"
USER_AGENT = "atlas-cloud-aso-screenshot-skill/1.0"
GET_BACKOFF_SECONDS = (1, 2, 4)
SUCCESS_STATUSES = {"completed", "succeeded", "success"}
FAILURE_STATUSES = {"failed", "error", "canceled", "cancelled"}


class AtlasError(RuntimeError):
    """Raised when Atlas Cloud returns an invalid or failed response."""


def _response_data(response: dict[str, Any], context: str) -> Any:
    code = str(response.get("code", ""))
    if code not in {"0", "200"}:
        message = response.get("message") or response.get("msg") or "unknown error"
        raise AtlasError(f"{context} failed: {message} (code={code or 'missing'})")
    if "data" not in response:
        raise AtlasError(f"{context} response did not include data")
    return response["data"]


def _output_url(data: Any) -> str | None:
    if isinstance(data, str) and data.startswith("https://"):
        return data
    if isinstance(data, list):
        for item in data:
            result = _output_url(item)
            if result:
                return result
        return None
    if not isinstance(data, dict):
        return None

    for key in ("outputs", "output", "result", "images"):
        if key in data:
            result = _output_url(data[key])
            if result:
                return result
    for key in ("url", "download_url", "image_url"):
        value = data.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            return value
    return None


class AtlasClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        request_timeout: float = 90,
        opener: Callable[..., Any] = urlopen,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout
        self._opener = opener
        self._sleep = sleep_fn

    def _request_bytes(self, request: Request, retry_get: bool) -> bytes:
        delays = (0, *GET_BACKOFF_SECONDS) if retry_get else (0,)
        last_error: Exception | None = None

        for attempt, delay in enumerate(delays):
            if delay:
                self._sleep(delay)
            try:
                with self._opener(request, timeout=self.request_timeout) as response:
                    return response.read()
            except HTTPError as exc:
                last_error = exc
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retry_get or not retryable or attempt == len(delays) - 1:
                    detail = exc.read().decode("utf-8", errors="replace")[:500]
                    raise AtlasError(
                        f"HTTP {exc.code} for {request.full_url}: {detail}"
                    ) from exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if not retry_get or attempt == len(delays) - 1:
                    raise AtlasError(f"request failed for {request.full_url}: {exc}") from exc

        raise AtlasError(f"request failed for {request.full_url}: {last_error}")

    def _json_request(
        self,
        method: str,
        url: str,
        *,
        payload: dict[str, Any] | None = None,
        authenticated: bool = True,
        retry_get: bool = False,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if authenticated:
            headers["Authorization"] = f"Bearer {self.api_key}"
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        request = Request(url, data=body, headers=headers, method=method)
        raw = self._request_bytes(request, retry_get=retry_get)
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AtlasError(f"invalid JSON from {url}") from exc
        if not isinstance(value, dict):
            raise AtlasError(f"expected an object response from {url}")
        return value

    def discover_model(self, model: str) -> dict[str, Any]:
        catalog_response = self._json_request(
            "GET", f"{self.base_url}/api/v1/models", authenticated=False
        )
        catalog = _response_data(catalog_response, "model catalog")
        if not isinstance(catalog, list):
            raise AtlasError("model catalog data is not a list")

        entry = next(
            (item for item in catalog if isinstance(item, dict) and item.get("model") == model),
            None,
        )
        if entry is None:
            raise AtlasError(f"model is not present in the live catalog: {model}")
        if entry.get("display_console") is not True:
            raise AtlasError(f"model is not currently enabled: {model}")
        schema_url = entry.get("schema")
        if not isinstance(schema_url, str) or not schema_url.startswith("https://"):
            raise AtlasError(f"model does not provide a valid schema URL: {model}")

        schema = self._json_request("GET", schema_url, authenticated=False)
        try:
            input_schema = schema["components"]["schemas"]["Input"]
            properties = input_schema["properties"]
            required = set(input_schema.get("required", []))
            paths = schema["paths"]
        except (KeyError, TypeError) as exc:
            raise AtlasError(f"model schema has an unexpected shape: {schema_url}") from exc

        expected_required = {"model", "prompt", "images"}
        if not expected_required.issubset(required):
            raise AtlasError(
                f"model schema no longer requires {sorted(expected_required)}"
            )
        if "/api/v1/model/generateImage" not in paths:
            raise AtlasError("model schema does not expose generateImage")
        if "/api/v1/model/prediction/{request_id}" not in paths:
            raise AtlasError("model schema does not expose prediction polling")
        if not isinstance(properties, dict):
            raise AtlasError("model input properties are not an object")
        return properties

    def upload_media(self, path: Path) -> str:
        boundary = f"atlas-{uuid.uuid4().hex}"
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        filename = path.name.replace('"', "")
        body = b"".join(
            (
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; name="file"; '
                    f'filename="{filename}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            )
        )
        request = Request(
            f"{self.base_url}/api/v1/model/uploadMedia",
            data=body,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        raw = self._request_bytes(request, retry_get=False)
        try:
            response = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AtlasError("upload returned invalid JSON") from exc
        data = _response_data(response, "media upload")
        url = _output_url(data)
        if not url:
            raise AtlasError("media upload did not return a download URL")
        return url

    def submit_image(self, payload: dict[str, Any]) -> str:
        # Deliberately one POST with no retry: generation may be billable.
        response = self._json_request(
            "POST", f"{self.base_url}/api/v1/model/generateImage", payload=payload
        )
        data = _response_data(response, "image generation")
        if not isinstance(data, dict):
            raise AtlasError("image generation data is not an object")
        prediction_id = data.get("id") or data.get("prediction_id")
        if not isinstance(prediction_id, str) or not prediction_id:
            raise AtlasError("image generation did not return a prediction ID")
        return prediction_id

    def wait_for_output(
        self, prediction_id: str, timeout_seconds: float, poll_interval: float
    ) -> str:
        deadline = time.monotonic() + timeout_seconds
        encoded_id = quote(prediction_id, safe="")
        prediction_url = f"{self.base_url}/api/v1/model/prediction/{encoded_id}"
        while True:
            response = self._json_request("GET", prediction_url, retry_get=True)
            data = _response_data(response, "prediction")
            if not isinstance(data, dict):
                raise AtlasError("prediction data is not an object")
            status = str(data.get("status", "")).lower()
            output = _output_url(data)
            if status in SUCCESS_STATUSES:
                if not output:
                    raise AtlasError("completed prediction did not include an output URL")
                return output
            if status in FAILURE_STATUSES:
                detail = data.get("error") or data.get("message") or "unknown error"
                raise AtlasError(f"prediction {status}: {detail}")
            if time.monotonic() >= deadline:
                raise AtlasError(
                    f"prediction timed out after {timeout_seconds:g} seconds; "
                    f"id={prediction_id}"
                )
            self._sleep(poll_interval)

    def download(self, url: str, output: Path, output_format: str) -> None:
        request = Request(
            url,
            headers={"Accept": "image/*", "User-Agent": USER_AGENT},
            method="GET",
        )
        content = self._request_bytes(request, retry_get=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            image = Image.open(io.BytesIO(content))
            image.load()
        except (UnidentifiedImageError, OSError) as exc:
            raise AtlasError("downloaded output is not a valid image") from exc

        requested = output_format.lower()
        if requested == "png":
            save_format = "PNG"
        elif requested in {"jpeg", "jpg"}:
            save_format = "JPEG"
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
        else:
            suffix = output.suffix.lower()
            save_format = "PNG" if suffix == ".png" else "JPEG"
            if save_format == "JPEG" and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")

        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            image.save(handle, format=save_format)
        os.replace(temporary, output)


def _enum_values(properties: dict[str, Any], name: str) -> list[Any]:
    value = properties.get(name, {})
    enum = value.get("enum", []) if isinstance(value, dict) else []
    return enum if isinstance(enum, list) else []


def build_payload(
    properties: dict[str, Any],
    *,
    model: str,
    prompt: str,
    images: list[str],
    aspect_ratio: str,
    resolution: str,
    output_format: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "prompt": prompt, "images": images}
    options = {
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "output_format": output_format,
    }
    for name, value in options.items():
        if name not in properties:
            continue
        allowed = _enum_values(properties, name)
        if allowed and value not in allowed:
            raise AtlasError(f"{name} must be one of: {', '.join(map(str, allowed))}")
        payload[name] = value
    return payload


def enhance_image(
    client: AtlasClient,
    *,
    input_paths: list[Path],
    output: Path,
    prompt: str,
    model: str,
    aspect_ratio: str,
    resolution: str,
    output_format: str,
    timeout_seconds: float,
    poll_interval: float,
) -> dict[str, Any]:
    properties = client.discover_model(model)
    uploaded_images = [client.upload_media(path) for path in input_paths]
    payload = build_payload(
        properties,
        model=model,
        prompt=prompt,
        images=uploaded_images,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        output_format=output_format,
    )
    prediction_id = client.submit_image(payload)
    result_url = client.wait_for_output(prediction_id, timeout_seconds, poll_interval)
    client.download(result_url, output, output_format)
    return {
        "status": "completed",
        "model": model,
        "prediction_id": prediction_id,
        "output": str(output),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enhance a store screenshot scaffold with Atlas Cloud"
    )
    parser.add_argument("--input", required=True, type=Path, help="Scaffold image")
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        type=Path,
        help="Additional style reference image; repeat up to nine times",
    )
    parser.add_argument("--prompt", required=True, help="Image editing instructions")
    parser.add_argument("--output", required=True, type=Path, help="Output image path")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--aspect-ratio", default="9:16")
    parser.add_argument("--resolution", default="2k")
    parser.add_argument("--output-format", default="png")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--poll-interval", type=float, default=3)
    parser.add_argument("--request-timeout", type=float, default=90)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the live model/schema without uploads or generation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_paths = [args.input, *args.reference]
    if len(input_paths) > 10:
        raise AtlasError("the selected model accepts at most 10 input images")
    for path in input_paths:
        if not path.is_file():
            raise AtlasError(f"input image does not exist: {path}")
    if args.timeout <= 0 or args.poll_interval <= 0 or args.request_timeout <= 0:
        raise AtlasError("timeouts and poll interval must be positive")

    api_key = os.environ.get("ATLASCLOUD_API_KEY", "")
    if not args.dry_run and not api_key:
        raise AtlasError("ATLASCLOUD_API_KEY is required unless --dry-run is used")

    client = AtlasClient(
        api_key=api_key,
        request_timeout=args.request_timeout,
    )
    if args.dry_run:
        properties = client.discover_model(args.model)
        payload = build_payload(
            properties,
            model=args.model,
            prompt=args.prompt,
            images=["<uploaded-input-url>" for _ in input_paths],
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            output_format=args.output_format,
        )
        print(json.dumps({"status": "dry-run", "payload": payload}, indent=2))
        return 0

    result = enhance_image(
        client,
        input_paths=input_paths,
        output=args.output,
        prompt=args.prompt,
        model=args.model,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        output_format=args.output_format,
        timeout_seconds=args.timeout,
        poll_interval=args.poll_interval,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AtlasError as exc:
        print(json.dumps({"error": str(exc)}), file=os.sys.stderr)
        raise SystemExit(1) from exc
