#!/usr/bin/env python3
"""CartoonForge adapter for Nafay 3D's faceless-short renderer."""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request, urllib.error, zipfile
from pathlib import Path

KIT_URL = "https://nafay3d.com/skills/faceless-shorts/faceless-shorts-skill.zip?v=7"

def run(args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(args, check=True)

def fetch(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "CartoonForge-Nafay/1.0"})
    with urllib.request.urlopen(req, timeout=240) as response, open(path, "wb") as out:
        shutil.copyfileobj(response, out)

def find_kit(root):
    for p in [root, *root.rglob("*")]:
        if (p / "references/style-catalog.md").is_file() and (p / "scripts/render.py").is_file():
            return p
    raise RuntimeError("Nafay runtime kit is missing its style catalogue or renderer.")

def entry_for(catalog, slug):
    pos = catalog.find(slug)
    if pos < 0:
        raise RuntimeError("Unknown style slug: " + slug)
    start = catalog.rfind("\n### ", 0, pos)
    start = 0 if start < 0 else start + 1
    match = re.search(r"^#{2,3}\s+", catalog[pos:], re.M)
    end = pos + match.start() if match else len(catalog)
    return catalog[start:end].strip()

def caption(text):
    words = text.split()
    if not words:
        return ""
    key = max(range(len(words)), key=lambda i: len(words[i]))
    groups = []
    for start in range(0, len(words), 3):
        chunk = words[start:start+3]
        if start <= key < start + 3:
            chunk[key-start] = "*" + chunk[key-start]
        groups.append(" ".join(chunk))
    return " | ".join(groups)

