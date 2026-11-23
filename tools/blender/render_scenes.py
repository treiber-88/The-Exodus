"""Runs inside Blender. Renders one landscape per route stop to OUT_DIR."""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector, noise

W, H = 320, 136
SCENE = "EXODUS_ART"

# sky top, sky horizon, far, mid, near, extras
SAND = (0.80, 0.58, 0.30)
ROCK = (0.46, 0.27, 0.18)
DUSK = (0.34, 0.20, 0.34)
DAY = ((0.10, 0.30, 0.72), (0.72, 0.84, 0.92))
HOT = ((0.28, 0.46, 0.80), (0.96, 0.84, 0.58))
EVE = ((0.20, 0.12, 0.42), (0.96, 0.52, 0.26))
SCENES = {
    "rameses": (EVE, DUSK, ROCK, SAND, ["pyramids", "city"]),
    "succoth": (DAY, ROCK, SAND, SAND, ["tents"]),
    "etham": (HOT, ROCK, SAND, SAND, []),
    "pi_hahiroth": (EVE, DUSK, ROCK, SAND, ["sea", "tents"]),
    "red_sea": (DAY, DUSK, ROCK, SAND, ["sea"]),
    "marah": (HOT, ROCK, ROCK, SAND, ["pool"]),
    "elim": (DAY, ROCK, SAND, SAND, ["pool", "palms"]),
    "wilderness_of_sin": (HOT, SAND, SAND, SAND, []),
    "rephidim": (HOT, ROCK, ROCK, SAND, ["crag"]),
    "mount_sinai": (EVE, DUSK, ROCK, ROCK, ["sinai", "tents"]),
    "taberah": (EVE, DUSK, ROCK, SAND, ["tents"]),
    "kibroth_hattaavah": (DAY, ROCK, SAND, SAND, ["tents"]),
    "hazeroth": (HOT, ROCK, SAND, SAND, ["palms"]),
    "kadesh": (DAY, DUSK, ROCK, SAND, ["pool", "palms", "tents"]),
    "mount_hor": (EVE, DUSK, ROCK, ROCK, ["sinai"]),
    "hormah": (HOT, ROCK, ROCK, SAND, ["city"]),
    "brook_zered": (DAY, ROCK, ROCK, SAND, ["river"]),
    "river_arnon": (HOT, DUSK, ROCK, SAND, ["river"]),
    "plains_of_moab": (DAY, DUSK, SAND, (0.50, 0.56, 0.26), ["tents", "palms"]),
    "mount_nebo": (EVE, DUSK, (0.36, 0.42, 0.24), ROCK, ["crag"]),
}


def material(rgb, emit=False):
    key = "exo_%s_%.2f_%.2f_%.2f" % ("e" if emit else "d", *rgb)
    m = bpy.data.materials.get(key)
    if m:
        return m
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    lin = linear(rgb)
    b.inputs["Base Color"].default_value = (0, 0, 0, 1) if emit else (*lin, 1)
    b.inputs["Roughness"].default_value = 1
    b.inputs["Specular IOR Level"].default_value = 0
    if emit:
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = 1
    return m


def linear(rgb):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb)


