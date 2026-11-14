from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import toml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_EXAMPLE = ROOT / "config.example.toml"
CONFIG_FILE = ROOT / "config.toml"
TASK_FILE = ROOT / ".cartoonforge-task.json"

# OVHcloud lists this SDXL model as Free and documents anonymous API access.
# Anonymous requests are rate-limited to two requests per minute per IP/model.
OVH_IMAGE_BASE_URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
OVH_IMAGE_MODEL = "stable-diffusion-xl-base-v10"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()


def generate_story_with_gemini(
    idea: str, style: str, scene_count: int, script_hint: str = "", character_hint: str = ""
) -> tuple[str, str]:
    """Turn a short idea into a production-ready script and character bible."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "Gemini auto-creation is enabled, but GEMINI_API_KEY is missing. "
            "Add it as a GitHub Actions repository secret, or disable auto-creation "
            "and provide both a script and character description."
        )

    prompt = f"""
You are the story editor and character designer for CartoonForge, a short-form cartoon studio.
Create a coherent, family-friendly cartoon story from the user's idea.

Return ONLY valid JSON with exactly these keys:
{{
  "title": "short engaging title",
  "script": "complete narration/script with clear beginning, middle and ending",
  "character": "a detailed visual character bible for the recurring lead character"
}}

Requirements:
- Write the script in natural, vivid English, unless the idea clearly requests another language.
- Make it suitable for a short cartoon video of {scene_count} scenes.
- Write {max(scene_count * 2, 6)} to {max(scene_count * 3, 9)} concise, visual sentences so scenes can be separated cleanly.
- Give the story a clear hook, escalating action, emotional moment and satisfying ending.
- Keep the plot simple enough to understand visually; avoid dialogue-heavy scenes.
- Character bible must specify species/type, age impression, body shape, face, eyes, colours, clothing, accessories and distinctive markings.
- Make the character description precise enough to repeat consistently in every image prompt.
- Do not use copyrighted franchise characters, existing film characters or branded designs.
- Do not include camera directions, markdown or text outside the JSON.
- If the user provides a script or character hint, preserve and improve it rather than replacing its core idea.