def main():
    topic = os.environ["NAFAY_TOPIC"].strip()
    script = os.environ["NAFAY_SCRIPT"].strip()
    slug = os.environ.get("NAFAY_STYLE", "bio-glow").strip()
    voice = os.environ.get("NAFAY_VOICE", "bf_emma").strip()
    music = os.environ.get("NAFAY_MUSIC", "tension").strip()
    sources = [s.strip() for s in re.split(r"[;\\n]+", os.environ.get("NAFAY_SOURCES", "")) if s.strip()]
    words = re.findall(r"\b[\w’'-]+\b", script)
    if not topic or not script or not 70 <= len(words) <= 125:
        raise RuntimeError("Enter a topic and a 70–125 word fact-checked script.")
    if len(sources) < 2 or any(not s.startswith(("https://", "http://")) for s in sources):
        raise RuntimeError("Provide at least two reliable source URLs, one per line.")
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise RuntimeError("Style must be a Nafay catalogue slug.")
    work = Path(tempfile.mkdtemp(prefix="cartoonforge-nafay-"))
    output = Path("cartoonforge-nafay-output").resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        archive = work / "kit.zip"
        extract = work / "kit"
        extract.mkdir()
        fetch(KIT_URL, archive)
        with zipfile.ZipFile(archive) as z:
            if z.testzip():
                raise RuntimeError("The downloaded Nafay archive failed its integrity check.")
            for member in z.infolist():
                target = (extract / member.filename).resolve()
                if extract.resolve() not in target.parents and target != extract.resolve():
                    raise RuntimeError("Unsafe path in Nafay archive.")
            z.extractall(extract)
        kit = find_kit(extract)
        project = work / "project"
        (project / "data").mkdir(parents=True)
        lines = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
        if len(lines) < 3:
            raise RuntimeError("Script needs at least three complete sentences.")
        data = {
            "title": topic, "voice": voice, "speed": 1.05, "lead": 0.35,
            "outro": 1.1, "gap": 0.22, "music": music, "sources": sources,
            "lines": [{"text": s, "caps": caption(s), "gap": 0.22} for s in lines]
        }
        (project / "script.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
        scripts = kit / "scripts"
        run([sys.executable, str(scripts / "voice.py"), str(project)])
        run([sys.executable, str(scripts / "words.py"), str(project)])

        catalog = (kit / "references/style-catalog.md").read_text()
        template = (kit / "references/prompt-template.md").read_text()
        style = entry_for(catalog, slug)
        source_url = "https://nafay3d.com/styles/" + slug + "/source.html"
        source_file = project / "reference-source.html"
        fetch(source_url, source_file)
        source = source_file.read_text(errors="replace")
        if "<html" not in source.lower() or len(source) < 5000:
            raise RuntimeError("The selected style reference source was not a complete HTML file.")
        line_times = (project / "data/lines.json").read_text()
        word_times = (project / "data/words.json").read_text()
        prompt = f"""
Follow this Nafay prompt template and selected style specification exactly:
{template}

Create a new original animation for this topic: {topic}
Narration script: {script}
Line timings: {line_times}
Word-level timings: {word_times}
Source URLs: {json.dumps(sources)}
Selected full style entry:
{style}

Build directly. Return one complete self-contained HTML document only. Preserve the source animation's shared helpers, player, CM and SFX systems, style identity, 9:16 720x1280 canvas, and required interfaces: window.seek(t), numeric window.DURATION, window.scoreSound, window.SFX.render(...), and a canvas. Replace the reference demo story with the supplied topic. Use the real word timings for captions and scene changes. Keep narration dominant, use the selected style's voiceover sound rules, create all geometry in code, and do not use external images or models. Every frame must be deterministic from time.

Complete unmodified reference source:
{source}
"""
        key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY is missing from repository Actions secrets.")
        model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        fallback = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
        html = None
        for chosen in [model, fallback]:
            if not chosen:
                continue
            url = "https://generativelanguage.googleapis.com/v1beta/models/" + chosen + ":generateContent"
            for delay in [0, 8, 20]:
                if delay:
                    time.sleep(delay)
                body = json.dumps({
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.25, "maxOutputTokens": 24000}
                }).encode()
                req = urllib.request.Request(url, data=body, headers={
                    "Content-Type": "application/json", "x-goog-api-key": key
                }, method="POST")
                try:
                    with urllib.request.urlopen(req, timeout=240) as response:
                        result = json.loads(response.read().decode())
                    html = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    break
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, KeyError, IndexError) as exc:
                    print(f"Gemini {chosen} retry: {exc}", flush=True)
            if html:
                break
        if not html:
            raise RuntimeError("Gemini could not generate the animation after retries and fallback.")
        fence = chr(96) * 3
        if html.startswith(fence):
            html = html.split("\n", 1)[1] if "\n" in html else html[len(fence):]
        if html.rstrip().endswith(fence):
            html = html.rstrip()[:-len(fence)]
        if not html.lstrip().lower().startswith(("<!doctype html", "<html")):
            raise RuntimeError("Gemini did not return a complete HTML document.")
        for required in ["<canvas", "window.seek", "window.DURATION", "window.scoreSound", "window.SFX"]:
            if required.lower() not in html.lower():
                raise RuntimeError("Generated animation is missing required interface: " + required)
        animation = project / "animation.html"
        animation.write_text(html)
        (project / "style-metadata.json").write_text(json.dumps({
            "slug": slug, "source_url": source_url, "topic": topic, "style_entry": style
        }, ensure_ascii=False, indent=2))
        chrome = os.environ.get("CHROME", "")
        renderer = [sys.executable, str(scripts / "render.py")]
        sheet = renderer + [str(animation), str(output / "contact-sheet.jpg"), "--sheet", "--step", "1.0"]
        final = renderer + [str(animation), str(output / "final.mp4"), "--vo", str(project / "data/narration.wav"), "--fps", "30", "--scale", "1.0"]
        if chrome:
            sheet += ["--chrome", chrome]
            final += ["--chrome", chrome]
        run(sheet)
        run(final)
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
            "-of", "json", str(output / "final.mp4")
        ], text=True))
        streams = probe.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), {})
        duration = float(probe.get("format", {}).get("duration", 0))
        audio = any(s.get("codec_type") == "audio" for s in streams)
        if not audio or not video.get("height") or video["height"] <= video.get("width", 0) or not 25 <= duration <= 45:
            raise RuntimeError("Final MP4 failed audio, portrait-orientation or duration checks.")
        for src, dst in [
            (project / "script.json", output / "script.json"),
            (project / "data/words.json", output / "word-timings.json"),
            (project / "style-metadata.json", output / "style-metadata.json")
        ]:
            shutil.copy2(src, dst)
        (output / "qa-report.json").write_text(json.dumps({
            "automated_checks": "passed", "visual_review": "pending", "publishable": False,
            "duration_seconds": round(duration, 2), "width": video.get("width"),
            "height": video.get("height"), "audio_present": audio,
            "contact_sheet_generated": (output / "contact-sheet.jpg").exists(),
            "every_frame_visually_inspected": False
        }, indent=2))
        print("MP4 and contact sheet created. Visual QA is still pending.", flush=True)
    finally:
        shutil.rmtree(work, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("CartoonForge Nafay render failed: " + str(exc), file=sys.stderr)
        sys.exit(1)
