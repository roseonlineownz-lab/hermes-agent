#!/usr/bin/env python3
"""
Viral Content Generator - Creates viral video scripts and prompts
For NovaMaster AI Content Agency
"""

import json
import sys
from datetime import datetime

# Viral hooks database
VIRAL_HOOKS = {
    "controversial": [
        "Stop doing {topic} wrong!",
        "The truth about {topic} nobody tells you",
        "Why I quit {topic} (and you should too)",
        "{topic} is a scam. Here's why.",
        "Unpopular opinion: {topic}"
    ],
    "curiosity": [
        "I tried {topic} for 30 days. Here's what happened...",
        "The {topic} hack that changed everything",
        "What nobody tells you about {topic}",
        "I wish I knew this before starting {topic}",
        "The secret to {topic} nobody talks about"
    ],
    "educational": [
        "How to {topic} in 60 seconds",
        "3 {topic} tips that actually work",
        "The only {topic} guide you'll ever need",
        "{topic} explained simply",
        "Master {topic} with this one trick"
    ],
    "transformation": [
        "My {topic} transformation (before/after)",
        "From zero to hero: My {topic} journey",
        "How {topic} changed my life",
        "30 day {topic} challenge results",
        "This {topic} hack saved me 10 hours/week"
    ]
}

# Platform-specific best practices
PLATFORM_SPECS = {
    "tiktok": {
        "duration": "15-60 seconds",
        "aspect": "9:16 vertical",
        "hook_length": "0-3 seconds",
        "hashtag_count": "3-5",
        "caption_max": 150,
        "best_times": ["6-9 AM", "7-11 PM"],
        "trending_audio": True
    },
    "instagram": {
        "duration": "15-90 seconds (Reels)",
        "aspect": "9:16 vertical or 4:5",
        "hook_length": "0-3 seconds",
        "hashtag_count": "5-10",
        "caption_max": 2200,
        "best_times": ["9-11 AM", "7-9 PM"],
        "trending_audio": True
    },
    "youtube": {
        "duration": "15-60 seconds (Shorts)",
        "aspect": "9:16 vertical",
        "hook_length": "0-5 seconds",
        "hashtag_count": "3-5",
        "caption_max": 5000,
        "best_times": ["12-4 PM", "6-9 PM"],
        "trending_audio": False
    },
    "linkedin": {
        "duration": "30-90 seconds",
        "aspect": "1:1 square or 9:16",
        "hook_length": "0-5 seconds",
        "hashtag_count": "3-5",
        "caption_max": 3000,
        "best_times": ["8-10 AM", "12-1 PM"],
        "trending_audio": False
    }
}

# CTA templates
CTAS = {
    "engagement": [
        "Save this for later!",
        "Share with someone who needs this",
        "Comment your thoughts below",
        "Double tap if you agree!",
        "Tag a friend who needs to see this"
    ],
    "conversion": [
        "Link in bio to shop",
        "DM me '{keyword}' for details",
        "Limited spots available - apply now",
        "Free trial - link in bio",
        "Use code VIRAL20 for 20% off"
    ],
    "follow": [
        "Follow for more {topic} tips",
        "Follow for daily {niche} content",
        "Hit follow for part 2",
        "Follow to join the community",
        "New videos daily - follow!"
    ]
}


def generate_hooks(niche: str, topic: str, tone: str = "curiosity") -> list:
    """Generate 5 viral hooks based on parameters"""
    hooks = []
    templates = VIRAL_HOOKS.get(tone, VIRAL_HOOKS["curiosity"])

    for template in templates[:5]:
        hook = template.format(topic=topic, niche=niche)
        hooks.append(hook)

    # Add custom hooks
    custom_hooks = [
        f"POV: You finally discovered the secret to {topic}",
        f"Rating viral {niche} hacks so you don't have to",
        f"Things I wish I knew before starting {topic}",
    ]
    hooks.extend(custom_hooks[:2])

    return hooks


def generate_script(hook: str, topic: str, platform: str, duration: int = 30) -> dict:
    """Generate full video script with timing"""

    specs = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])

    # Parse hook type
    if "Stop" in hook or "wrong" in hook:
        script_type = "problem-solution"
    elif "tried" in hook or "days" in hook:
        script_type = "transformation"
    elif "How to" in hook or "tips" in hook:
        script_type = "educational"
    else:
        script_type = "storytelling"

    # Generate script structure
    script = {
        "type": script_type,
        "timing": {
            "hook": "0-3s",
            "setup": "3-10s",
            "value": "10-25s",
            "cta": "25-30s"
        },
        "scenes": []
    }

    if script_type == "problem-solution":
        script["scenes"] = [
            {"time": "0-3s", "visual": f"Close-up, frustrated expression", "audio": hook},
            {"time": "3-10s", "visual": "Show common mistake", "audio": f"Most people do {topic} wrong. Here's the problem..."},
            {"time": "10-25s", "visual": "Demonstrate correct method", "audio": f"The right way: [demonstration]. This changes everything."},
            {"time": "25-30s", "visual": "Happy result/reaction", "audio": "Try this today and let me know!"}
        ]
    elif script_type == "educational":
        script["scenes"] = [
            {"time": "0-3s", "visual": "Text overlay with hook", "audio": hook},
            {"time": "3-10s", "visual": "Introduction/setup shot", "audio": f"Let me break down {topic} in 30 seconds..."},
            {"time": "10-25s", "visual": "Step-by-step demonstration", "audio": "Step 1... Step 2... Step 3..."},
            {"time": "25-30s", "visual": "Summary/result", "audio": "Save this for later!"}
        ]
    else:
        script["scenes"] = [
            {"time": "0-3s", "visual": "Hook visual", "audio": hook},
            {"time": "3-10s", "visual": "Context setup", "audio": "Here's what happened..."},
            {"time": "10-25s", "visual": "Main content/payoff", "audio": "The results speak for themselves..."},
            {"time": "25-30s", "visual": "Conclusion", "audio": "Would you try this?"}
        ]

    return script


