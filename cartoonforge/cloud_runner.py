from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import toml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_EXAMPLE = ROOT / "config.example.toml"
CONFIG_FILE = ROOT / "config.toml"
TASK_FILE = ROOT / ".cartoonforge-task.json"


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing GitHub Actions secret: {name}")
    return value


def scene_chunks(script: str, count: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?。！？])\s+", paragraph) if s.strip()]
        units.extend(sentences or [paragraph])
    if not units:
        raise SystemExit("The script is empty.")
    if len(units) == 1 and len(units[0].split()) > 45:
        words = units[0].split()
        step = max(1, (len(words) + count - 1) // count)
        units = [" ".join(words[i:i + step]) for i in range(0, len(words), step)]
    actual_count = min(count, len(units))
    return [
        " ".join(units[round(i * len(units) / actual_count):round((i + 1) * len(units) / actual_count)])
        for i in range(actual_count)
    ]


def configure_image_provider() -> None:
    config = toml.load(CONFIG_EXAMPLE)
    app = config.setdefault("app", {})
    app["video_source"] = "openai_image"
    app["openai_image_base_url"] = required_env("OPENAI_IMAGE_BASE_URL").rstrip("/")
    app["openai_image_model"] = required_env("OPENAI_IMAGE_MODEL")
    api_key = os.environ.get("OPENAI_IMAGE_API_KEY", "").strip()
    app["openai_image_api_keys"] = [api_key] if api_key else []
    app["openai_image_prompt_template"] = "{term}"
    with CONFIG_FILE.open("w", encoding="utf-8") as handle:
        toml.dump(config, handle)


def main() -> int:
    script = os.environ.get("CARTOON_SCRIPT", "").strip()
    character = os.environ.get("CARTOON_CHARACTER", "").strip()
    style = os.environ.get("CARTOON_STYLE", "3D family animation").strip()
    count = int(os.environ.get("CARTOON_SCENES", "4"))
    voice = os.environ.get("CARTOON_VOICE", "en-US-AriaNeural-Female").strip()
    if not script or not character:
        raise SystemExit("Both the script and recurring character description are required.")
    if not 1 <= count <= 8:
        raise SystemExit("Scene count must be between 1 and 8.")

    configure_image_provider()
    scenes = scene_chunks(script, count)
    prompts = [
        (
            f"Create a polished {style} animated cartoon frame. Recurring main character — "
            f"keep this exact design in every scene: {character}. Scene {i + 1}: {scene}. "
            "Maintain identical face, proportions, colours, clothing and markings. "
            "Expressive cinematic composition, readable action, coherent environment, "
            "high-quality animation-film art direction, no text, no captions, no watermark."
        )
        for i, scene in enumerate(scenes)
    ]
    task = {
        "video_subject": "CartoonForge original animated short",
        "video_script": script,
        "video_terms": prompts,
        "video_source": "openai_image",
        "voice_name": voice or "no-voice",
        "subtitle_enabled": True,
        "video_language": "en-US",
    }
    TASK_FILE.write_text(json.dumps([task], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Rendering {len(scenes)} cartoon scene(s). Image provider charges/quotas may apply.")
    return subprocess.run(
        ["uv", "run", "python", "cli.py", "--batch-file", str(TASK_FILE), "--stop-at", "video"],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
