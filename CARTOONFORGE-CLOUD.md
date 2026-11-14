# CartoonForge Cloud

CartoonForge is the cartoon-focused cloud workflow layered on top of MoneyPrinterTurbo 1.3.10. The upstream application remains intact; this project adds a recurring-character prompt builder, optional Gemini story creation and a GitHub Actions render entry point.

## First workflow

1. Enter a short story idea.
2. Optionally add a script or character direction; Gemini can create both automatically.
3. Choose art style, scene count and narration voice.
4. CartoonForge asks Gemini to create a coherent script and a repeatable visual character bible (when auto-creation is enabled).
5. It splits the script into sequential scene beats and repeats the character design constraints in every image prompt.
6. OVHcloud's free Stable Diffusion XL (SDXL) model generates scene artwork.
7. The upstream pipeline creates narration, subtitles, background audio and an MP4.
8. The MP4 is uploaded as a downloadable GitHub Actions artifact.

The initial renderer creates illustrated scenes with animated pan/zoom motion. It is not yet full frame-by-frame character animation. Repeating the character description encourages consistency, but image models can still vary details. Reference-image conditioning and direct text-to-video are later milestones.

## Gemini story and character creation

The workflow's **Use Gemini to write the script and design the recurring character** option is enabled by default.

One-time setup:
1. Open [Google AI Studio API keys](https://aistudio.google.com/app/apikey).
2. Create a Gemini API key on a Free Tier project.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Select **New repository secret**.
5. Set the name to `GEMINI_API_KEY` and paste the key as the value.

The workflow uses the Gemini API to generate the story script and recurring-character description from the user's idea. The key stays in GitHub Actions secrets and is not written into the repository. Google's Gemini API offers a free tier for supported models, including limited quotas; availability and limits depend on the model and project. Do not link a paid billing project if you want to keep this setup free.

Official references:
- [Google AI Studio API keys](https://aistudio.google.com/app/apikey)
- [Gemini API pricing and free tier](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API billing and free-tier availability in the UK](https://ai.google.dev/gemini-api/docs/billing)

If you do not configure the Gemini secret, disable auto-creation and provide both the complete script and recurring character description manually.

## Image generation: OVHcloud free SDXL

CartoonForge is preconfigured to use:

- API base URL: `https://oai.endpoints.kepler.ai.cloud.ovh.net/v1`
- Model: `stable-diffusion-xl-base-v10`
- Endpoint: OpenAI-compatible `/images/generations`
- Image size: `1024x1024` (the size accepted by this OVHcloud model)
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
4. Enter a short story idea. Leave auto-creation enabled to let Gemini write the script and design the character.
5. Optionally add extra script or character direction, then choose style, scene count and voice.
6. Start the workflow.
7. When complete, open the run and download the `cartoonforge-video-*` artifact.

FFmpeg is installed on the GitHub runner. You do not need to install FFmpeg or download the project to Windows to render.

## Current limitations

- The first pass generates still images and turns them into moving video clips; it is not yet full generative character animation.
- Anonymous image generation is rate-limited to two requests per minute per IP/model. A 3–8 scene render may take several minutes and can be affected by shared GitHub runner IP usage.
- Gemini's free tier has model-specific request/token quotas and may change over time. A rate-limit response requires waiting or retrying.
- The image model is free according to OVHcloud's current catalogue; service terms and quotas can change.
- A first successful workflow run is required to verify provider compatibility and MP4 output.
- GitHub-hosted runners have execution-time and storage limits; render longer episodes in shorter batches.

## Upstream

This repository is a fork of [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), based on version 1.3.10. The upstream MIT licence and copyright notice remain in `LICENSE`.