Art style: {style}
Number of visual scenes: {scene_count}
Story idea: {idea}
Optional script direction: {script_hint or "None"}
Optional character direction: {character_hint or "Invent a distinctive original character"}
""".strip()

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 5000,
            "responseMimeType": "application/json",
        },
    }

    # A temporary 503 should not kill the whole video job. Retry transient
    # failures, then try the lower-cost stable Flash-Lite model as a fallback.
    fallback_model = os.environ.get(
        "GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"
    ).strip()
    models = [GEMINI_MODEL]
    if fallback_model and fallback_model != GEMINI_MODEL:
        models.append(fallback_model)

    result = None
    last_error = None
    transient_statuses = {429, 500, 502, 503, 504}
    for model in models:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        for attempt, delay in enumerate((0, 8, 20, 40), start=1):
            if delay:
                print(
                    f"Gemini {model} is temporarily unavailable; "
                    f"retrying in {delay}s (attempt {attempt}/4)...",
                    flush=True,
                )
                time.sleep(delay)
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    result = json.loads(response.read().decode("utf-8"))
                print(f"Story generation succeeded using {model}.")
                break
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")[:1200]
                last_error = (error.code, detail)
                if error.code not in transient_statuses:
                    raise SystemExit(
                        f"Gemini API returned HTTP {error.code} using {model}. "
                        f"Check the API key and model access. Details: {detail}"
                    ) from error
                print(
                    f"Gemini {model} returned HTTP {error.code} "
                    f"(temporary service/rate limit issue).",
                    flush=True,
                )
            except (urllib.error.URLError, TimeoutError) as error:
                last_error = ("network", str(error))
                print(f"Gemini network error using {model}: {error}", flush=True)
        if result is not None:
            break

    if result is None:
        code, detail = last_error or ("unknown", "No response received")
        raise SystemExit(
            "Gemini story generation failed after automatic retries and fallback. "
            f"Last error: HTTP {code}. Details: {detail}"
        )

    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        generated = json.loads(text)
        script = str(generated.get("script", "")).strip()
        character = str(generated.get("character", "")).strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise SystemExit(
            "Gemini returned an unexpected response. Please retry the workflow."
        ) from error

    if not script or not character:
        raise SystemExit("Gemini did not return both a script and character description.")
    print(f"Gemini created the story: {generated.get('title', 'Untitled cartoon')}")
    print(f"Generated script length: {len(script)} characters")
    print(f"Generated character description length: {len(character)} characters")
    return script, character


def scene_chunks(script: str, count: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    units: list[str] = []
    for paragraph in paragraphs:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?。！？])\s+", paragraph)
            if sentence.strip()
        ]
        units.extend(sentences or [paragraph])
    if not units:
        raise SystemExit("The script is empty.")
    if len(units) == 1 and len(units[0].split()) > 45:
        words = units[0].split()
        step = max(1, (len(words) + count - 1) // count)
        units = [" ".join(words[i : i + step]) for i in range(0, len(words), step)]
    actual_count = min(count, len(units))
    return [
        " ".join(
            units[
                round(i * len(units) / actual_count) :
                round((i + 1) * len(units) / actual_count)
            ]
        )
        for i in range(actual_count)
    ]


def configure_image_provider() -> None:
    config = toml.load(CONFIG_EXAMPLE)
    app = config.setdefault("app", {})
    app["video_source"] = "openai_image"
    app["openai_image_base_url"] = (
        os.environ.get("OPENAI_IMAGE_BASE_URL", OVH_IMAGE_BASE_URL).strip().rstrip("/")
    )
    app["openai_image_model"] = (
        os.environ.get("OPENAI_IMAGE_MODEL", OVH_IMAGE_MODEL).strip()
    )
    # OVHcloud SDXL currently accepts 1024x1024 only. Explicitly override
    # MoneyPrinterTurbo's portrait/landscape size inference.
    app["openai_image_size"] = "1024x1024"
    api_key = (
        os.environ.get("OVH_AI_ENDPOINTS_ACCESS_TOKEN", "").strip()
        or os.environ.get("OPENAI_IMAGE_API_KEY", "").strip()
    )
    app["openai_image_api_keys"] = [api_key] if api_key else []
    app["openai_image_prompt_template"] = "{term}"
    with CONFIG_FILE.open("w", encoding="utf-8") as handle:
        toml.dump(config, handle)


def main() -> int:
    idea = os.environ.get("CARTOON_IDEA", "").strip()
    script = os.environ.get("CARTOON_SCRIPT", "").strip()
    character = os.environ.get("CARTOON_CHARACTER", "").strip()
    style = os.environ.get("CARTOON_STYLE", "3D family animation").strip()
    count = int(os.environ.get("CARTOON_SCENES", "3"))
    voice = os.environ.get("CARTOON_VOICE", "en-US-AriaNeural-Female").strip()
    auto_create = os.environ.get("CARTOON_AUTO_CREATE", "true").lower() in {
        "1", "true", "yes", "on"
    }

    if not 1 <= count <= 8:
        raise SystemExit("Scene count must be between 1 and 8.")

    if auto_create:
        if not idea:
            raise SystemExit("Enter a short story idea to use Gemini auto-creation.")
        script, character = generate_story_with_gemini(
            idea=idea,
            style=style,
            scene_count=count,
            script_hint=script,
            character_hint=character,
        )
    elif not script or not character:
        raise SystemExit(
            "Manual mode requires both a script and a recurring character description."
        )

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
        "video_subject": idea or "CartoonForge original animated short",
        "video_script": script,
        "video_terms": prompts,
        "video_source": "openai_image",
        "voice_name": voice or "no-voice",
        "subtitle_enabled": True,
        "video_language": "en-US",
    }
    TASK_FILE.write_text(
        json.dumps([task], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Rendering {len(scenes)} cartoon scene(s) with OVHcloud SDXL "
        "(free model; anonymous rate limit: 2 requests/minute/IP/model)."
    )
    return subprocess.run(
        [
            "uv", "run", "python", "cli.py", "--batch-file",
            str(TASK_FILE), "--stop-at", "video",
        ],
        cwd=ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