def mountain(scn, x0, y0, radius, height, seed, rgb):
    bm = bmesh.new()
    n = 48
    grid = []
    for j in range(n):
        row = []
        for i in range(n):
            x = -radius + 2 * radius * i / (n - 1)
            y = -radius + 2 * radius * j / (n - 1)
            falloff = max(0.0, 1 - math.hypot(x, y) / radius)
            rough = noise.fractal(Vector((x * .35 + seed, y * .35, seed)), 1.0, 2.0, 4)
            z = height * falloff ** 1.25 * (1 + .42 * rough) - .4
            row.append(bm.verts.new((x0 + x, y0 + y, z)))
        grid.append(row)
    for j in range(n - 1):
        for i in range(n - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    link(scn, "mountain", bm, material(rgb))


def link(scn, name, bm, mat, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    o.location, o.rotation_euler, o.scale = loc, rot, scale
    scn.collection.objects.link(o)
    return o


GROUND = []


def ground(x, y):
    """Height of the terrain at x, y, so objects can sit on it."""
    best = 0.0
    for y0, y1, base, amp, freq, seed in GROUND:
        if y0 <= y <= y1:
            best = surface(x, y, y0, y1, base, amp, freq, seed)
    return best


BASIN = []  # (centre x, centre y, radius x, radius y) of a carved pond
BASIN_FLOOR = -.6
POOL_LEVEL = -.25


def surface(x, y, y0, y1, base, amp, freq, seed):
    t = (y - y0) / (y1 - y0)
    n = noise.fractal(Vector((x * freq + seed, y * freq, seed)), 1.0, 2.0, 4)
    h = base + amp * n * (0.35 + t)
    for cx, cy, rx, ry in BASIN:
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        if d < 1:
            k = 1 - d
            k = k * k * (3 - 2 * k)
            h = h * (1 - k) + BASIN_FLOOR * k
    return h


def footing(x, y, w, d):
    """Lowest ground under a footprint, so no corner hangs in the air."""
    return min(ground(x + a, y + b) for a in (-w, w) for b in (-d, d)) - .04


def terrain(scn, y0, y1, base, amp, freq, seed, rgb):
    GROUND.append((y0, y1, base, amp, freq, seed))
    bm = bmesh.new()
    nx, ny = 240, 40
    rows = []
    for j in range(ny):
        t = j / (ny - 1)
        y = y0 + (y1 - y0) * t
        row = []
        for i in range(nx):
            x = -60 + 120 * i / (nx - 1)
            row.append(bm.verts.new((x, y, surface(x, y, y0, y1, base, amp, freq, seed))))
        rows.append(row)
    for j in range(ny - 1):
        for i in range(nx - 1):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    # A curtain below the front edge, so no sky shows between ridge layers.
    skirt = [bm.verts.new((v.co.x, v.co.y, -4)) for v in rows[0]]
    for i in range(nx - 1):
        bm.faces.new((skirt[i], skirt[i + 1], rows[0][i + 1], rows[0][i]))
    link(scn, "terrain", bm, material(rgb))


def cone(scn, loc, r, h, rgb, segs=4, rot=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=0.02, depth=h)
    link(scn, "cone", bm, material(rgb), (loc[0], loc[1], loc[2] + h / 2), (0, 0, rot))


def box(scn, loc, size, rgb):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    return link(scn, "box", bm, material(rgb), loc, scale=size)


def water(scn, y0, y1, z=0.05):
    bm = bmesh.new()
    a = bm.verts.new((-60, y0, z)); b = bm.verts.new((60, y0, z))
    c = bm.verts.new((60, y1, z)); d = bm.verts.new((-60, y1, z))
    bm.faces.new((a, b, c, d))
    link(scn, "water", bm, material((0.10, 0.34, 0.66), emit=True)).visible_shadow = False
    r = random.Random(4)
    for _ in range(26):
        x, y = r.uniform(-16, 16), r.uniform(y0, y1)
        box(scn, (x, y, z + 0.02), (r.uniform(.5, 1.6), .06, .01), (0.5, 0.78, 0.9))


def palm(scn, x, y):
    z = footing(x, y, .07, .07)
    box(scn, (x, y, z + 1.0), (.14, .14, 2.0), (0.30, 0.18, 0.08))
    for k in range(7):
        a = k / 7 * math.tau
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        link(scn, "frond", bm, material((0.16, 0.42, 0.14)),
             (x + math.cos(a) * .55, y + math.sin(a) * .25, z + 2.0 - .12),
             (0, .45 * (1 if math.cos(a) > 0 else -1), a * 0), (1.1, .22, .07))


def tent(scn, x, y, rgb, yaw=0.0):
    bm = bmesh.new()
    w, d, h = .62, .52, .86
    v = [bm.verts.new(p) for p in ((-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0), (-w, 0, h), (w, 0, h))]
    for f in ((v[0], v[1], v[5], v[4]), (v[2], v[3], v[4], v[5]), (v[1], v[2], v[5]), (v[3], v[0], v[4])):
        bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    z = footing(x, y, w, d)
    link(scn, "tent", bm, material(rgb), (x, y, z), (0, 0, yaw))
    # Dark doorway on the gable end that faces the viewer's side.
    side = -1 if math.sin(yaw) >= 0 else 1
    ex, ey = side * (w + .012) * math.cos(yaw), side * (w + .012) * math.sin(yaw)
    door = box(scn, (x + ex, y + ey, z + .2), (.012, .2, .4), (0.08, 0.06, 0.08))
    door.rotation_euler = (0, 0, yaw)


def extras(scn, names):
    r = random.Random(11)
    if "sea" in names:
        water(scn, -1, 14)
    if "river" in names:
        water(scn, 0.5, 4)
    if "pool" in names:
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=1)
        # Sits below the natural ground inside the carved basin, so the
        # terrain itself forms the shoreline.
        link(scn, "pool", bm, material((0.12, 0.42, 0.72), emit=True),
             (2.5, 1, POOL_LEVEL), scale=(4.0, 1.7, 1)).visible_shadow = False
    if "pyramids" in names:
        for x, y, s in ((-9, 20, 3.0), (-4.5, 22, 4.2), (8, 21, 2.6)):
            cone(scn, (x, y, -.2), s, s * .95, (0.86, 0.66, 0.36), 4, math.pi / 4)
    if "city" in names:
        for _ in range(12):
            x, y = r.uniform(-14, 14), r.uniform(9, 12)
            h = r.uniform(.8, 2.2)
            w = r.uniform(1, 2)
            z = footing(x, y, w / 2, .5)
            box(scn, (x, y, z + h / 2), (w, 1, h), (0.78, 0.62, 0.42))
    if "sinai" in names:
        mountain(scn, 1, 25, 15, 11, 3.7, (0.42, 0.27, 0.23))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
        link(scn, "cloud", bm, material((0.86, 0.84, 0.82), emit=True), (1, 23, 10.5), scale=(4.5, 2, .9))
    if "crag" in names:
        for x, rad, h in ((-11, 6, 5), (-5, 4, 3), (9, 7, 6), (14, 4, 3.4)):
            mountain(scn, x, 13, rad, h, x * .37 + 2, ROCK)
    if "palms" in names:
        for x, y in ((-5.5, 2), (-3.5, 3.5), (5.8, 3), (7.2, 1.6), (-7, 4)):
            palm(scn, x, y)
    if "tents" in names:
        colors = [(.34, .24, .20), (.48, .34, .24), (.62, .24, .18), (.72, .60, .42), (.26, .20, .22)]
        y_min, y_max = (-4.2, -1.7) if "sea" in names else (-1.5, 7.5)
        placed = []
        for _ in range(600):
            if len(placed) >= 14:
                break
            y = r.uniform(y_min, y_max)
            # Keep tents inside the camera's view at this distance.
            half_view = .52 * (y + 10) - .7
            x = r.uniform(-half_view, half_view)
            if "pool" in names and ((x - 2.5) / 4.8) ** 2 + ((y - 1) / 2.5) ** 2 < 1:
                continue
            if any(math.hypot(x - a, y - b) < 1.55 for a, b in placed):
                continue
            placed.append((x, y))
        # Draw far to near so the camp reads with depth.
        for x, y in sorted(placed, key=lambda p: -p[1]):
            tent(scn, x, y, r.choice(colors), r.uniform(.45, 1.05) * r.choice((-1, 1)))


def sky(scn, top, horizon):
    w = bpy.data.worlds.get("exo_sky") or bpy.data.worlds.new("exo_sky")
    w.use_nodes = True
    t = w.node_tree
    t.nodes.clear()
    tc = t.nodes.new("ShaderNodeTexCoord")
    sep = t.nodes.new("ShaderNodeSeparateXYZ")
    ramp = t.nodes.new("ShaderNodeValToRGB")
    bg = t.nodes.new("ShaderNodeBackground")
    ambient = t.nodes.new("ShaderNodeBackground")
    path = t.nodes.new("ShaderNodeLightPath")
    mix = t.nodes.new("ShaderNodeMixShader")
    out = t.nodes.new("ShaderNodeOutputWorld")
    t.links.new(tc.outputs["Generated"], sep.inputs[0])
    t.links.new(sep.outputs["Z"], ramp.inputs[0])
    t.links.new(ramp.outputs[0], bg.inputs[0])
    ambient.inputs[0].default_value = (1.0, 0.86, 0.68, 1)
    ambient.inputs[1].default_value = 0.42
    t.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    t.links.new(ambient.outputs[0], mix.inputs[1])
    t.links.new(bg.outputs[0], mix.inputs[2])
    t.links.new(mix.outputs[0], out.inputs[0])
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*linear(horizon), 1)
    ramp.color_ramp.elements[1].position = 0.28
    ramp.color_ramp.elements[1].color = (*linear(top), 1)
    scn.world = w


