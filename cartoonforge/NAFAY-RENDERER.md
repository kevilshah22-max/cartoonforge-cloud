# CartoonForge × Nafay 3D Style Renderer

This is a separate rendering engine inside CartoonForge Cloud. It does not replace the existing MoneyPrinterTurbo / OVH SDXL workflow.

## What it does

1. Accepts a topic and a fact-checked 70–125 word narration script.
2. Downloads the official Nafay faceless-shorts runtime kit into a temporary GitHub Actions workspace.
3. Looks up the selected style slug in the full 62-style catalogue and fetches that style's complete public source.html.
4. Generates local Kokoro narration and word-level timings.
5. Builds a style-specific animation prompt using the Nafay prompt template, the complete style entry, voice timings and full reference source.
6. Uses Gemini to create a new self-contained animation HTML file.
7. Renders a timestamped contact sheet, then renders the final MP4 with the style's procedural sound kit mixed under narration.
8. Checks MP4 streams, portrait orientation and duration, and uploads the MP4, contact sheet, script, timings and QA report as a GitHub Actions artifact.

## Run

1. Add GEMINI_API_KEY under Settings → Secrets and variables → Actions.
2. Open Actions → CartoonForge — Nafay Style Renderer → Run workflow.
3. Enter a topic, a fact-checked script, and a style slug such as bio-glow, cosmic-scale, clay-diorama, low-poly-atlas, storybook or evidence-board.
4. Select a Kokoro voice. Music and sound effects follow the selected style's built-in sound design.
5. Download the cartoonforge-nafay artifact after the workflow completes.

The renderer uses local Kokoro-82M TTS, Whisper word alignment (with the upstream timing fallback), headless Chrome and FFmpeg. No dedicated GPU is required; 3D rendering uses Chrome's software-rendering fallback on the GitHub runner.

## QA / publishing guardrail

A successful workflow means the MP4 passed automated technical checks. It does not mean visual QA is complete. The contact sheet must still be inspected for visual defects, scene coherence, text readability, caption timing and pacing. The generated qa-report.json deliberately sets visual_review to pending and publishable to false. This workflow does not upload to YouTube.

## Attribution and source integrity

The style catalogue and rendering workflow are by Nafay 3D (https://nafay3d.com). The workflow fetches the public runtime kit and each selected style's complete reference source at run time, leaves those files unmodified, and uses them as the basis for an original topic-specific animation. When sharing a video made in a Nafay style, credit Nafay 3D where appropriate. Do not imply affiliation.

## Existing CartoonForge workflow

The existing CartoonForge — Create Cartoon Video workflow remains unchanged. This renderer is an additional engine; both workflows can coexist.
