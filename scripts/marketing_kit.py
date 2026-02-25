"""
scripts/marketing_kit.py
─────────────────────────────────────────────────────────────────
CooCook Marketing Content Generator
Generates: Social media posts, Press releases, Landing page copy

Usage:
  python scripts/marketing_kit.py --social "Food trends 2026"
  python scripts/marketing_kit.py --press "New chef feature launch"
  python scripts/marketing_kit.py --landing "Tagline for homepage"
─────────────────────────────────────────────────────────────────
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from core import get_logger

try:
    from anthropic import Anthropic
    CLIENT = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
except Exception:
    CLIENT = None

logger = get_logger("MKT", "Marketing-Kit")

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "marketing"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Content Generators ────────────────────────────────────────

def generate_social_posts(topic: str, platforms: list[str] = None) -> dict:
    """Generate platform-specific social media posts"""
    if not CLIENT:
        return {"error": "Claude API not configured"}

    if platforms is None:
        platforms = ["twitter", "instagram", "linkedin"]

    logger.info(f"Generating social posts for: {topic}")

    try:
        response = CLIENT.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Create social media posts about: {topic}\n\n"
                        f"Format 3 posts:\n"
                        f"1. Twitter (280 chars, 1-2 emojis, hashtags)\n"
                        f"2. Instagram (2-3 paragraphs, 5-10 hashtags, call-to-action)\n"
                        f"3. LinkedIn (professional tone, industry insight, 1-2 paragraphs)\n\n"
                        f"Make them engaging and on-brand for CooCook."
                    ),
                }
            ],
        )

        content = response.content[0].text
        posts = {
            "topic": topic,
            "generated_at": datetime.utcnow().isoformat(),
            "content": content,
            "word_count": len(content.split()),
        }

        # Save to file
        filename = f"social_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)

        logger.info(f"Social posts saved to {filename}")
        return posts

    except Exception as e:
        logger.error(f"Social post generation failed: {e}")
        return {"error": str(e)}


def generate_press_release(announcement: str) -> dict:
    """Generate professional press release"""
    if not CLIENT:
        return {"error": "Claude API not configured"}

    logger.info(f"Generating press release for: {announcement}")

    try:
        response = CLIENT.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write a professional press release for CooCook about: {announcement}\n\n"
                        f"Structure:\n"
                        f"- HEADLINE (compelling, max 12 words)\n"
                        f"- SUBHEADING (supporting detail, max 15 words)\n"
                        f"- FIRST PARAGRAPH (lead, key facts, 2-3 sentences)\n"
                        f"- BODY (details, impact, quotes from executives)\n"
                        f"- BOILERPLATE (About CooCook section, 50 words)\n"
                        f"- CONTACT (media contact info format)\n\n"
                        f"Tone: Professional, newsworthy, quote an imaginary CEO/founder."
                    ),
                }
            ],
        )

        content = response.content[0].text
        press = {
            "announcement": announcement,
            "generated_at": datetime.utcnow().isoformat(),
            "content": content,
            "format": "press_release",
        }

        filename = f"press_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Press release saved to {filename}")
        return press

    except Exception as e:
        logger.error(f"Press release generation failed: {e}")
        return {"error": str(e)}


def generate_landing_copy(focus: str) -> dict:
    """Generate landing page copy"""
    if not CLIENT:
        return {"error": "Claude API not configured"}

    logger.info(f"Generating landing page copy for: {focus}")

    try:
        response = CLIENT.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=900,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write landing page copy for CooCook focusing on: {focus}\n\n"
                        f"Sections:\n"
                        f"1. Hero Headline (1 powerful sentence, max 10 words)\n"
                        f"2. Subheading (benefit-driven, max 15 words)\n"
                        f"3. Value Proposition (3-4 core benefits, bullet points)\n"
                        f"4. Social Proof (imaginary statistic + quote)\n"
                        f"5. Call-to-Action (urgent, benefit-focused)\n\n"
                        f"Tone: Conversational, exciting, consumer-focused."
                    ),
                }
            ],
        )

        content = response.content[0].text
        landing = {
            "focus": focus,
            "generated_at": datetime.utcnow().isoformat(),
            "content": content,
            "format": "landing_page",
        }

        filename = f"landing_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Landing page copy saved to {filename}")
        return landing

    except Exception as e:
        logger.error(f"Landing copy generation failed: {e}")
        return {"error": str(e)}


def generate_email_campaign(campaign_type: str) -> dict:
    """Generate email marketing campaign"""
    if not CLIENT:
        return {"error": "Claude API not configured"}

    logger.info(f"Generating email campaign: {campaign_type}")

    try:
        response = CLIENT.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write an email campaign for CooCook - Type: {campaign_type}\n\n"
                        f"Include:\n"
                        f"- Subject line (max 50 chars, attention-grabbing)\n"
                        f"- Preheader text (max 50 chars)\n"
                        f"- Body (3-4 short paragraphs)\n"
                        f"- CTA button (clear action)\n"
                        f"- Footer (unsubscribe + social links)\n\n"
                        f"Campaign types: welcome, abandonment, re-engagement, promotion"
                    ),
                }
            ],
        )

        content = response.content[0].text
        email = {
            "campaign_type": campaign_type,
            "generated_at": datetime.utcnow().isoformat(),
            "content": content,
        }

        filename = f"email_{campaign_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Email campaign saved to {filename}")
        return email

    except Exception as e:
        logger.error(f"Email campaign generation failed: {e}")
        return {"error": str(e)}


# ─── CLI Interface ────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CooCook Marketing Kit")
    parser.add_argument("--social", type=str, help="Generate social media posts")
    parser.add_argument("--press", type=str, help="Generate press release")
    parser.add_argument("--landing", type=str, help="Generate landing page copy")
    parser.add_argument("--email", type=str, help="Generate email campaign")
    parser.add_argument("--list", action="store_true", help="List generated files")
    args = parser.parse_args()

    if args.social:
        result = generate_social_posts(args.social)
        print_result("Social Media Posts", result)

    elif args.press:
        result = generate_press_release(args.press)
        print_result("Press Release", result)

    elif args.landing:
        result = generate_landing_copy(args.landing)
        print_result("Landing Page Copy", result)

    elif args.email:
        result = generate_email_campaign(args.email)
        print_result("Email Campaign", result)

    elif args.list:
        print("\n📂 Generated Marketing Assets:")
        print(f"   Directory: {OUTPUT_DIR}\n")
        for file in sorted(OUTPUT_DIR.glob("*")):
            size = file.stat().st_size / 1024
            print(f"   📄 {file.name} ({size:.1f} KB)")

    else:
        parser.print_help()


def print_result(title: str, result: dict):
    """Pretty print result"""
    if "error" in result:
        print(f"\n❌ {title} Generation Failed:")
        print(f"   {result['error']}\n")
    else:
        print(f"\n✅ {title} Generated:")
        print("=" * 60)
        if "content" in result:
            print(result["content"][:300] + "...\n")
        print(f"📁 Saved to: {OUTPUT_DIR}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
