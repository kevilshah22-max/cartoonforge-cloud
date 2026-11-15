"""Optional Magic Hour image-to-video enhancement for CartoonForge cloud renders.

This adapter is deliberately optional: the existing free MoneyPrinterTurbo render
remains the fallback when no API key is configured or the trial quota is exhausted.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://api.magichour.ai/v1"
MODEL = "ltx-2.5"
RESOLUTION = "480p"
MAX_TRIAL_CREDITS = 360  # Keep 40 of the advertised 400 signup credits in reserve.
CREDITS_PER_SECOND = 24
POLL_INTERVAL_SECONDS = 12
POLL_TIMEOUT_SECONDS = 20 * 60


class MagicHourError(RuntimeError):
    """A safe, user-readable provider error."""


def _request_json(method: str, url: str, api_key: str, payload=None, timeout=60):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1000]
        if error.code == 402:
            raise MagicHourError(
                "Magic Hour has insufficient trial credits. The original free render was kept."
            ) from error
        if error.code == 401:
            raise MagicHourError(
                "Magic Hour rejected the API key. Check the MAGIC_HOUR_API_KEY secret."
            ) from error
        raise MagicHourError(f"Magic Hour HTTP {error.code}: {detail}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise MagicHourError(f"Magic Hour network error: {error}") from error


def _available_credits(api_key: str) -> int:
    account = _request_json("GET", f"{API_BASE}/account", api_key)
    try:
        credits = int(account["credits"])
    except (KeyError, TypeError, ValueError) as error:
        raise MagicHourError("Magic Hour account response did not include a valid credit balance.") from error
    print(f"Magic Hour account balance: {credits} credits.", flush=True)
    return max(0, credits)


def _upload_image(image_path: Path, api_key: str) -> str:
    extension = image_path.suffix.lower().lstrip(".")
    if extension not in {"png", "jpg", "jpeg", "webp"}:
        raise MagicHourError(f"Unsupported image format: {extension}")
    result = _request_json(
        "POST",
        f"{API_BASE}/files/upload-urls",
        api_key,
        {"items": [{"type": "image", "extension": extension}]},
    )
    items = result.get("items") or []
    if not items or not items[0].get("upload_url") or not items[0].get("file_path"):
        raise MagicHourError("Magic Hour did not return an image upload URL.")
    upload_url = items[0]["upload_url"]
    if not upload_url.startswith("https://"):
        raise MagicHourError("Magic Hour returned an unsafe upload URL.")
    mime = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }[extension]
    request = urllib.request.Request(
        upload_url,
        data=image_path.read_bytes(),
        headers={"Content-Type": mime},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status not in (200, 201, 204):
                raise MagicHourError(f"Image upload returned HTTP {response.status}.")
    except urllib.error.HTTPError as error:
        raise MagicHourError(f"Image upload failed with HTTP {error.code}.") from error
    return items[0]["file_path"]


def _animate_one(image_path: Path, output_path: Path, api_key: str, seconds: int, index: int):
    asset_path = _upload_image(image_path, api_key)
    created = _request_json(
        "POST",
        f"{API_BASE}/image-to-video",
        api_key,
        {
            "name": f"CartoonForge scene {index}",
            "end_seconds": seconds,
            "model": MODEL,
            "resolution": RESOLUTION,
            "audio": False,
            "style": {
                "prompt": (
                    "Animate the existing cartoon characters as the same characters, "
                    "not as a slideshow. Show clear continuous body movement, expressive "
                    "facial motion, natural gestures and environmental movement. "
                    "Preserve the original character identity, clothing, proportions, "
                    "art style and scene composition. Use a lively, fluid animated-film "
                    "performance with coherent motion; avoid morphing, extra limbs, "
                    "scene cuts, text and logos."
                )
            },
            "assets": {"image_file_path": asset_path},
        },
    )
    project_id = created.get("id")
    if not project_id:
        raise MagicHourError("Magic Hour did not return a video project ID.")

    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        status = _request_json(
            "GET", f"{API_BASE}/video-projects/{urllib.parse.quote(project_id)}", api_key
        )
        state = str(status.get("status", "")).lower()
        print(f"Magic Hour scene {index}: {state or 'unknown'}", flush=True)
        if state == "complete":
            downloads = status.get("downloads") or []
            download_url = downloads[0].get("url") if downloads else None
            if not download_url or not download_url.startswith("https://"):
                raise MagicHourError("Completed Magic Hour job has no safe download URL.")
            request = urllib.request.Request(download_url, headers={"User-Agent": "CartoonForge/2.0"})
            with urllib.request.urlopen(request, timeout=180) as response:
                output_path.write_bytes(response.read())
            if not output_path.is_file() or output_path.stat().st_size < 10_000:
                raise MagicHourError("Magic Hour returned an empty or incomplete MP4.")
            return
        if state in {"error", "canceled"}:
            error = status.get("error") or {}
            message = error.get("message", "provider job did not complete")
            raise MagicHourError(f"Magic Hour scene {index} failed: {message}")
        time.sleep(POLL_INTERVAL_SECONDS)
    raise MagicHourError(f"Magic Hour scene {index} timed out after 20 minutes.")


def _probe_video(path: Path) -> tuple[int, int, float, bool]:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True, check=True, timeout=30,
    )
    data = json.loads(result.stdout)
    stream = (data.get("streams") or [{}])[0]
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout.strip()
    return int(stream.get("width", 0)), int(stream.get("height", 0)), duration, bool(audio)


def _replace_video_track(
    original: Path, clips: list[Path], work_dir: Path, subtitle_path: Path | None = None
) -> None:
    width, height, duration, has_audio = _probe_video(original)
    if width < 2 or height < 2 or duration <= 0:
        raise MagicHourError("Could not inspect the original CartoonForge MP4.")
    count = len(clips)
    inputs = []
    filters = []
    for index, clip in enumerate(clips):
        inputs.extend(["-stream_loop", "-1", "-i", str(clip)])
        segment_duration = duration / count
        filters.append(
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30,setsar=1,"
            f"trim=duration={segment_duration:.4f},setpts=PTS-STARTPTS[v{index}]"
        )
    filters.append("".join(f"[v{i}]" for i in range(count)) +
                   f"concat=n={count}:v=1:a=0[outv]")
    video_label = "outv"
    if subtitle_path and subtitle_path.is_file():
        subtitle_name = str(subtitle_path).replace(":", "\\:").replace("'", "\\'")
        filters.append(f"[outv]subtitles='{subtitle_name}'[captioned]")
        video_label = "captioned"
        print(f"Reapplying generated subtitles: {subtitle_path}", flush=True)
    audio_index = count
    command = ["ffmpeg", "-y", *inputs, "-i", str(original),
               "-filter_complex", ";".join(filters), "-map", f"[{video_label}]"]
    if has_audio:
        command.extend(["-map", f"{audio_index}:a:0"])
    command.extend([
        "-t", f"{duration:.3f}", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "20", "-pix_fmt", "yuv420p",
    ])
    if has_audio:
        command.extend(["-c:a", "copy"])
    command.extend(["-movflags", "+faststart", str(work_dir / "animated-final.mp4")])
    subprocess.run(command, check=True, timeout=1800, capture_output=True, text=True)
    rendered = work_dir / "animated-final.mp4"
    if not rendered.is_file() or rendered.stat().st_size < 50_000:
        raise MagicHourError("Animated MP4 validation failed.")
    backup = original.with_name(original.stem + "-before-animation.mp4")
    original.replace(backup)
    rendered.replace(original)
    backup.unlink(missing_ok=True)


def enhance_latest_render(root: Path, started_at: float, scene_limit: int = 3) -> bool:
    """Animate the newest scene images and replace the final MP4 video track.

    Returns False without changing the original render when the provider is not
    configured or any optional enhancement step fails.
    """
    api_key = os.environ.get("MAGIC_HOUR_API_KEY", "").strip()
    if not api_key:
        print("Magic Hour is not configured; keeping the free baseline render.")
        return False

    tasks_dir = root / "storage" / "tasks"
    if not tasks_dir.is_dir():
        print("No task storage found; keeping the free baseline render.")
        return False
    images = []
    for path in tasks_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        if any(token in path.stem.lower() for token in ("cover", "thumbnail", "logo", "avatar")):
            continue
        try:
            if path.stat().st_mtime >= started_at and path.stat().st_size > 20_000:
                images.append(path)
        except OSError:
            continue
    images.sort(key=lambda item: (item.stat().st_mtime, str(item)))
    images = images[-max(1, min(scene_limit, 3)):]
    renders = []
    for path in tasks_dir.rglob("final-*.mp4"):
        if path.is_file() and path.stat().st_mtime >= started_at:
            renders.append(path)
    if not images or not renders:
        print("Magic Hour skipped: no fresh scene images or final MP4 were found.")
        return False

    final_video = max(renders, key=lambda item: item.stat().st_mtime)
    try:
        available_credits = _available_credits(api_key)
    except Exception as error:
        print(
            f"Magic Hour account preflight failed ({type(error).__name__}: {error}). "
            "Keeping the original free render.",
            flush=True,
        )
        return False

    # LTX 2.5 at 480p costs 24 credits per output second. Never spend more
    # than 360 credits in one run, and never queue work beyond the live balance.
    safe_budget = min(MAX_TRIAL_CREDITS, available_credits)
    seconds_per_scene = min(
        5, safe_budget // CREDITS_PER_SECOND // len(images)
    )
    if seconds_per_scene < 1:
        print(
            f"Magic Hour skipped: {available_credits} credits available; "
            f"at least {len(images) * CREDITS_PER_SECOND} are required.",
            flush=True,
        )
        return False

    work_dir = final_video.parent / "magichour-animation"
    work_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    estimated_total = len(images) * seconds_per_scene * CREDITS_PER_SECOND
    print(
        f"Magic Hour enhancement: {len(images)} scene(s), {seconds_per_scene}s each, "
        f"estimated {estimated_total} credits (live balance {available_credits}; "
        f"per-run cap {MAX_TRIAL_CREDITS}).",
        flush=True,
    )
    try:
        for index, image_path in enumerate(images, start=1):
            clip_path = work_dir / f"scene-{index:02d}.mp4"
            _animate_one(image_path, clip_path, api_key, seconds_per_scene, index)
            clips.append(clip_path)
        subtitle_files = [
            path for path in final_video.parent.rglob("*.srt")
            if path.is_file() and path.stat().st_mtime >= started_at
        ]
        subtitle_path = max(subtitle_files, key=lambda item: item.stat().st_mtime) if subtitle_files else None
        _replace_video_track(final_video, clips, work_dir, subtitle_path=subtitle_path)
        print(f"Magic Hour animation enhancement completed: {final_video}", flush=True)
        return True
    except Exception as error:
        print(
            f"Magic Hour enhancement unavailable ({type(error).__name__}: {error}). "
            "Keeping the original free render.",
            flush=True,
        )
        return False
