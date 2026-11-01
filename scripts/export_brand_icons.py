"""Exporta el emblema de static/images/logo-mark.svg a iconos de plataforma.

Uso: .venv/bin/python scripts/export_brand_icons.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
NAVY = (2, 22, 127, 255)
WHITE = (255, 255, 255, 255)
GOLD = (255, 208, 20, 255)
MASTER = 1024
RESAMPLE = Image.Resampling.LANCZOS


def mark(size: int, *, inset: float = 0, opaque: bool = True) -> Image.Image:
    """Dibuja la fortaleza y el libro, con margen para iconos adaptables."""
    canvas = Image.new('RGBA', (MASTER, MASTER), NAVY if opaque else (0, 0, 0, 0))
    scale = 1 - 2 * inset

    def point(x: float, y: float) -> tuple[int, int]:
        return (round((inset + x / 64 * scale) * MASTER), round((inset + y / 64 * scale) * MASTER))

    def width(value: float) -> int:
        return round(value / 64 * scale * MASTER)

    def stroke(points: list[tuple[float, float]], color: tuple[int, ...], weight: float) -> None:
        coords = [point(x, y) for x, y in points]
        w = width(weight)
        draw.line(coords, fill=color, width=w, joint='curve')
        r = w / 2
        for x, y in (coords[0], coords[-1]):
            draw.ellipse((round(x-r), round(y-r), round(x+r), round(y+r)), fill=color)

    # El SVG y el PNG comparten las mismas coordenadas en una retícula de 64.
    mask = Image.new('L', (MASTER, MASTER), 0)
    ImageDraw.Draw(mask).rounded_rectangle((*point(1, 1), *point(63, 63)), radius=width(14), fill=255)
    gradient = Image.new('RGBA', (MASTER, MASTER))
    gradient_draw = ImageDraw.Draw(gradient)
    for y in range(MASTER):
        t = y / MASTER
        gradient_draw.line((0, y, MASTER, y), fill=(
            round(6 * (1-t) + t), round(51 * (1-t) + 14*t), round(151 * (1-t) + 85*t), 255,
        ))
    canvas.paste(gradient, (0, 0), mask)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((*point(3.5, 3.5), *point(60.5, 60.5)), radius=width(12), outline=GOLD, width=width(.8))

    side = [(14, 37), (14, 22), (16.5, 22), (16.5, 17.5), (19.5, 17.5),
            (19.5, 22), (22, 22), (22, 17.5), (24.5, 17.5), (24.5, 37)]
    stroke(side, GOLD, 2.2)
    stroke([(64-x, y) for x, y in side], GOLD, 2.2)
    stroke([(26, 37), (26, 18), (28, 18), (28, 13), (30, 13), (30, 18),
            (34, 18), (34, 13), (36, 13), (36, 18), (38, 18), (38, 37)], GOLD, 2.4)
    stroke([(13, 38), (51, 38)], GOLD, 1.6)
    for x in (17, 21, 43, 47):
        stroke([(x, 27), (x, 34)], WHITE, 1.4)
    stroke([(29.5, 36), (29.5, 29), (32, 26), (34.5, 29), (34.5, 36)], WHITE, 1.9)

    def bezier(start, control1, control2, end):
        return [
            (
                (1-t)**3 * start[0] + 3*(1-t)**2*t * control1[0] + 3*(1-t)*t*t * control2[0] + t**3 * end[0],
                (1-t)**3 * start[1] + 3*(1-t)**2*t * control1[1] + 3*(1-t)*t*t * control2[1] + t**3 * end[1],
            )
            for t in (i / 20 for i in range(21))
        ]

    left_page = bezier((31.3, 44), (26, 40.5), (19, 40.4), (12, 42.5)) + [(12, 51)]
    left_page += bezier((12, 51), (19, 49), (25, 50), (31.3, 54))
    right_page = [(64-x, y) for x, y in left_page]
    draw.polygon([point(*p) for p in left_page], fill=WHITE)
    draw.polygon([point(*p) for p in right_page], fill=WHITE)
    stroke([(16, 45), (24, 45), (29, 47)], GOLD, .7)
    stroke([(48, 45), (40, 45), (35, 47)], GOLD, .7)
    stroke([(32, 44), (32, 54)], GOLD, 2.1)
    image = canvas.resize((size, size), RESAMPLE)
    return image.convert('RGB') if opaque else image


def write(path: Path, size: int, **kwargs: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mark(size, **kwargs).save(path, optimize=True)


def main() -> None:
    write(ROOT / 'static/images/favicon-32.png', 32)
    write(ROOT / 'static/images/apple-touch-icon.png', 180)
    write(ROOT / 'MOVIL/assets/icon/icon.png', 1024)
    write(ROOT / 'MOVIL/assets/icon/icon_foreground.png', 1024, inset=.19, opaque=False)

    android = ROOT / 'MOVIL/android/app/src/main/res'
    densities = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}
    for density, factor in densities.items():
        write(android / f'mipmap-{density}/ic_launcher.png', round(48 * factor))
        write(android / f'drawable-{density}/ic_launcher_foreground.png', round(108 * factor), inset=.19, opaque=False)

    ios = ROOT / 'MOVIL/ios/Runner/Assets.xcassets/AppIcon.appiconset'
    contents = json.loads((ios / 'Contents.json').read_text())
    for item in contents['images']:
        dimension = float(item['size'].split('x')[0]) * float(item['scale'].removesuffix('x'))
        write(ios / item['filename'], round(dimension))

    web = ROOT / 'MOVIL/web'
    write(web / 'favicon.png', 32)
    for size in (192, 512):
        write(web / f'icons/Icon-{size}.png', size)
        write(web / f'icons/Icon-maskable-{size}.png', size, inset=.12)


if __name__ == '__main__':
    main()
