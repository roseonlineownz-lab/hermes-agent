---
name: comfyui-telegram-trigger
description: Trigger ComfyUI image generation workflows from Telegram. Supports prompt queuing, batch generation, NSFW-aware pipelines, and result delivery back to Telegram.
category: automation
tags: [comfyui, telegram, image-generation, nsfw, batch]
---

# ComfyUI Telegram Trigger

Triggers: user sends image prompt via Telegram, or requests batch generation from CLI.

## What It Does

1. Accepts image generation prompts via Telegram or CLI
2. Routes to ComfyUI API (:8188) with the appropriate workflow
3. Supports multiple workflow presets (portrait, landscape, NSFW, batch)
4. Queues requests when ComfyUI is busy
5. Delivers generated images back to Telegram
6. Saves all outputs to ~/ComfyUI/output/ with structured naming

## Required Setup

- ComfyUI running on :8188 with API enabled (--enable-api flag)
- Telegram bot configured in Hermes gateway
- Workflow JSON templates in ~/.hermes/data/comfyui/workflows/

## Workflow Presets

| Preset | Resolution | Steps | Sampler | Best For |
|--------|-----------|-------|---------|----------|
| quick | 512x512 | 20 | euler | Fast previews |
| portrait-hq | 768x1344 | 30 | dpmpp_2m | High quality portraits |
| landscape-hq | 1344x768 | 30 | dpmpp_2m | Scenes, landscapes |
| nsfw-standard | 768x1152 | 25 | dpmpp_2m | Adult content (standard) |
| nsfw-hq | 1024x1536 | 35 | dpmpp_2m | Adult content (high quality) |
| batch-4 | 512x512 | 20 | euler | 4 variations, fast |
| batch-hq | 768x768 | 30 | dpmpp_2m | 4 variations, quality |

## Usage

### From Telegram
```
/gen quick een kat in ruimtepak
/gen portrait-hq cinematic portrait van een cyberpunk karakter
/gen nsfw-hq [prompt]
/gen batch-hq 4 variaties van [prompt]
```

### From CLI
```
comfyui generate --preset portrait-hq "cinematic portrait, moody lighting"
comfyui batch --preset batch-4 --count 4 "abstract geometric patterns"
comfyui workflow --custom ~/.hermes/data/comfyui/workflows/custom.json
```

### Queue Management
```
comfyui queue status
comfyui queue cancel [id]
comfyui queue clear
```

## API Flow

1. POST to :8188/prompt with workflow JSON + prompt injection
2. Poll :8188/history/{prompt_id} for completion
3. On completion, download output image from :8188/view?filename=...
4. Save locally + send to Telegram as photo

## Prompt Enhancement

Before sending to ComfyUI, prompts are enhanced with:
- Quality tags: "masterpiece, best quality, highly detailed"
- Negative prompt injection: "bad anatomy, blurry, low quality, watermark, text"
- Style-specific LoRA hints if configured

## Telegram Delivery

- Images under 10MB: direct photo upload
- Images over 10MB: send URL or compressed version
- Batch results: send as media group (up to 10 images)
- Queue position updates: text message with ETA

## Pitfalls

- ComfyUI can only process 1 prompt at a time — use the queue system
- Large resolution NSFW workflows may hit VRAM limits on RTX 5070 Ti (12GB) — monitor with nvidia-smi
- Telegram has a 50MB file size limit for bots
- Workflow JSONs are model-dependent — changing checkpoint breaks workflows
- If ComfyUI crashes mid-generation, the queue is lost — implement persistence
- NSFW content must respect Telegram's content policies for bot messages
