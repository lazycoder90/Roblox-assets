#!/usr/bin/env python3
"""Generate the blocky jellyfish pet as a Blockbench .bbmodel + pixel texture.

Usage: python3 tools/build_jellyfish.py
Outputs (relative to project root):
  jellyfish/Jellyfish.bbmodel
  jellyfish/jellyfish_texture.png

Conventions
- Units are Blockbench pixels (16 px = 1 block). Y is up. Origin (0,0,0) is the
  centre axis of the bell, so rotating the pet around Y spins it in place.
- Cubes whose name starts with "G_" are "glow" parts (gold). The Blender export
  script splits them into a separate mesh so Roblox Studio can set Neon/lights.
"""
import base64
import json
import math
import os
import struct
import uuid
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "jellyfish")
TEX_W = TEX_H = 64
NS = uuid.UUID("12345678-1234-5678-1234-567812345678")

# ---------------------------------------------------------------- texture ---
# 4 swatches of 8x8 px on the first row: white, shade, gold, bright gold.
SWATCH = {"white": 0, "shade": 8, "gold": 16, "bright": 24}


def make_texture():
    px = [[(0, 0, 0, 0)] * TEX_W for _ in range(TEX_H)]
    base = {
        "white": ((246, 248, 255), (236, 240, 252)),
        "shade": ((226, 236, 250), (214, 228, 246)),
        "gold": ((255, 196, 40), (255, 214, 90)),
        "bright": ((255, 240, 150), (255, 250, 205)),
    }
    for name, x0 in SWATCH.items():
        a, b = base[name]
        for y in range(8):
            for x in range(8):
                c = b if (x + y) % 4 == 0 else a  # light dither = pixel-art feel
                px[y][x0 + x] = (*c, 255)
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in px)

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", TEX_W, TEX_H, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


# ----------------------------------------------------------------- model ----
elements = []


def cube(name, c, s, mat, rot=(0, 0, 0)):
    cx, cy, cz = c
    sx, sy, sz = s
    uid = str(uuid.uuid5(NS, f"{len(elements)}:{name}"))
    x0 = SWATCH[mat]
    face = {"uv": [x0, 0, x0 + 8, 8], "texture": 0}
    el = {
        "name": name,
        "box_uv": False,
        "rescale": False,
        "locked": False,
        "light_emission": 0,
        "render_order": "default",
        "allow_mirror_modeling": True,
        "from": [round(cx - sx / 2, 3), round(cy - sy / 2, 3), round(cz - sz / 2, 3)],
        "to": [round(cx + sx / 2, 3), round(cy + sy / 2, 3), round(cz + sz / 2, 3)],
        "autouv": 0,
        "color": 0,
        "origin": [round(cx, 3), round(cy, 3), round(cz, 3)],
        "faces": {f: dict(face) for f in ("north", "east", "south", "west", "up", "down")},
        "type": "cube",
        "uuid": uid,
    }
    if any(rot):
        el["rotation"] = [round(r, 3) for r in rot]
    elements.append(el)
    return uid


def group(name, origin=(0, 0, 0)):
    return {"name": name, "origin": list(origin), "color": 0,
            "uuid": str(uuid.uuid5(NS, "group:" + name)), "export": True,
            "isOpen": False, "locked": False, "visibility": True,
            "autouv": 0, "children": []}


def star(g, name, c, r=1.7, mat="bright"):
    """Tiny 3-axis sparkle star."""
    cx, cy, cz = c
    t = 0.8
    g["children"] += [
        cube(f"G_{name}_x", (cx, cy, cz), (2 * r, t, t), mat),
        cube(f"G_{name}_y", (cx, cy, cz), (t, 2 * r, t), mat),
        cube(f"G_{name}_z", (cx, cy, cz), (t, t, 2 * r), mat),
    ]


def polar(r, theta, tangent=0.0):
    """x,z from radius/angle (theta in rad, 0 = +Z) plus a sideways offset."""
    return (r * math.sin(theta) + tangent * math.cos(theta),
            r * math.cos(theta) - tangent * math.sin(theta))


# ---- Bell -----------------------------------------------------------------
# (y_bottom, height, width) - each tier is a "plus" of two cuboids = rounded dome
TIERS = [(20, 3, 24), (23, 4, 30), (27, 4, 32), (31, 4, 30),
         (35, 3, 24), (38, 3, 16), (41, 2, 8)]

