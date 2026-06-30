"""Generate a real, color-accurate product photo for every catalog item using
an AI image model via OpenRouter, saved as static files the frontend serves at
/products/<slug>.jpg.

Usage (run locally, NOT on the serverless server):
    pip install requests pillow
    export OPENROUTER_API_KEY=sk-or-...   # PowerShell: $env:OPENROUTER_API_KEY="sk-or-..."
    python manage.py generate_product_images           # generate missing only
    python manage.py generate_product_images --force   # regenerate all

Images are written to <repo>/frontend/public/products/. Commit them and deploy
the frontend; the seed sets each product's image_url to /products/<slug>.jpg.
"""
import base64
import io
import os
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from assistify.apps.products.management.commands.seed_products import (
    LINES,
    PROMPT_NOUNS,
    product_slug,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _output_dir():
    root = Path(__file__).resolve()
    while root != root.parent and not (root / "frontend").exists():
        root = root.parent
    out = root / "frontend" / "public" / "products"
    out.mkdir(parents=True, exist_ok=True)
    return out


class Command(BaseCommand):
    help = "Generate real product images (per type + color) via an OpenRouter image model."

    def add_arguments(self, parser):
        parser.add_argument("--model", default="google/gemini-2.5-flash-image", help="OpenRouter image model id")
        parser.add_argument("--width", type=int, default=800, help="Saved image width (px)")
        parser.add_argument("--force", action="store_true", help="Regenerate images that already exist")

    def handle(self, *args, **opts):
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            raise CommandError("OPENROUTER_API_KEY is not set. Set it in your environment first.")
        try:
            import requests
        except ImportError:
            raise CommandError("The 'requests' package is required. Run: pip install requests")
        try:
            from PIL import Image
        except ImportError:
            raise CommandError("Pillow is required. Run: pip install pillow")

        out_dir = _output_dir()
        self.stdout.write(f"Saving images to: {out_dir}")

        items = [
            (line["name_en"], color_en)
            for line in LINES
            for color_en, _ in line["colors"]
        ]
        total = len(items)
        done = skipped = failed = 0

        for i, (name_en, color_en) in enumerate(items, 1):
            slug = product_slug(name_en, color_en)
            dest = out_dir / f"{slug}.jpg"
            if dest.exists() and not opts["force"]:
                skipped += 1
                continue

            noun = PROMPT_NOUNS.get(name_en, name_en.lower())
            prompt = (
                f"Professional e-commerce product photograph of {color_en} {noun}. "
                f"The item is clearly {color_en} in color. Neatly presented on a plain soft "
                f"off-white studio background, centered, even soft studio lighting, "
                f"photorealistic, high detail. No people, no mannequin, no text, no watermark."
            )

            ok = False
            for attempt in range(3):
                try:
                    resp = requests.post(
                        OPENROUTER_URL,
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "model": opts["model"],
                            "messages": [{"role": "user", "content": prompt}],
                            "modalities": ["image", "text"],
                        },
                        timeout=120,
                    )
                    resp.raise_for_status()
                    imgs = resp.json()["choices"][0]["message"].get("images") or []
                    if not imgs:
                        raise RuntimeError("no image returned")
                    raw = base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1])
                    img = Image.open(io.BytesIO(raw)).convert("RGB")
                    w = opts["width"]
                    h = int(img.height * (w / img.width))
                    img.resize((w, h), Image.LANCZOS).save(dest, "JPEG", quality=85, optimize=True)
                    done += 1
                    ok = True
                    self.stdout.write(self.style.SUCCESS(f"[{i}/{total}] {slug}.jpg"))
                    break
                except Exception as exc:
                    self.stderr.write(f"[{i}/{total}] try{attempt + 1} failed {slug}: {exc}")
                    time.sleep(3)
            if not ok:
                failed += 1
            time.sleep(0.4)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. generated={done}, skipped(existing)={skipped}, failed={failed}, total={total}"
        ))
        self.stdout.write("Next: commit frontend/public/products/, deploy, then the images appear.")
