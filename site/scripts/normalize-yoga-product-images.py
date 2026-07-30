#!/usr/bin/env python3
"""Create centered, consistent display derivatives without touching originals.

The source product photos are supplied as square JPGs, but the photographed
object is not consistently centered inside those squares. This script isolates
the non-white foreground, scales it to a common visual footprint, aligns its
base, and places it on a warm-white square canvas for the storefront.

Requires Pillow in the local image-processing environment. The generated WebP
files are runtime assets; the original JPGs remain the source of truth.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "public/yoga-verde/assets/products"
OUTPUT_DIR = SOURCE_DIR / "display"
CANVAS_SIZE = 1200
TARGET_FOREGROUND = 1000
CANVAS_BACKGROUND = (250, 248, 244, 255)


def foreground_mask(image: Image.Image) -> Image.Image:
    """Return a soft alpha mask for the photographed object, not paper grain."""

    rgb = image.convert("RGB")
    # A generic difference-from-white threshold included subtle JPG noise over
    # the whole canvas in a few photos. Use the same dark/saturated foreground
    # rule as the visual audit instead, so the crop follows the actual bottle,
    # jar, label or candle rather than the white backdrop.
    mask = Image.new("L", rgb.size)
    mask.putdata(
        [
            255 if min(red, green, blue) < 232 or max(red, green, blue) - min(red, green, blue) > 18 else 0
            for red, green, blue in rgb.getdata()
        ]
    )
    return mask


def largest_component_bbox(mask: Image.Image) -> tuple[int, int, int, int]:
    """Ignore isolated JPG specks that would otherwise expand the crop."""

    reduced_size = 300
    reduced = mask.resize((reduced_size, reduced_size), Image.Resampling.BOX)
    pixels = [value > 128 for value in reduced.getdata()]
    visited = bytearray(len(pixels))
    best = (0, 0, 0, 0, 0)

    for start, enabled in enumerate(pixels):
        if not enabled or visited[start]:
            continue
        queue = deque([start])
        visited[start] = 1
        area = 0
        min_x = max_x = start % reduced_size
        min_y = max_y = start // reduced_size

        while queue:
            current = queue.popleft()
            x = current % reduced_size
            y = current // reduced_size
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

            for neighbor in (current - 1, current + 1, current - reduced_size, current + reduced_size):
                if neighbor < 0 or neighbor >= len(pixels) or visited[neighbor]:
                    continue
                neighbor_x = neighbor % reduced_size
                if abs(neighbor_x - x) > 1 or not pixels[neighbor]:
                    continue
                visited[neighbor] = 1
                queue.append(neighbor)

        if area > best[0]:
            best = (area, min_x, min_y, max_x + 1, max_y + 1)

    if best[0] == 0:
        raise RuntimeError("No connected foreground component found")

    _, left, top, right, bottom = best
    scale_x = mask.width / reduced_size
    scale_y = mask.height / reduced_size
    return (
        round(left * scale_x),
        round(top * scale_y),
        round(right * scale_x),
        round(bottom * scale_y),
    )


def normalize(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGBA")
    mask = foreground_mask(image)
    bbox = largest_component_bbox(mask)

    left, top, right, bottom = bbox
    padding_x = max(12, int((right - left) * 0.08))
    padding_y = max(12, int((bottom - top) * 0.08))
    left = max(0, left - padding_x)
    top = max(0, top - padding_y)
    right = min(image.width, right + padding_x)
    bottom = min(image.height, bottom + padding_y)

    cropped = image.crop((left, top, right, bottom))
    cropped.putalpha(mask.crop((left, top, right, bottom)).filter(ImageFilter.GaussianBlur(radius=0.8)))

    scale = TARGET_FOREGROUND / max(cropped.width, cropped.height)
    resized = cropped.resize(
        (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), CANVAS_BACKGROUND)
    x = (CANVAS_SIZE - resized.width) // 2
    y = CANVAS_SIZE - resized.height - 70
    canvas.alpha_composite(resized, (x, max(40, y)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(destination, "WEBP", quality=94, method=6)


def main() -> None:
    sources = sorted(SOURCE_DIR.glob("*.jpg"))
    if not sources:
        raise SystemExit(f"No JPG product sources found in {SOURCE_DIR}")

    for source in sources:
        destination = OUTPUT_DIR / f"{source.stem}.webp"
        normalize(source, destination)
        print(f"{source.name} -> {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