bell = group("Bell")
trim = group("Gold_Trim")
for i, (y0, h, w) in enumerate(TIERS):
    mat = "white" if i % 2 == 0 else "shade"
    cy = y0 + h / 2
    bell["children"].append(cube(f"bell_{i}_a", (0, cy, 0), (w, h, w - 8), mat))
    bell["children"].append(cube(f"bell_{i}_b", (0, cy, 0), (w - 8, h, w), mat))
    # gold ribs on the four faces
    for d, (dx, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
        off = w / 2 + 0.3
        pos = (dx * off, cy, dz * off)
        size = (2, h, 0.6) if dz else (0.6, h, 2)
        trim["children"].append(cube(f"G_rib_{i}_{d}", pos, size, "gold"))

# gold ring under the rim
for d, (dx, dz) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
    pos = (dx * 12.5, 20.8, dz * 12.5)
    size = (16, 1.6, 1) if dz else (1, 1.6, 16)
    trim["children"].append(cube(f"G_ring_{d}", pos, size, "gold"))
# diamond emblems (front/back/left/right) on the widest tiers
for sgn in (1, -1):
    for xo in (-7.5, 7.5):
        trim["children"].append(cube(f"G_diamond_z{sgn}_{xo}", (xo, 33, sgn * 15.5),
                                     (4, 4, 0.8), "bright", rot=(0, 0, 45)))
    for zo in (-7.5, 7.5):
        trim["children"].append(cube(f"G_diamond_x{sgn}_{zo}", (sgn * 15.5, 33, zo),
                                     (0.8, 4, 4), "bright", rot=(45, 0, 0)))
# big diamond emblem near the top
for d, (dx, dz) in enumerate(((0, 1), (0, -1))):
    trim["children"].append(cube(f"G_topdiamond_{d}", (0, 42.2, dz * 4.4),
                                 (3, 3, 0.8), "bright", rot=(0, 0, 45)))

# ---- Halo -----------------------------------------------------------------
halo = group("Halo")
HALO_Y, HALO_R = 50, 14
for k in range(8):
    th = math.radians(k * 45)
    x, z = polar(HALO_R, th)
    halo["children"].append(cube(f"G_halo_{k}", (x, HALO_Y, z), (11.6, 1.6, 1.6),
                                 "bright", rot=(0, k * 45, 0)))
for k, th in enumerate((0, 90, 180, 270)):
    x, z = polar(HALO_R + 0.6, math.radians(th))
    halo["children"].append(cube(f"G_halocap_{k}", (x, HALO_Y, z), (1.6, 5, 1.6), "gold"))
    star(halo, f"halostar_{k}", (x * 1.0, HALO_Y + 3.5, z * 1.0), r=1.4)

# ---- Tentacles ------------------------------------------------------------
tent_root = group("Tentacles")
sparkles = group("Sparkles")
N_SEG, SEG_STEP = 7, 4.0
for k in range(8):
    th = math.radians(k * 45)
    g = group(f"Tentacle_{k}")
    for i in range(N_SEG):
        w = max(2.0, 4.0 - i * 0.28)
        r = 10 + i * 0.9
        t = math.sin(i * 0.95 + k * 0.8) * 2.8
        x, z = polar(r, th, t)
        cy = 20 - i * SEG_STEP - SEG_STEP / 2 + 0.5
        last = i >= N_SEG - 1
        g["children"].append(cube(f"{'G_' if last else ''}tent_{k}_{i}", (x, cy, z),
                                  (w, SEG_STEP + 0.6, w), "gold" if last else
                                  ("white" if i % 2 == 0 else "shade"),
                                  rot=(0, k * 45, 0)))
        if i == 3 and k % 2 == 0:
            sx, sz = polar(r + w / 2 + 1.6, th, t)
            star(sparkles, f"tent_{k}", (sx, cy, sz))
        if i == 5 and k % 2 == 1:
            sx, sz = polar(r + w / 2 + 1.4, th, t)
            star(sparkles, f"tent_{k}b", (sx, cy, sz), r=1.4)
    tent_root["children"].append(g)

# ---- Oral arms (inner ribbons) -------------------------------------------
arms_root = group("Oral_Arms")
N_ARM = 7
for k in range(4):
    th = math.radians(45 + k * 90)
    g = group(f"Arm_{k}")
    for i in range(N_ARM):
        w = max(2.0, 5.0 - i * 0.4)
        t = math.sin(i * 0.8 + k * 1.7) * 1.5
        x, z = polar(2.5 + i * 0.2, th, t)
        h = 4.6
        cy = 20 - i * 4.2 - h / 2 + 0.5
        g["children"].append(cube(f"arm_{k}_{i}", (x, cy, z), (w, h, 1.6),
                                  "white" if i % 2 == 0 else "shade",
                                  rot=(0, 45 + k * 90, 0)))
        if i % 2 == 0:
            g["children"].append(cube(f"G_armstripe_{k}_{i}", (x, cy, z),
                                      (1, h, 1.9), "gold", rot=(0, 45 + k * 90, 0)))
    arms_root["children"].append(g)

outliner = [bell, trim, halo, tent_root, arms_root, sparkles]

# ----------------------------------------------------------------- write ----
tex_png = make_texture()
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "jellyfish_texture.png"), "wb") as f:
    f.write(tex_png)

bbmodel = {
    "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
    "name": "Jellyfish",
    "model_identifier": "",
    "visible_box": [1, 1, 0],
    "variable_placeholders": "",
    "variable_placeholder_buttons": [],
    "timeline_setups": [],
    "unhandled_root_fields": {},
    "resolution": {"width": TEX_W, "height": TEX_H},
    "elements": elements,
    "outliner": outliner,
    "textures": [{
        "path": "", "name": "jellyfish_texture.png", "folder": "", "namespace": "",
        "id": "0", "width": TEX_W, "height": TEX_H, "uv_width": TEX_W, "uv_height": TEX_H,
        "particle": False, "use_as_default": False, "layers_enabled": False,
        "sync_to_project": "", "render_mode": "default", "render_sides": "auto",
        "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
        "frame_interpolate": False, "visible": True, "internal": True, "saved": True,
        "uuid": str(uuid.uuid5(NS, "texture")),
        "source": "data:image/png;base64," + base64.b64encode(tex_png).decode(),
    }],
}
with open(os.path.join(OUT, "Jellyfish.bbmodel"), "w") as f:
    json.dump(bbmodel, f, indent=1)

glow = sum(1 for e in elements if e["name"].startswith("G_"))
print(f"cubes: {len(elements)} (glow {glow}, body {len(elements) - glow})")
print("wrote", os.path.join(OUT, "Jellyfish.bbmodel"))
