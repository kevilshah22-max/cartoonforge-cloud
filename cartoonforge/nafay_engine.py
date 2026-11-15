#!/usr/bin/env python3
"""CartoonForge adapter for Nafay 3D's faceless-short renderer."""
import json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request, urllib.error, zipfile
from pathlib import Path

KIT_URL = "https://nafay3d.com/skills/faceless-shorts/faceless-shorts-skill.zip?v=7"

def run(args):
    print("+", " ".join(map(str, args)), flush=True)
    subprocess.run(args, check=True)

def fetch(url, path):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/zip,*/*;q=0.8",
        "Referer": "https://nafay3d.com/"
    })
    with urllib.request.urlopen(req, timeout=240) as response, open(path, "wb") as out:
        shutil.copyfileobj(response, out)
        return response.headers.get("Content-Type", "unknown")

def find_kit(root):
    for p in [root, *root.rglob("*")]:
        if (p / "scripts/voice.py").is_file() and (p / "scripts/words.py").is_file():
            return p
    files = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())
    preview = ", ".join(files[:100]) or "(archive contains no files)"
    raise RuntimeError("Nafay voice/timing kit not recognised. Extracted files: " + preview)

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
    sources = [s.strip() for s in re.split(r"[;\n]+", os.environ.get("NAFAY_SOURCES", "")) if s.strip()]
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

        if slug != "bio-glow":
            raise RuntimeError("The cloud animation generator currently supports bio-glow.")
        animation = project / "animation.html"
        source_file = project / "reference-source.html"
        source_file.write_text("CartoonForge deterministic Bio Glow adaptation; original Nafay source is not used as a story fallback.\\n")
        run([sys.executable, str(Path(__file__).resolve().parent / "vein_animation.py"), str(project), str(animation)])
        preview_only = False
        (project / "style-metadata.json").write_text(json.dumps({
            "slug": slug, "topic": topic, "style_entry": "Bio Glow-inspired red-cell science animation",
            "generator": "CartoonForge deterministic scene generator"
        }, ensure_ascii=False, indent=2))
        chrome = os.environ.get("CHROME", "")
        renderer = [sys.executable, str(Path(__file__).resolve().parent / "nafay-kit" / "render.py")]
        sheet = renderer + [str(animation), str(output / "contact-sheet.jpg"), "--sheet", "--step", "0.5"]
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
            (project / "style-metadata.json", output / "style-metadata.json"),
            (source_file, output / "reference-source.html"),
            (animation, output / "animation.html"),
            (project / "data/narration.wav", output / "narration.wav")
        ]:
            shutil.copy2(src, dst)
        (output / "qa-report.json").write_text(json.dumps({
            "automated_checks": "passed", "visual_review": "pending", "publishable": False,
            "preview_only": preview_only,
            "preview_note": "Original Bio Glow style sample used as a preview; not the final topic-adapted animation." if preview_only else None,
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
