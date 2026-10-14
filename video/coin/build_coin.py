"""Builds the Flip-2 coin (Keethesh Labs mint) in the current Blender session.
Run inside Blender (MCP execute or `blender -b coin.blend --python build_coin.py`)."""
import math
import bmesh
import bpy

FONT_PATH = "/Users/keethesh/Experiments/flip-2/video/assets/fonts/InstrumentSerif-Regular.ttf"
FIELD_Z, RIM_Z, EDGE_Z = 0.062, 0.092, 0.078  # half-heights: field, rim top, edge shoulder
RELIEF = 0.022

# ---------- reset ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.worlds):
    for b in list(coll):
        coll.remove(b)
scene = bpy.context.scene
font = bpy.data.fonts.load(FONT_PATH, check_existing=True)


# ---------- materials ----------
def gold(name, rough, rough_var=0.06, color=(1.0, 0.66, 0.2, 1)):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = 1.0
    # micro-variation in roughness so reflections break up like real metal
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 180
    noise.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeMapRange")
    ramp.inputs["To Min"].default_value = rough - rough_var
    ramp.inputs["To Max"].default_value = rough + rough_var
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Value"])
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Roughness"])
    # very fine scratches/grain via bump
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 900
    nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m, nt, bsdf


polished, _, _ = gold("GoldPolished", 0.35, 0.05)  # satin relief
frosted, _, _ = gold("GoldFrosted", 0.315, 0.045, (0.95, 0.6, 0.18, 1))  # field

# reeded edge: radial stripes as bump, only meaningful on the cylinder wall
edge_mat, ent, ebsdf = gold("GoldReeded", 0.22, 0.05)
geo = ent.nodes.new("ShaderNodeTexCoord")  # object space, so reeds follow the coin
sep = ent.nodes.new("ShaderNodeSeparateXYZ")
ent.links.new(geo.outputs["Object"], sep.inputs["Vector"])
atan = ent.nodes.new("ShaderNodeMath")
atan.operation = "ARCTAN2"
ent.links.new(sep.outputs["Y"], atan.inputs[0])
ent.links.new(sep.outputs["X"], atan.inputs[1])
mul = ent.nodes.new("ShaderNodeMath")
mul.operation = "MULTIPLY"
mul.inputs[1].default_value = 160  # number of reeds
ent.links.new(atan.outputs["Value"], mul.inputs[0])
sine = ent.nodes.new("ShaderNodeMath")
sine.operation = "SINE"
ent.links.new(mul.outputs["Value"], sine.inputs[0])
ebump = ent.nodes.new("ShaderNodeBump")
ebump.inputs["Strength"].default_value = 0.9
ebump.inputs["Distance"].default_value = 0.01
ent.links.new(sine.outputs["Value"], ebump.inputs["Height"])
ent.links.new(ebump.outputs["Normal"], ebsdf.inputs["Normal"])

# ---------- body: revolve a profile ----------
prof = [  # (r, z) from top centre around the edge to bottom centre
    (0.0, FIELD_Z), (0.80, FIELD_Z), (0.835, FIELD_Z + 0.004), (0.875, RIM_Z - 0.004), (0.885, RIM_Z),
    (0.965, RIM_Z), (0.985, RIM_Z - 0.006), (0.998, EDGE_Z), (1.0, EDGE_Z - 0.01),
]
prof = prof + [(r, -z) for r, z in reversed(prof)]
me = bpy.data.meshes.new("CoinBody")
bm = bmesh.new()
verts = [bm.verts.new((r, 0, z)) for r, z in prof]
edges = [bm.edges.new((verts[i], verts[i + 1])) for i in range(len(verts) - 1)]
bmesh.ops.spin(bm, geom=verts + edges, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=256, use_merge=True)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(me)
bm.free()
body = bpy.data.objects.new("CoinBody", me)
scene.collection.objects.link(body)
for m in (frosted, polished, edge_mat):
    me.materials.append(m)
# material per face: field = frosted, rim = polished, wall = reeded
for p in me.polygons:
    c = p.center
    r = math.hypot(c.x, c.y)
    p.material_index = 0 if r < 0.82 else (2 if abs(c.z) < EDGE_Z - 0.008 and r > 0.99 else 1)
    p.use_smooth = True
coin = bpy.data.objects.new("Coin", None)
scene.collection.objects.link(coin)
body.parent = coin


