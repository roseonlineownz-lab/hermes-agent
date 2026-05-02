---
name: viral-content-generator
description: Creates viral video scripts, trending topics, and AI video prompts for social media marketing agencies
---

# Viral Content Generator

Generate viral-worthy content for client social media accounts.

## Capabilities

1. **Trend Research** - Find trending topics in any niche
2. **Script Writing** - Create engaging short-form video scripts (TikTok, Reels, Shorts)
3. **Video Prompts** - Generate AI video generation prompts for ComfyUI/Higgsfield
4. **Hook Generator** - Create scroll-stopping hooks
5. **CTA Builder** - Build conversion-focused calls-to-action

## Usage

### Generate Viral Content Package

```bash
/hermes viral-content --niche "e-commerce" --topic "skincare" --platform "tiktok" --count 5
```

### Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `--niche` | e-commerce, coaching, real-estate, fitness, finance | Target industry |
| `--topic` | any | Specific product/topic |
| `--platform` | tiktok, instagram, youtube, linkedin | Target platform |
| `--count` | 1-10 | Number of variations |
| `--tone` | professional, casual, humorous, urgent | Content tone |

### Output Format

For each video concept:
- **Hook** (0-3 sec) - Scroll-stopping opener
- **Script** (15-60 sec) - Full video script with timing
- **Visual Prompt** - AI video generation prompt
- **Caption** - Social media caption with hashtags
- **CTA** - Call-to-action

## Example Request

```
Create 3 viral video concepts for a skincare brand selling vitamin C serum
Target: Instagram Reels
Tone: Professional but approachable
```

## Example Output

### Video 1: "The Morning Mistake"

**Hook:** "Stop applying vitamin C wrong! 90% of people make this mistake..."

**Script:**
- 0-3s: [Close-up of person applying serum incorrectly]
- 3-10s: "You're applying vitamin C on dry skin. Here's why that's wrong..."
- 10-20s: [Demonstration of correct method on damp skin]
- 20-30s: "Damp skin = 3x better absorption. Try it tomorrow!"

**Visual Prompt:** "Close-up beauty shot, woman applying serum, soft morning light, skincare routine, Instagram aesthetic, 4k"

**Caption:** "The #1 vitamin C mistake 🍊 Save this for tomorrow morning! #skincare #vitaminc #glowingskin"

**CTA:** "Shop our Vitamin C Serum - Link in bio!"

---

## Integration

This skill works with:
- **ComfyUI** - For AI video generation
- **Higgsfield API** - For video synthesis
- **OpenClaw** - For auto-posting workflows
- **Hermes** - For script generation

## Pricing Template

Include in client proposals:

```
Viral Content Package:
- 10 video concepts/week: €500
- 20 video concepts/week: €900  
- 50 video concepts/week: €2000

Includes: Scripts, prompts, captions, posting schedule
```
