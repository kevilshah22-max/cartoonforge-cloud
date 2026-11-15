# CartoonForge 2.0 — optional AI motion

CartoonForge keeps the existing free MoneyPrinterTurbo render as its baseline. When
`MAGIC_HOUR_API_KEY` is configured, the cloud runner can add a generative motion pass
to the scene images and replace the baseline video's visual track while retaining its
narration audio. If the provider is unavailable, the baseline MP4 is kept.

## Enable the optional motion pass

1. Create a free Magic Hour developer account at https://magichour.ai/developer.
2. Create an API key in the Developer dashboard.
3. In this GitHub repository, open **Settings → Secrets and variables → Actions**.
4. Add a repository secret named `MAGIC_HOUR_API_KEY` and paste the key as its value.
5. Run **Actions → CartoonForge — Create Cartoon Video → Run workflow**.

No payment card is required to create the account or obtain the advertised starter
credits. The current provider documentation advertises 400 signup credits. This
integration uses the LTX 2.5 model at 480p and limits a run to at most 360 estimated
credits (normally three 5-second scene clips), leaving a small reserve. Actual
availability, model access, and credit balances are controlled by Magic Hour and can
change. The workflow does not purchase credits or subscribe on the user's behalf.

## Important limitations

- The Magic Hour pass is optional. Without the secret, the existing free baseline
  render runs unchanged.
- If the provider rejects the key, runs out of credits, times out, or returns an
  invalid result, CartoonForge logs the reason and keeps the original MP4.
- Free-account generations are for personal, non-commercial use under Magic Hour's
  current terms. Commercial use requires a paid subscription, credit-pack purchase,
  or separately agreed paid usage-based arrangement.
- Free LTX 2.5 output is 480p. The baseline renderer and audio remain responsible
  for narration, subtitles, and final MP4 assembly.
- AI video generation can alter fine character details between clips. Character
  consistency must be checked in the resulting MP4; this integration does not claim
  perfect identity preservation.

Provider documentation:
- https://docs.magichour.ai/tools/video/image-to-video
- https://docs.magichour.ai/api-reference/video-projects/image-to-video
- https://magichour.ai/faq
