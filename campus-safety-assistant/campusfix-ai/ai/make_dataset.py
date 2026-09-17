"""Generates a simulated camera-capture dataset: `ai/dataset/` + manifest.json.

24 images: 3 per hazard category + clean/irrelevant/blurry negatives.
Deterministic (seeded) so judges get identical files every run.
Descriptions/locations mirror real reporter phrasing.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
OUT = HERE / "dataset"
W, H = 640, 480


def grain(img: Image.Image, amt: int = 14, rng: random.Random | None = None) -> Image.Image:
    rng = rng or random
    px = img.load()
    for x in range(0, W, 2):
        for y in range(0, H, 2):
            n = rng.randint(-amt, amt)
            r, g, b = img.getpixel((x, y))
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    return img


def wire(draw: ImageDraw.ImageDraw, x0, y0, x1, y1, color=(255, 170, 30), width=6):
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2 + 40
    draw.line([(x0, y0), (mx, my), (x1, y1)], fill=color, width=width, joint="curve")


def scene_electrical(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (28, 28, 34))
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, 580, 420], outline=(70, 70, 80), width=4)
    for i in range(3):
        wire(d, 80, 120 + i * 70, 420, 140 + i * 70,
             color=rng.choice([(255, 170, 30), (255, 60, 40), (250, 220, 90)]))
    sx, sy = 450, 200  # socket
    d.rectangle([sx, sy, sx + 90, sy + 130], fill=(225, 225, 225), outline=(150, 150, 150), width=3)
    d.rectangle([sx + 25, sy + 35, sx + 35, sy + 75], fill=(20, 20, 20))
    d.rectangle([sx + 55, sy + 35, sx + 65, sy + 75], fill=(20, 20, 20))
    for _ in range(8):  # spark flecks
        x, y = rng.randint(sx - 30, sx + 120), rng.randint(sy - 30, sy + 160)
        d.ellipse([x, y, x + 5, y + 5], fill=(255, 240, 160))
    return grain(img, rng=rng)


def scene_plumbing(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (214, 232, 240))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 70], fill=(190, 205, 215))  # ceiling strip
    for _ in range(7):
        x = rng.randint(60, 580)
        d.line([(x, 70), (x + rng.randint(-15, 15), rng.randint(250, 420))],
               fill=(40, 120, 200), width=rng.randint(4, 9))
        d.ellipse([x - 6, 400, x + 6, 416], fill=(40, 120, 200))
    d.ellipse([120, 400, 520, 465], fill=(70, 150, 215))  # puddle
    d.ellipse([180, 415, 460, 450], fill=(120, 185, 230))
    return grain(img, amt=8, rng=rng)


def scene_waste(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (96, 140, 82))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 330, W, H], fill=(74, 110, 64))
    for i, bx in enumerate((120, 300)):
        tilt = rng.randint(-12, 12)
        d.rectangle([bx, 210 + tilt, bx + 110, 340], fill=(34, 52, 40),
                    outline=(20, 30, 24), width=4)
        d.rectangle([bx - 8, 195 + tilt, bx + 118, 215 + tilt], fill=(22, 36, 28))
    for _ in range(60):  # scattered litter
        x, y = rng.randint(20, 620), rng.randint(300, 465)
        d.ellipse([x, y, x + rng.randint(4, 12), y + rng.randint(3, 8)],
                  fill=rng.choice([(200, 190, 170), (160, 60, 50), (220, 220, 220), (120, 100, 70)]))
    return grain(img, rng=rng)


def scene_infrastructure(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (206, 188, 160))
    d = ImageDraw.Draw(img)
    x, y = 120, 40
    pts = [(x, y)]
    for _ in range(9):
        x += rng.randint(20, 60)
        y += rng.randint(25, 55)
        pts.append((x, y))
    d.line(pts, fill=(60, 45, 35), width=7, joint="curve")
    for _ in range(3):  # peeled patches
        px, py = rng.randint(80, 450), rng.randint(80, 350)
        d.rectangle([px, py, px + 90, py + 60], fill=(150, 128, 100), outline=(90, 70, 55), width=3)
    d.rectangle([0, 420, W, H], fill=(150, 130, 105))
    return grain(img, rng=rng)


def scene_furniture(rng: random.Random, broken: bool = True) -> Image.Image:
    img = Image.new("RGB", (W, H), (176, 150, 120))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 300], fill=(215, 205, 190))
    d.rectangle([140, 300, 500, 330], fill=(120, 80, 50))  # table top
    for lx in (160, 460):
        d.rectangle([lx, 330, lx + 25, 450], fill=(110, 72, 45))
    cx, cy = 90, 330  # chair (tilted if broken)
    d.rectangle([cx, cy - 110, cx + 70, cy - 95], fill=(95, 62, 40))
    if broken:
        d.polygon([(cx + 10, cy - 95), (cx + 110, cy + 40), (cx + 85, cy + 50), (cx - 5, cy - 90)],
                  fill=(95, 62, 40))
        d.line([(cx + 40, cy - 60), (cx + 130, cy + 30)], fill=(60, 38, 25), width=5)
    else:
        d.rectangle([cx, cy - 95, cx + 70, cy + 30], fill=(95, 62, 40))
    return grain(img, rng=rng)


def scene_road(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (128, 128, 132))
    d = ImageDraw.Draw(img)
    for i in range(6):  # lane dashes
        d.rectangle([300, 20 + i * 80, 340, 60 + i * 80], fill=(230, 230, 220))
    for _ in range(3):
        px, py = rng.randint(80, 500), rng.randint(80, 380)
        d.ellipse([px, py, px + rng.randint(90, 150), py + rng.randint(55, 85)], fill=(45, 45, 48))
        d.ellipse([px + 15, py + 12, px + 100, py + 60], fill=(30, 30, 33))
    return grain(img, amt=18, rng=rng)


def scene_clean(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (232, 228, 220))
    d = ImageDraw.Draw(img)
    d.rectangle([150, 80, 490, 220], fill=(52, 110, 80), outline=(120, 90, 60), width=6)  # board
    for row in range(2):
        for col in range(4):
            x, y = 90 + col * 130, 300 + row * 80
            d.rectangle([x, y, x + 90, y + 18], fill=(140, 100, 70))
            d.rectangle([x + 8, y + 18, x + 20, y + 60], fill=(120, 85, 60))
            d.rectangle([x + 62, y + 18, x + 74, y + 60], fill=(120, 85, 60))
    return grain(img, amt=6, rng=rng)


def scene_irrelevant(rng: random.Random) -> Image.Image:
    img = Image.new("RGB", (W, H), (250, 200, 170))
    d = ImageDraw.Draw(img)
    for y in range(H):  # sunset gradient
        d.line([(0, y), (W, y)], fill=(250 - y // 6, 190 - y // 8, 160 - y // 10))
    d.ellipse([220, 60, 420, 260], fill=(255, 220, 190))  # sun
    d.rectangle([0, 360, W, H], fill=(90, 60, 80))
    return grain(img, amt=6, rng=rng)


# file, scene fn, description, location, expected category/severity
PLAN = [
    ("electrical_1.jpg", scene_electrical, "Exposed electrical wire hanging from wall socket, sparking", "Lab 304", "Electrical", "CRITICAL"),
    ("electrical_2.jpg", scene_electrical, "Switch board making crackling noise with burning smell", "Hostel Block C, floor 2", "Electrical", "CRITICAL"),
    ("electrical_3.jpg", scene_electrical, "Fuse box with open panel cover, wires visible inside", "Electrical room, Block A", "Electrical", "HIGH"),
    ("plumbing_1.jpg", scene_plumbing, "Water leaking beside power outlet in electrical lab", "Electrical Lab, Block A", "Plumbing", "HIGH"),
    ("plumbing_2.jpg", scene_plumbing, "Tap broken in bathroom, water flowing continuously and flooding floor", "Hostel Block B bathroom", "Plumbing", "HIGH"),
    ("plumbing_3.jpg", scene_plumbing, "Ceiling dripping above computer room, getting worse", "Block B computer room", "Plumbing", "HIGH"),
    ("waste_1.jpg", scene_waste, "Overflowing dustbins with garbage scattered all around", "Canteen back gate", "Waste", "MEDIUM"),
    ("waste_2.jpg", scene_waste, "Food waste dumped behind hostel creating bad smell", "Hostel Block D", "Waste", "MEDIUM"),
    ("waste_3.jpg", scene_waste, "Litter strewn across playground after event", "Playground", "Waste", "LOW"),
    ("infra_1.jpg", scene_infrastructure, "Large crack in classroom wall with plaster peeling off", "Room 203", "Infrastructure", "MEDIUM"),
    ("infra_2.jpg", scene_infrastructure, "Portion of ceiling plaster fell in corridor", "First floor corridor, Block C", "Infrastructure", "HIGH"),
    ("infra_3.jpg", scene_infrastructure, "Window glass broken with sharp shards exposed", "Lab 201", "Infrastructure", "HIGH"),
    ("furniture_1.jpg", scene_furniture, "Broken chair with one leg snapped in classroom", "Room 110", "Furniture", "MEDIUM"),
    ("furniture_2.jpg", scene_furniture, "Bench collapsed in canteen seating area", "Canteen", "Furniture", "MEDIUM"),
    ("furniture_3.jpg", scene_furniture, "Cupboard door hanging loose, may fall on students", "Lab 102", "Furniture", "HIGH"),
    ("road_1.jpg", scene_road, "Deep pothole in the middle of campus main road", "Main gate road", "RoadPavement", "HIGH"),
    ("road_2.jpg", scene_road, "Footpath tiles broken and uneven near library", "Library pathway", "RoadPavement", "MEDIUM"),
    ("road_3.jpg", scene_road, "Open manhole without cover on walkway", "Hostel walkway", "RoadPavement", "CRITICAL"),
    ("clean_1.jpg", scene_clean, "Clean classroom, everything looks normal", "Room 201", "OtherUnknown", "MEDIUM"),
    ("clean_2.jpg", scene_clean, "Auditorium clean after event, chairs stacked fine", "Auditorium", "OtherUnknown", "MEDIUM"),
    ("irrelevant_1.jpg", scene_irrelevant, "Just a selfie with friends at sunset", "Main corridor", "OtherUnknown", "MEDIUM"),
    ("blurry_1.jpg", None, "Water leaking beside power outlet in electrical lab", "Electrical Lab, Block A", "Plumbing", "HIGH"),
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    rng = random.Random(7)
    manifest = []
    for fname, fn, desc, loc, cat, sev in PLAN:
        if fname == "blurry_1.jpg":
            img = scene_plumbing(random.Random(21)).filter(ImageFilter.GaussianBlur(6))
        else:
            img = fn(rng)
        img.save(OUT / fname, quality=88)
        manifest.append({"file": fname, "description": desc, "location": loc,
                         "expected_category": cat, "expected_severity": sev})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"Wrote {len(manifest)} images -> {OUT} (+ manifest.json)")


if __name__ == "__main__":
    main()
