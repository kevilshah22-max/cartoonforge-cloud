# CartoonForge Cloud

**Turn a cartoon script into a downloadable MP4 from GitHub Actions — without a local GPU or local FFmpeg installation.**

Built on [MoneyPrinterTurbo 1.3.10](https://github.com/harry0703/MoneyPrinterTurbo), with a cartoon-oriented scene and recurring-character prompt workflow.

The workflow is preconfigured for OVHcloud's free Stable Diffusion XL image-generation model and supports anonymous API access. No provider API key is needed for the default setup.

Read [CARTOONFORGE-CLOUD.md](CARTOONFORGE-CLOUD.md) for setup, run instructions and limitations.

## Status

The workflow and scene-prompt builder are the initial implementation. The first provider-backed render still needs to be tested. The initial renderer creates animated still-image scenes with narration/subtitles and MP4 assembly; full character animation and reference-image conditioning are subsequent milestones.
