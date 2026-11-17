"""Blender headless: build meshes from Jellyfish.bbmodel, render preview, export FBX.

Run:
  /Applications/Blender.app/Contents/MacOS/Blender -b --python tools/export_blender.py
"""
import json
import math
import os

import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "jellyfish", "Jellyfish.bbmodel")
TEX = os.path.join(ROOT, "jellyfish", "jellyfish_texture.png")
EXPORT = os.path.join(ROOT, "jellyfish", "export")
SCALE = 1 / 16 * 3  # 16 px = 1 block -> 3 Blender units (Roblox studs on import)
os.makedirs(EXPORT, exist_ok=True)

data = json.load(open(SRC))
TW, TH = data["resolution"]["width"], data["resolution"]["height"]

bpy.ops.wm.read_factory_settings(use_empty=True)

img = bpy.data.images.load(TEX)
img.alpha_mode = "NONE"
mat = bpy.data.materials.new("JellyfishMat")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = "Closest"
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.9

# face -> 4 corner indices (Blockbench Y-up space), viewed from outside, CCW
# corners of a cube indexed by bits (x,y,z): idx = x + 2*y + 4*z (0=min, 1=max)
FACES = {
    "north": (1, 0, 2, 3),  # -Z
    "south": (4, 5, 7, 6),  # +Z  -> built below in CCW order
    "east": (1, 5, 7, 3),   # +X
    "west": (0, 2, 6, 4),   # -X
    "up": (2, 3, 7, 6),     # +Y
    "down": (0, 4, 5, 1),   # -Y
}
# fix winding explicitly (outward normals) - verified below via normals recalc
FACES = {
    "north": (1, 0, 2, 3),
    "south": (4, 5, 7, 6),
    "east": (5, 1, 3, 7),
    "west": (0, 4, 6, 2),
    "up": (2, 6, 7, 3),
    "down": (0, 1, 5, 4),
}


def rot_matrix(rot):
    rx, ry, rz = (math.radians(a) for a in rot)
    return (Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(ry, 3, "Y")
            @ Matrix.Rotation(rx, 3, "X"))


def to_blender(v):
    # Blockbench (x, y, z) Y-up  ->  Blender (x, -z, y) Z-up, scaled
    return Vector((v.x * SCALE, -v.z * SCALE, v.y * SCALE))


def build(name, elems):
    verts, faces, uvs = [], [], []
    for el in elems:
        f, t = Vector(el["from"]), Vector(el["to"])
        o = Vector(el["origin"])
        R = rot_matrix(el.get("rotation", (0, 0, 0)))
        corners = []
        for i in range(8):
            p = Vector((t.x if i & 1 else f.x, t.y if i & 2 else f.y, t.z if i & 4 else f.z))
            corners.append(to_blender(o + R @ (p - o)))
        base = len(verts)
        verts += corners
        for fname, idx in FACES.items():
            faces.append([base + i for i in idx])
            u0, v0, u1, v1 = el["faces"][fname]["uv"]
            u0, u1 = u0 / TW, u1 / TW
            v0, v1 = 1 - v0 / TH, 1 - v1 / TH
            uvs.append([(u0, v1), (u1, v1), (u1, v0), (u0, v0)])
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for poly, quad in zip(me.polygons, uvs):
        for li, uvc in zip(poly.loop_indices, quad):
            uv.data[li].uv = uvc
    me.materials.append(mat)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


glow = [e for e in data["elements"] if e["name"].startswith("G_")]
body = [e for e in data["elements"] if not e["name"].startswith("G_")]
objs = {"JellyfishBody": build("JellyfishBody", body),
        "JellyfishGlow": build("JellyfishGlow", glow)}

# make normals point outward
for ob in objs.values():
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.select_set(False)

# ---- FBX export (each mesh separately, origin at model origin) -------------
for name, ob in objs.items():
    for o in objs.values():
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(EXPORT, f"{name}.fbx"), use_selection=True,
        axis_forward="-Z", axis_up="Y", apply_unit_scale=True,
        global_scale=1.0, path_mode="COPY", embed_textures=False,
        mesh_smooth_type="FACE", add_leaf_bones=False)
    print("exported", name, len(ob.data.polygons) // 6, "cubes")

# ---- preview render --------------------------------------------------------
scn = bpy.context.scene
scn.render.engine = "BLENDER_WORKBENCH"
sh = scn.display.shading
sh.light = "STUDIO"
sh.color_type = "TEXTURE"
sh.show_cavity = False
scn.render.resolution_x, scn.render.resolution_y = 900, 900
scn.render.film_transparent = False
scn.world = bpy.data.worlds.new("w")
scn.world.color = (0.80, 0.55, 0.30)  # orange studs-ish backdrop like reference
scn.view_settings.view_transform = "Standard"

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"
cam.data.ortho_scale = 13.5
scn.collection.objects.link(cam)
scn.camera = cam
center = Vector((0, 0, 4.6))


def shoot(az, el, path):
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam.location = center + d * 30
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)


shoot(math.radians(30), math.radians(12), os.path.join(ROOT, "jellyfish", "preview.png"))
shoot(math.radians(120), math.radians(12), os.path.join(ROOT, "jellyfish", "preview_side.png"))