def build(name, cfg):
    (top, horizon), far, mid, near, names = cfg
    scn = bpy.data.scenes.get(SCENE) or bpy.data.scenes.new(SCENE)
    for o in list(scn.collection.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    seed = sum(map(ord, name))
    GROUND.clear()
    BASIN[:] = [(2.5, 1, 4.2, 1.9)] if "pool" in names else []
    sky(scn, top, horizon)
    terrain(scn, 26, 42, 1.0, 7.0, .09, seed, far)
    terrain(scn, 12, 26, .3, 3.0, .15, seed + 5, mid)
    if "sea" in names:
        terrain(scn, -9, -1, 0.12, .35, .22, seed + 9, near)
    elif "river" in names:
        terrain(scn, -9, .5, 0.12, .35, .22, seed + 9, near)
        terrain(scn, 4, 13, 0.12, .35, .22, seed + 10, near)
    else:
        terrain(scn, -9, 13, 0, .55, .22, seed + 9, near)
    extras(scn, names)

    cam_data = bpy.data.cameras.new("exo_cam")
    cam_data.lens = 30
    cam = bpy.data.objects.new("exo_cam", cam_data)
    cam.location = (0, -10, 2.7)
    cam.rotation_euler = (math.radians(85), 0, 0)
    scn.collection.objects.link(cam)
    scn.camera = cam

    sun_data = bpy.data.lights.new("exo_sun", "SUN")
    sun_data.energy = 2.6
    sun_data.color = (1.0, 0.93, 0.8)
    sun = bpy.data.objects.new("exo_sun", sun_data)
    sun.rotation_euler = (math.radians(58), 0, math.radians(-38))
    scn.collection.objects.link(sun)

    rd = scn.render
    rd.engine = "BLENDER_EEVEE"
    rd.resolution_x, rd.resolution_y, rd.resolution_percentage = W * 2, H * 2, 100
    rd.film_transparent = False
    rd.filter_size = 0.01
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.look = "None"
    rd.image_settings.file_format = "PNG"
    rd.image_settings.color_mode = "RGB"
    rd.filepath = os.path.join(OUT_DIR, name + ".png")
    bpy.ops.render.render(write_still=True, scene=scn.name)


os.makedirs(OUT_DIR, exist_ok=True)
for scene_name, config in SCENES.items():
    build(scene_name, config)
if SCENE in bpy.data.scenes:
    bpy.data.scenes.remove(bpy.data.scenes[SCENE])
result = {"rendered": len(SCENES), "out": OUT_DIR}
