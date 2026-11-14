# CartoonForge Cloud

CartoonForge is the cartoon-focused cloud workflow layered on top of MoneyPrinterTurbo 1.3.10. The upstream application remains intact; this project adds a recurring-character prompt builder and a GitHub Actions render entry point.

## First workflow

1. Accepts a complete story/script and a recurring character description.
2. Splits the script into 3–8 sequential scene beats.
3. Repeats the same character design constraints and selected art direction in every scene prompt.
4. Uses OVHcloud's free Stable Diffusion XL (SDXL) image-generation model to generate scene artwork.
5. Uses the upstream pipeline for narration, subtitles, background audio and MP4 assembly.
6. Uploads the MP4 as a downloadable GitHub Actions artifact.

The initial renderer creates illustrated scenes with animated pan/zoom motion. It is not yet full frame-by-frame character animation. Repeating the character description encourages consistency, but image models can still vary details. Reference-image conditioning and direct text-to-video are later milestones.

## Image generation: OVHcloud free SDXL

CartoonForge is preconfigured to use:

- API base URL: `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1`
- Model: `stable-diffusion-xl-base-v10`
- Endpoint: OpenAI-compatible `/images/generations`
- Authentication: none required for anonymous access

OVHcloud lists this SDXL model as **Free** and documents anonymous access at **2 requests per minute per IP and model**. The workflow uses anonymous access by default, so you do not need to create an OVHcloud account, add a payment card, or configure API secrets to try it. GitHub-hosted runners use shared infrastructure, so another user sharing an outbound IP could temporarily affect the rate limit.

Optional authenticated access is supported through the GitHub Actions secret `OVH_AI_ENDPOINTS_ACCESS_TOKEN`. This is not needed for the free anonymous path. OVHcloud's documentation says creating an authenticated AI Endpoints key requires a Public Cloud project with a payment method, so do not create one just for this initial test.

Official references:
- [OVHcloud SDXL model and API example](https://www.ovhcloud.com/en-gb/public-cloud/ai-endpoints/catalog/stable-diffusion-xl/)
- [OVHcloud AI Endpoints access and anonymous rate limits](https://docs.ovhcloud.com/en/guides/public-cloud/ai-machine-learning/ai-endpoints-getting-started/)

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
- Anonymous image generation is rate-limited to two requests per minute per IP/model. A 3–8 scene render may take several minutes and can be affected by shared GitHub runner IP usage.
- The image model is free according to OVHcloud's current catalogue; service terms and quotas can change.
- A first successful workflow run is required to verify provider compatibility and MP4 output.
- GitHub-hosted runners have execution-time and storage limits; render longer episodes in shorter batches.

## Upstream

This repository is a fork of [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), based on version 1.3.10. The upstream MIT licence and copyright notice remain in `LICENSE`.
