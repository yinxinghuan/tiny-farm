#!/usr/bin/env ~/miniconda3/bin/python3
"""
Generate the Tiny Farm poster (1024x1024).
  1. txt2img (cottagecore voxel farm scene, title-safe upper third)
  2. Download
  3. PIL composite the title typography
"""

import json
import os
import ssl
import subprocess
import time
import urllib.request

USER_ID = 618336286
API_URL = "http://aiservice.wdabuliu.com:8019/genl_image"
OUT_DIR = "/Users/yin/code/games/tiny-farm"
RAW_DIR = "/Users/yin/code/games/_poster_raw"
os.makedirs(RAW_DIR, exist_ok=True)

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

PROMPT = (
    "editorial cottagecore voxel art poster, perfect square 1:1 composition, "
    "the upper one-third of the canvas is a clean empty warm peach-cream gradient sky reserved for typography with absolutely no objects, "
    "in the lower two-thirds: one charming tiny low-poly 3D voxel farm island sitting at the center, isometric camera angle, "
    "the small island has tidy rows of golden ripe wheat, two big bright yellow sunflowers, one cozy little cottage with a coral-red triangular roof tiny chimney with a curl of smoke, "
    "two lush blocky round-canopy green trees, a single small white cow with black spots standing on grass, a winding light brown dirt path, "
    "soft fluffy little clouds drifting on the horizon, vibrant saturated colors, golden hour warm sunlight, gentle ground shadow under the island, "
    "blocky minecraft-adjacent low-poly 3D style, dreamy charming inviting, generous empty space around the subject, no text, no letters, no signs"
)


def call_txt2img(prompt: str) -> str:
    payload = {"query": "", "params": {"prompt": prompt, "user_id": USER_ID}}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    print(f"[api] submit ...")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=360, context=SSL_CTX) as r:
        data = json.loads(r.read())
    print(f"[api] {data.get('code')}  ({time.time()-t0:.1f}s)  -> {data.get('url')}")
    if data.get("code") != 200:
        raise RuntimeError(data)
    return data["url"]


def download(url: str, out_path: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    ext = os.path.splitext(url.split("?")[0])[1].lower()
    if ext and ext != ".png":
        tmp = out_path + ext
        with open(tmp, "wb") as f:
            f.write(data)
        subprocess.run(
            ["sips", "-s", "format", "png", tmp, "--out", out_path],
            check=True, capture_output=True,
        )
        os.remove(tmp)
    else:
        with open(out_path, "wb") as f:
            f.write(data)
    return out_path


def composite_title(raw_path: str, out_path: str):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(raw_path).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Fonts — chunky friendly display for title, mono for sub
    display_paths = [
        "/System/Library/Fonts/Supplemental/Futura.ttc",
        "/System/Library/Fonts/Supplemental/AvenirNextCondensed.ttc",
        "/System/Library/Fonts/Avenir.ttc",
        "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Neue.ttc",
    ]
    mono_paths = [
        "/System/Library/Fonts/Supplemental/Andale Mono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Monaco.ttf",
    ]
    display = next((p for p in display_paths if os.path.exists(p)), None)
    mono = next((p for p in mono_paths if os.path.exists(p)), None)

    fpx = 170
    title_font = ImageFont.truetype(display, fpx) if display else ImageFont.load_default()
    sub_font = ImageFont.truetype(mono, 24) if mono else ImageFont.load_default()

    title = "TINY FARM"
    track_em = 0.06
    widths = [draw.textbbox((0, 0), ch, font=title_font)[2] for ch in title]
    total = sum(widths) + (len(title) - 1) * fpx * track_em
    x = (1024 - total) / 2
    y = 70

    # subtle white halo for legibility on warm sky
    halo_color = (255, 248, 230, 70)
    for ox in (-3, 0, 3):
        for oy in (-3, 0, 3):
            if ox == 0 and oy == 0:
                continue
            xx = x
            for i, ch in enumerate(title):
                draw.text((xx + ox, y + oy), ch, fill=halo_color, font=title_font)
                xx += widths[i] + fpx * track_em

    title_color = (52, 36, 22, 250)  # warm dark ink
    xx = x
    for i, ch in enumerate(title):
        draw.text((xx, y), ch, fill=title_color, font=title_font)
        xx += widths[i] + fpx * track_em

    # tagline
    sub = "PLANT  ·  GROW  ·  HARVEST"
    sb = draw.textbbox((0, 0), sub, font=sub_font)
    sx = (1024 - (sb[2] - sb[0])) / 2
    draw.text((sx, y + fpx + 18), sub, fill=(80, 56, 30, 215), font=sub_font)

    final = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    final.save(out_path, "PNG", quality=95)
    print(f"[poster] composited → {out_path}")


def main():
    url = call_txt2img(PROMPT)
    raw_ext = ".webp" if url.endswith(".webp") else ".png"
    raw_path = os.path.join(RAW_DIR, f"tiny_farm_raw{raw_ext}")
    download(url, raw_path)
    print(f"[poster] raw → {raw_path}")
    out_path = os.path.join(OUT_DIR, "cover.png")
    composite_title(raw_path, out_path)
    poster_path = os.path.join(OUT_DIR, "poster.png")
    # Both names: meta.json points to cover.png, games-list expects poster.png
    import shutil
    shutil.copyfile(out_path, poster_path)
    print(f"[poster] copied → {poster_path}")


if __name__ == "__main__":
    main()
