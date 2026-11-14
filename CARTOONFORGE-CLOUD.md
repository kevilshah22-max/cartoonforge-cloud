# CartoonForge Cloud

CartoonForge is the cartoon-focused cloud workflow layered on top of MoneyPrinterTurbo 1.3.10. The upstream application remains intact; this project adds a recurring-character prompt builder and a GitHub Actions render entry point.

## First workflow

1. Accepts a complete story/script and a recurring character description.
2. Splits the script into 3–8 sequential scene beats.
3. Repeats the same character design constraints and selected art direction in every scene prompt.
4. Uses MoneyPrinterTurbo's existing OpenAI-compatible image-material provider to generate scene artwork.
5. Uses the upstream pipeline for narration, subtitles, background audio and MP4 assembly.
6. Uploads the MP4 as a downloadable GitHub Actions artifact.

The initial renderer creates illustrated scenes with animated pan/zoom motion. It is not yet full frame-by-frame character animation. Repeating the character description encourages consistency, but image models can still vary details. Reference-image conditioning and direct text-to-video are later milestones.

## Required GitHub Actions secrets

Open **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Purpose |
| --- | --- |
| `OPENAI_IMAGE_BASE_URL` | OpenAI-compatible image API base URL, e.g. `https://api.openai.com/v1` |
| `OPENAI_IMAGE_MODEL` | Image model supported by that endpoint |
| `OPENAI_IMAGE_API_KEY` | Endpoint API key; optional only for unauthenticated endpoints |

Credentials are not committed. Provider pricing, quotas and terms apply. GitHub Actions supplies CPU rendering and FFmpeg, not a GPU or free image-generation credits.

## Run

1. Open the **Actions** tab.
2. Select **CartoonForge — Create Cartoon Video**.
3. Select **Run workflow**.
4. Paste the script, describe the recurring character, and choose style, scene count and voice.
5. Start the workflow.
6. When complete, open the run and download the `cartoonforge-video-*` artifact.

FFmpeg is installed on the GitHub runner. You do not need to install FFmpeg or download the project to Windows to render.

## Current limitations

- The first pass generates still images and turns them into moving video clips; it is not yet full generative character animation.
- The endpoint must implement the OpenAI-compatible `/images/generations` API expected by MoneyPrinterTurbo.
- Each image may incur provider charges. Check pricing before running.
- A first successful workflow run is required to verify provider compatibility and MP4 output.
- GitHub-hosted runners have execution-time and storage limits; render longer episodes in shorter batches.

## Upstream

This repository is a fork of [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), based on version 1.3.10. The upstream MIT licence and copyright notice remain in `LICENSE`.