# ---------- face decoration (built in XY plane facing +Z, then mounted) ----------
def text_obj(s, size, extrude=0.012, spacing=1.0):
    cu = bpy.data.curves.new(f"t_{s}", "FONT")
    cu.body = s
    cu.font = font
    cu.size = size
    cu.extrude = extrude
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.space_character = spacing
    cu.bevel_depth = 0.0015 if len(s) == 1 else 0.004
    ob = bpy.data.objects.new(f"t_{s}", cu)
    scene.collection.objects.link(ob)
    ob.data.materials.append(polished)
    return ob


def arc_text(s, radius, size, top=True, span=None):
    span = span or min(150, 11 * len(s))
    objs = []
    n = len(s)
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        f = (i + 0.5) / n
        if top:
            ang = math.radians(90 + span / 2 - f * span)
            rot = ang - math.pi / 2
        else:
            ang = math.radians(270 - span / 2 + f * span)
            rot = ang + math.pi / 2
        ob = text_obj(ch, size)
        ob.location = (radius * math.cos(ang), radius * math.sin(ang), 0)
        ob.rotation_euler = (0, 0, rot)
        objs.append(ob)
    return objs


def bead_ring(radius, count, r):
    me = bpy.data.meshes.new("beads")
    bm = bmesh.new()
    for i in range(count):
        a = math.tau * i / count
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r,
                                  matrix=__import__("mathutils").Matrix.Translation((radius * math.cos(a), radius * math.sin(a), 0)))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("beads", me)
    scene.collection.objects.link(ob)
    me.materials.append(polished)
    return ob


def make_face(center, top_legend, bottom_legend, name):
    root = bpy.data.objects.new(name, None)
    scene.collection.objects.link(root)
    parts = [text_obj(center, 0.62, spacing=1.02)]
    parts[0].location = (0, -0.02, 0)
    parts += arc_text(top_legend, 0.66, 0.135, top=True)
    parts += arc_text(bottom_legend, 0.66, 0.135, top=False)
    parts.append(bead_ring(0.775, 120, 0.0085))
    for p in parts:
        p.parent = root
        p.location.z = RELIEF / 2 if p.type == "FONT" else 0.0
    root.location = (0, 0, FIELD_Z)
    return root


front = make_face("YES", "KEETHESH LABS", "MMXXVI", "FaceFront")
back = make_face("NO", "IN DOUBT WE TRUST", "ONE DECISION", "FaceBack")
back.rotation_euler = (0, math.pi, 0)  # flip about the face's vertical axis: upright when the coin turns
back.location = (0, 0, -FIELD_Z)
front.parent = coin
back.parent = coin

# coin stands facing the camera (-Y); spin about world Z
coin.rotation_euler = (math.radians(90), 0, 0)
pivot = bpy.data.objects.new("Spin", None)
scene.collection.objects.link(pivot)
coin.parent = pivot

# ---------- studio: camera, lights, world ----------
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 135
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -12.0, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam


def area(name, loc, size, power, color=(1, 1, 1), shape="RECTANGLE", size_y=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = power
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    direction = -__import__("mathutils").Vector(loc)
    ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return ob


area("Key", (-4.5, -6, 4.5), 4.0, 450, (1.0, 0.95, 0.88), size_y=6)
area("Fill", (5, -5, -1), 6.0, 130, (0.9, 0.93, 1.0), size_y=3)
area("Rim", (0.5, 4, 5), 3.0, 350, (1.0, 0.9, 0.75))
area("Top", (0, -1, 7), 5.0, 150)

# Blender's bundled "interior" studio HDRI: metal needs something to reflect
world = bpy.data.worlds.new("Studio")
scene.world = world
wn = world.node_tree.nodes
bg = wn["Background"]
env = wn.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(f"{bpy.utils.resource_path('LOCAL')}/datafiles/studiolights/world/interior.exr")
world.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.55

# ---------- render settings ----------
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.render.film_transparent = True
scene.render.resolution_x = scene.render.resolution_y = 480
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Khronos PBR Neutral"  # keeps gold saturated; AgX washes it out
scene.view_settings.exposure = -0.3
cam_data.sensor_fit = "HORIZONTAL"
cam_data.ortho_scale = 2.2

# 72 frames, 5 degrees each: frame i shows rotation i*5 deg about Z
scene.frame_start, scene.frame_end = 0, 71
pivot.rotation_mode = "XYZ"
for i in range(72):
    pivot.rotation_euler = (0, 0, math.radians(i * 5))
    pivot.keyframe_insert("rotation_euler", index=2, frame=i)
scene.frame_set(0)
result = {"objects": len(bpy.data.objects)}