def generate_visual_prompt(script: dict, topic: str, niche: str) -> str:
    """Generate AI video generation prompt"""

    base_prompts = {
        "problem-solution": f"Professional {niche} content, before/after comparison, clean aesthetic, product showcase, 4k quality",
        "educational": f"Step-by-step {niche} tutorial, clear demonstration, text overlays, professional lighting, 4k",
        "transformation": f"Dramatic {niche} transformation, split screen before/after, emotional journey, cinematic, 4k",
        "storytelling": f"Narrative {niche} content, authentic moments, natural lighting, relatable, 4k quality"
    }

    base = base_prompts.get(script["type"], base_prompts["educational"])

    # Add style modifiers
    modifiers = [
        "vertical format",
        "social media optimized",
        "trending aesthetic",
        "high engagement visual",
        "scroll-stopping"
    ]

    return f"{base}, {', '.join(modifiers)}. Topic: {topic}"


def generate_caption(hook: str, topic: str, platform: str) -> str:
    """Generate social media caption with hashtags"""

    specs = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["instagram"])

    # Generate relevant hashtags
    hashtag_bases = {
        "skincare": ["#skincare", "#glowingskin", "#skincareroutine", "#skincaretips", "#healthyskin"],
        "fitness": ["#fitness", "#workout", "#fitnessmotivation", "#gym", "#fitfam"],
        "business": ["#business", "#entrepreneur", "#businesstips", "#success", "#mindset"],
        "food": ["#food", "#foodie", "#recipe", "#cooking", "#delicious"],
        "fashion": ["#fashion", "#style", "#ootd", "#fashionblogger", "#styleinspo"],
    }

    # Default hashtags
    default_tags = ["#viral", "#trending", "#fyp", "#explore", "#contentcreator"]

    # Find matching hashtags
    tags = hashtag_bases.get(topic.lower(), default_tags)

    # Generate caption
    caption = f"{hook}\n\n{topic} tips that actually work! 💯\n\n"
    caption += "Save this for later! 🔖\n\n"
    caption += " ".join(tags[:int(specs["hashtag_count"])])

    return caption[:specs["caption_max"]]


def generate_content_package(niche: str, topic: str, platform: str, count: int = 5, tone: str = "curiosity") -> list:
    """Generate complete viral content package"""

    packages = []

    # Generate hooks for each video
    all_hooks = generate_hooks(niche, topic, tone)

    for i in range(min(count, len(all_hooks))):
        hook = all_hooks[i]

        # Generate full content
        script = generate_script(hook, topic, platform)
        visual_prompt = generate_visual_prompt(script, topic, niche)
        caption = generate_caption(hook, topic, platform)

        # Select CTA
        cta_type = "engagement" if i % 2 == 0 else "conversion"
        cta = CTAS[cta_type][i % len(CTAs[cta_type])]

        package = {
            "video_number": i + 1,
            "hook": hook,
            "script": script,
            "visual_prompt": visual_prompt,
            "caption": caption,
            "cta": cta,
            "platform_specs": PLATFORM_SPECS[platform],
            "estimated_production_time": "15-30 minutes"
        }

        packages.append(package)

    return packages


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate viral content for social media")
    parser.add_argument("--niche", default="e-commerce", help="Target niche")
    parser.add_argument("--topic", default="skincare", help="Specific topic")
    parser.add_argument("--platform", default="instagram", choices=["tiktok", "instagram", "youtube", "linkedin"])
    parser.add_argument("--count", type=int, default=5, help="Number of videos to generate")
    parser.add_argument("--tone", default="curiosity", choices=["controversial", "curiosity", "educational", "transformation"])
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    print(f"\n🎬 Generating {args.count} viral {args.platform} videos for {args.niche}: {args.topic}\n")

    packages = generate_content_package(
        niche=args.niche,
        topic=args.topic,
        platform=args.platform,
        count=args.count,
        tone=args.tone
    )

    for pkg in packages:
        print(f"\n{'='*60}")
        print(f"📹 VIDEO {pkg['video_number']}")
        print(f"{'='*60}")
        print(f"\n🪝 HOOK: {pkg['hook']}")
        print(f"\n📝 SCRIPT:")
        for scene in pkg['script']['scenes']:
            print(f"   {scene['time']}: {scene['audio']}")
            print(f"      Visual: {scene['visual']}")
        print(f"\n🎨 VISUAL PROMPT: {pkg['visual_prompt']}")
        print(f"\n📝 CAPTION: {pkg['caption']}")
        print(f"\n📣 CTA: {pkg['cta']}")
        print(f"\n⏱️  Production time: {pkg['estimated_production_time']}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(packages, f, indent=2)
        print(f"\n💾 Saved to {args.output}")


if __name__ == "__main__":
    main()
