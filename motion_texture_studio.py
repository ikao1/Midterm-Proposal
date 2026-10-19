bl_info = {
    "name": "Motion Texture Studio",
    "author": "Irene Kao",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Motion Texture",
    "description": "Animate stills, image sequences, and movies on objects, with moving raised textures.",
    "category": "Material",
}

import colorsys
import json
import math
import os
import re

import bpy

GRAPH_VERSION = 10
MATERIAL_PREFIX = "MotionTexture_"
MODIFIER_NAME = "MotionTexture Displacement"
HUE_GROUP_NAME = "MotionTexture_Hue"
IMAGE_EXTENSIONS = ".png;.jpg;.jpeg;.jpe;.bmp;.tga;.tif;.tiff;.exr;.hdr;.webp;.gif"
MOVIE_EXTENSIONS = ".mp4;.mov;.avi;.mkv;.webm;.m4v"
DROP_EXTENSIONS = IMAGE_EXTENSIONS + ";" + MOVIE_EXTENSIONS
IMAGE_FILTER = "*.png;*.jpg;*.jpeg;*.jpe;*.bmp;*.tga;*.tif;*.tiff;*.exr;*.hdr;*.webp;*.gif"
MOVIE_FILTER = "*.mp4;*.mov;*.avi;*.mkv;*.webm;*.m4v"

_SUSPEND_UPDATES = False

DEFAULTS = {
    "invert": False,
    "grayscale": 0.0,
    "hue": 0.0,
    "saturation": 1.0,
    "brightness": 1.0,
    "contrast": 1.0,
    "gamma": 1.0,
    "temperature": 0.0,
    "tint": 0.0,
    "posterize": 0,
    "amount": 1.0,
    "scale": 1.0,
    "tiling_x": 1.0,
    "tiling_y": 1.0,
    "rotation": 0.0,
    "offset_x": 0.0,
    "offset_y": 0.0,
    "flip_x": False,
    "flip_y": False,
    "relief": 0.5,
    "depth": 0.5,
    "relief_invert": False,
    "detail": 0.0,
    "detail_scale": 8.0,
    "relief_speed": 0.5,
    "relief_amplitude": 0.5,
    "relief_phase": 0.0,
    "roughness": 0.5,
    "metallic": 0.0,
    "specular": 0.5,
    "ior": 1.5,
    "coat": 0.0,
    "coat_roughness": 0.03,
    "sheen": 0.0,
    "sheen_roughness": 0.5,
    "anisotropic": 0.0,
    "subsurface": 0.0,
    "transmission": 0.0,
    "alpha": 1.0,
    "normal_strength": 1.0,
    "emission": 0.0,
    "glow_mask": False,
    "glow_color": (1.0, 1.0, 1.0, 1.0),
}

RESET_SECTIONS = {
    "COLOR": (
        "invert", "grayscale", "hue", "saturation", "brightness", "contrast",
        "gamma", "temperature", "tint", "posterize", "amount",
    ),
    "TRANSFORM": (
        "scale", "tiling_x", "tiling_y", "rotation", "offset_x", "offset_y",
        "flip_x", "flip_y",
    ),
    "SURFACE": (
        "relief", "depth", "relief_invert", "detail", "detail_scale",
        "roughness", "metallic", "specular", "ior", "coat", "coat_roughness",
        "sheen", "sheen_roughness", "anisotropic", "subsurface", "transmission",
        "alpha", "normal_strength", "emission", "glow_mask", "glow_color",
    ),
    "ANIMATION": (
        "relief_speed", "relief_amplitude", "relief_phase",
    ),
    "ALL": tuple(DEFAULTS.keys()),
}

SURFACE_PRESETS = {
    "MATTE": {"label": "Matte", "roughness": 0.9, "metallic": 0.0, "specular": 0.25, "ior": 1.45, "coat": 0.0, "coat_roughness": 0.1, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "GLOSSY": {"label": "Glossy", "roughness": 0.15, "metallic": 0.0, "specular": 0.8, "ior": 1.5, "coat": 0.4, "coat_roughness": 0.05, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "PLASTIC": {"label": "Plastic", "roughness": 0.3, "metallic": 0.0, "specular": 0.6, "ior": 1.45, "coat": 0.0, "coat_roughness": 0.03, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "CERAMIC": {"label": "Ceramic", "roughness": 0.12, "metallic": 0.0, "specular": 0.7, "ior": 1.5, "coat": 0.6, "coat_roughness": 0.03, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "METAL": {"label": "Metal", "roughness": 0.25, "metallic": 1.0, "specular": 0.5, "ior": 1.5, "coat": 0.0, "coat_roughness": 0.03, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "BRUSHED": {"label": "Brushed", "roughness": 0.35, "metallic": 1.0, "specular": 0.5, "ior": 1.5, "coat": 0.0, "coat_roughness": 0.03, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.8, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "VELVET": {"label": "Velvet", "roughness": 0.85, "metallic": 0.0, "specular": 0.2, "ior": 1.45, "coat": 0.0, "coat_roughness": 0.03, "sheen": 1.0, "sheen_roughness": 0.3, "anisotropic": 0.0, "subsurface": 0.1, "transmission": 0.0, "alpha": 1.0, "emission": 0.0},
    "GLASS": {"label": "Glass", "roughness": 0.05, "metallic": 0.0, "specular": 0.5, "ior": 1.45, "coat": 0.0, "coat_roughness": 0.03, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 1.0, "alpha": 1.0, "emission": 0.0},
    "GLOWING": {"label": "Glowing", "roughness": 0.6, "metallic": 0.0, "specular": 0.4, "ior": 1.45, "coat": 0.0, "coat_roughness": 0.03, "sheen": 0.0, "sheen_roughness": 0.5, "anisotropic": 0.0, "subsurface": 0.0, "transmission": 0.0, "alpha": 1.0, "emission": 1.5},
}
PRESET_ITEMS = [(key, SURFACE_PRESETS[key]["label"], "") for key in SURFACE_PRESETS]

MOTION_PRESETS = (
    ("SCROLL_X", "Scroll X", "Slide the image and its relief horizontally"),
    ("SCROLL_Y", "Scroll Y", "Slide the image and its relief vertically"),
    ("DRIFT", "Drift", "Slow diagonal movement"),
    ("PULSE", "Pulse", "Breathe the raised relief in and out"),
    ("BREATHE", "Breathe", "Gently scale the texture"),
    ("RIPPLE", "Ripple", "Move the relief with a repeating swell"),
    ("FLICKER", "Flicker", "Step the brightness like unstable light"),
    ("STOP_MOTION", "Stop Motion", "Step the texture in held increments"),
)
MOTION_PRESET_ITEMS = [(key, label, desc) for key, label, desc in MOTION_PRESETS]

RELIEF_MOTION_ITEMS = (
    ("DRIFT", "Drift", "Move the procedural relief sideways"),
    ("PULSE", "Pulse", "Raise and lower the relief"),
    ("RIPPLE", "Ripple", "Move and pulse the relief"),
    ("CRAWL", "Crawl", "Creep the relief diagonally"),
)

SOURCE_MODE_ITEMS = (
    ("STILL", "Still", "One image"),
    ("SEQUENCE", "Image Sequence", "Numbered image files"),
    ("MOVIE", "Movie", "Video file"),
)
LOOP_ITEMS = (
    ("ONCE", "Once", "Play once and hold the last frame"),
    ("LOOP", "Loop", "Repeat from the start"),
)
COLOR_SPACE_ITEMS = (
    ("sRGB", "sRGB", ""),
    ("Non-Color", "Non-Color", ""),
    ("Linear Rec.709", "Linear", ""),
)
RELIEF_MODE_ITEMS = (
    ("BUMP", "Bump", "Fast raised shading"),
    ("DISPLACEMENT", "Displacement", "True displaced geometry; best in Cycles"),
)
RELIEF_SOURCE_ITEMS = (
    ("IMAGE", "Image Luminance", "Use the source image's brightness as height"),
    ("NOISE", "Noise", "Use animated procedural noise as height"),
    ("WAVE", "Wave", "Use animated bands as height"),
)
INTERPOLATION_ITEMS = (
    ("BEZIER", "Bezier", ""),
    ("LINEAR", "Linear", ""),
    ("CONSTANT", "Constant", ""),
)


def _mix(nt, name, blend="MIX"):
    node = nt.nodes.new("ShaderNodeMixRGB")
    node.name = name
    node.blend_type = blend
    return node


def _link_single(nt, to_socket, from_socket):
    for link in list(to_socket.links):
        nt.links.remove(link)
    if from_socket is not None:
        nt.links.new(from_socket, to_socket)


def _vmath(nt, name, op, a, b=None):
    node = nt.nodes.new("ShaderNodeVectorMath")
    node.name = name
    node.operation = op
    if isinstance(a, tuple):
        node.inputs[0].default_value = a
    else:
        nt.links.new(a, node.inputs[0])
    if b is not None:
        if isinstance(b, tuple):
            node.inputs[1].default_value = b
        else:
            nt.links.new(b, node.inputs[1])
    return node


def _posterize(nt, in_socket):
    mul = _vmath(nt, "MT_Post_mul", "MULTIPLY", in_socket, (8.0,) * 3)
    flr = _vmath(nt, "MT_Post_flr", "FLOOR", mul.outputs["Vector"])
    div = _vmath(nt, "MT_Post_div", "MULTIPLY", flr.outputs["Vector"], (1.0 / 8.0,) * 3)
    return mul, div


def _set_input(node, name, value):
    try:
        node.inputs[name].default_value = value
    except Exception:
        pass


def _tint_color(temperature, tint):
    r = 1.0 + 0.28 * temperature + 0.12 * tint
    g = 1.0 - 0.18 * tint
    b = 1.0 - 0.28 * temperature + 0.12 * tint
    clamp = lambda v: max(0.05, min(2.0, v))
    return (clamp(r), clamp(g), clamp(b), 1.0)


def _hue_rgb(t):
    return colorsys.hsv_to_rgb(t % 1.0, 1.0, 1.0) + (1.0,)


def _fill_hue_ramp(cr):
    cr.interpolation = "LINEAR"
    stops = [0.0, 1 / 6.0, 2 / 6.0, 3 / 6.0, 4 / 6.0, 5 / 6.0, 1.0]
    while len(cr.elements) > 1:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = 0.0
    cr.elements[0].color = _hue_rgb(0.0)
    for p in stops[1:]:
        cr.elements.new(p).color = _hue_rgb(p)


def _hue_group():
    ng = bpy.data.node_groups.get(HUE_GROUP_NAME)
    if ng is None:
        ng = bpy.data.node_groups.new(HUE_GROUP_NAME, "ShaderNodeTree")
    node = ng.nodes.get("Hue")
    if node is None:
        node = ng.nodes.new("ShaderNodeValToRGB")
        node.name = "Hue"
        _fill_hue_ramp(node.color_ramp)
    return ng


def _get_hue_group_readonly():
    ng = bpy.data.node_groups.get(HUE_GROUP_NAME)
    if ng is not None and ng.nodes.get("Hue"):
        return ng
    return None


def _remove_hue_group():
    ng = bpy.data.node_groups.get(HUE_GROUP_NAME)
    if ng is not None:
        bpy.data.node_groups.remove(ng)


def _show_material_preview():
    wm = getattr(bpy.context, "window_manager", None)
    if wm is None:
        return
    for win in wm.windows:
        screen = getattr(win, "screen", None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                shading = getattr(space, "shading", None)
                if shading is not None and shading.type == "SOLID":
                    shading.type = "MATERIAL"


def _material_name(obj):
    return MATERIAL_PREFIX + re.sub(r"[^A-Za-z0-9_]+", "_", obj.name)[:48]


def _find_material(obj):
    mat = bpy.data.materials.get(_material_name(obj))
    if mat is not None:
        return mat
    for slot in getattr(obj, "material_slots", ()):
        candidate = slot.material
        if candidate is not None and candidate.name.startswith(MATERIAL_PREFIX):
            return candidate
    return None


def _get_material(obj):
    mat = _find_material(obj)
    if mat is None:
        mat = bpy.data.materials.new(_material_name(obj))
    mat.use_nodes = True
    slots = obj.data.materials
    index = next((i for i, slot in enumerate(slots) if slot == mat), None)
    if index is None:
        slots.append(mat)
        index = len(slots) - 1
    obj.active_material_index = index
    return mat


def _settings(context):
    obj = getattr(context, "active_object", None)
    if obj is not None and obj.type == "MESH":
        return getattr(obj, "motion_texture", None)
    return None


def _settings_for(obj):
    if obj is None or obj.type != "MESH":
        return None
    return getattr(obj, "motion_texture", None)


def _sequence_range(path):
    folder = os.path.dirname(path)
    base = os.path.basename(path)
    stem, ext = os.path.splitext(base)
    match = re.match(r"^(.*?)(\d+)$", stem)
    if not match or not os.path.isdir(folder):
        return None
    prefix, _number = match.group(1), int(match.group(2))
    pattern = re.compile(r"^%s(\d+)%s$" % (re.escape(prefix), re.escape(ext)), re.IGNORECASE)
    numbers = []
    try:
        for filename in os.listdir(folder):
            found = pattern.match(filename)
            if found:
                numbers.append(int(found.group(1)))
    except OSError:
        return None
    if not numbers:
        return None
    return min(numbers), max(numbers)


def _apply_source_settings(node, s):
    if node is None or s is None:
        return
    image = node.image
    if image is None:
        return
    try:
        image.colorspace_settings.name = s.color_space
    except Exception:
        pass
    user = node.image_user
    if s.source_mode == "SEQUENCE":
        try:
            image.source = "SEQUENCE"
        except Exception:
            pass
        start = max(1, s.frame_start)
        end = max(start, s.frame_end)
        user.frame_start = start
        user.frame_duration = max(1, end - start + 1)
        user.frame_offset = s.frame_offset
        user.use_cyclic = s.loop_mode == "LOOP"
        user.use_auto_refresh = True
    elif s.source_mode == "MOVIE":
        try:
            image.source = "MOVIE"
        except Exception:
            pass
        user.frame_start = 1
        user.frame_offset = s.frame_offset
        user.use_cyclic = s.loop_mode == "LOOP"
        user.use_auto_refresh = True
    else:
        try:
            image.source = "FILE"
        except Exception:
            pass
        user.frame_start = 1
        user.frame_duration = 1
        user.frame_offset = 0
        user.use_cyclic = False


def _build(mat, s):
    nt = mat.node_tree
    nt.nodes.clear()
    nt["mt_version"] = GRAPH_VERSION
    link = nt.links.new

    coord = nt.nodes.new("ShaderNodeTexCoord")
    coord.name = "MT_Coord"
    coord.location = (-1900, 0)

    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.name = "MT_Map"
    mapn.location = (-1680, 0)

    image = nt.nodes.new("ShaderNodeTexImage")
    image.name = "MT_Image"
    image.location = (-1460, 0)
    image.extension = "REPEAT"

    invert = nt.nodes.new("ShaderNodeInvert")
    invert.name = "MT_Invert"
    invert.location = (-1240, 220)

    mono_bw = nt.nodes.new("ShaderNodeRGBToBW")
    mono_bw.name = "MT_Mono_BW"
    mono_bw.location = (-1240, -40)

    mono_mix = _mix(nt, "MT_Mono_Mix")
    mono_mix.location = (-1040, 120)

    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.name = "MT_HueSat"
    hsv.location = (-820, 120)

    gamma = nt.nodes.new("ShaderNodeGamma")
    gamma.name = "MT_Gamma"
    gamma.location = (-600, 120)

    bc = nt.nodes.new("ShaderNodeBrightContrast")
    bc.name = "MT_BC"
    bc.location = (-400, 120)

    tint = _mix(nt, "MT_Tint", blend="MULTIPLY")
    tint.location = (-200, 120)

    post_mul, post_div = _posterize(nt, tint.outputs["Color"])
    post_mul.location = (0, -140)
    post_div.location = (260, -140)

    post_mix = _mix(nt, "MT_Post_Mix")
    post_mix.location = (460, 80)

    amount = _mix(nt, "MT_Amount")
    amount.location = (660, 80)

    glow = _mix(nt, "MT_Glow", blend="MULTIPLY")
    glow.location = (220, 320)

    glow_lum = nt.nodes.new("ShaderNodeRGBToBW")
    glow_lum.name = "MT_Glow_Lum"
    glow_lum.location = (220, 580)

    glow_mul = nt.nodes.new("ShaderNodeMath")
    glow_mul.name = "MT_Glow_Mul"
    glow_mul.operation = "MULTIPLY"
    glow_mul.location = (420, 580)

    motion_map = nt.nodes.new("ShaderNodeMapping")
    motion_map.name = "MT_MotionMap"
    motion_map.location = (-1460, -620)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.name = "MT_Noise"
    noise.location = (-1240, -540)
    noise.inputs["Detail"].default_value = 6.0

    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.name = "MT_Wave"
    wave.location = (-1240, -820)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.wave_profile = "SIN"

    proc_mix = _mix(nt, "MT_ProcMix")
    proc_mix.location = (-1020, -660)

    bump_bw = nt.nodes.new("ShaderNodeRGBToBW")
    bump_bw.name = "MT_Bump_BW"
    bump_bw.location = (-1020, -340)

    detail_mix = _mix(nt, "MT_Detail_Mix")
    detail_mix.location = (-800, -500)

    bump = nt.nodes.new("ShaderNodeBump")
    bump.name = "MT_Bump"
    bump.location = (-580, -500)

    displacement = nt.nodes.new("ShaderNodeDisplacement")
    displacement.name = "MT_Displace"
    displacement.location = (-360, -700)

    normal_img = nt.nodes.new("ShaderNodeTexImage")
    normal_img.name = "MT_Normal_Img"
    normal_img.location = (260, -620)

    normal_flat = nt.nodes.new("ShaderNodeRGB")
    normal_flat.name = "MT_NormalFlat"
    normal_flat.location = (260, -840)
    normal_flat.outputs["Color"].default_value = (0.5, 0.5, 1.0, 1.0)

    normal_map = nt.nodes.new("ShaderNodeNormalMap")
    normal_map.name = "MT_NormalMap"
    normal_map.location = (460, -620)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.name = "MT_BSDF"
    bsdf.location = (600, 80)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.name = "MT_Out"
    out.location = (920, 80)

    link(coord.outputs["UV"], mapn.inputs["Vector"])
    link(mapn.outputs["Vector"], image.inputs["Vector"])

    link(image.outputs["Color"], invert.inputs["Color"])
    link(invert.outputs["Color"], mono_bw.inputs["Color"])
    link(invert.outputs["Color"], mono_mix.inputs["Color1"])
    link(mono_bw.outputs["Val"], mono_mix.inputs["Color2"])
    link(mono_mix.outputs["Color"], hsv.inputs["Color"])
    link(hsv.outputs["Color"], gamma.inputs["Color"])
    link(gamma.outputs["Color"], bc.inputs["Color"])
    link(bc.outputs["Color"], tint.inputs["Color1"])
    link(tint.outputs["Color"], post_mul.inputs[0])
    link(post_div.outputs["Vector"], post_mix.inputs["Color2"])
    link(tint.outputs["Color"], post_mix.inputs["Color1"])
    link(post_mix.outputs["Color"], amount.inputs["Color2"])
    link(image.outputs["Color"], amount.inputs["Color1"])
    link(amount.outputs["Color"], bsdf.inputs["Base Color"])

    link(amount.outputs["Color"], glow.inputs["Color1"])
    try:
        link(glow.outputs["Color"], bsdf.inputs["Emission Color"])
    except Exception:
        pass
    link(amount.outputs["Color"], glow_lum.inputs["Color"])
    link(glow_lum.outputs["Val"], glow_mul.inputs[0])

    link(coord.outputs["Object"], motion_map.inputs["Vector"])
    link(motion_map.outputs["Vector"], noise.inputs["Vector"])
    link(motion_map.outputs["Vector"], wave.inputs["Vector"])
    link(noise.outputs["Factor"], proc_mix.inputs["Color1"])
    link(wave.outputs["Fac"], proc_mix.inputs["Color2"])
    link(image.outputs["Color"], bump_bw.inputs["Color"])
    link(bump_bw.outputs["Val"], detail_mix.inputs["Color1"])
    link(proc_mix.outputs["Color"], detail_mix.inputs["Color2"])
    link(detail_mix.outputs["Color"], bump.inputs["Height"])
    link(detail_mix.outputs["Color"], displacement.inputs["Height"])
    link(mapn.outputs["Vector"], normal_img.inputs["Vector"])
    link(normal_flat.outputs["Color"], normal_map.inputs["Color"])
    link(normal_map.outputs["Normal"], bump.inputs["Normal"])
    link(bump.outputs["Normal"], bsdf.inputs["Normal"])

    link(bsdf.outputs["BSDF"], out.inputs["Surface"])
    _set_values(nt, s)


def _set_values(nt, s):
    mapn = nt.nodes["MT_Map"]
    image_node = nt.nodes["MT_Image"]
    invert = nt.nodes["MT_Invert"]
    mono_mix = nt.nodes["MT_Mono_Mix"]
    hsv = nt.nodes["MT_HueSat"]
    gamma = nt.nodes["MT_Gamma"]
    bc = nt.nodes["MT_BC"]
    tint = nt.nodes["MT_Tint"]
    post_mul = nt.nodes["MT_Post_mul"]
    post_div = nt.nodes["MT_Post_div"]
    post_mix = nt.nodes["MT_Post_Mix"]
    amount = nt.nodes["MT_Amount"]
    glow = nt.nodes["MT_Glow"]
    glow_lum = nt.nodes["MT_Glow_Lum"]
    glow_mul = nt.nodes["MT_Glow_Mul"]
    noise = nt.nodes["MT_Noise"]
    wave = nt.nodes["MT_Wave"]
    proc_mix = nt.nodes["MT_ProcMix"]
    detail_mix = nt.nodes["MT_Detail_Mix"]
    bump = nt.nodes["MT_Bump"]
    displacement = nt.nodes["MT_Displace"]
    normal_img = nt.nodes["MT_Normal_Img"]
    normal_flat = nt.nodes["MT_NormalFlat"]
    normal_map = nt.nodes["MT_NormalMap"]
    bsdf = nt.nodes["MT_BSDF"]
    out = nt.nodes["MT_Out"]

    if s.image is not None:
        image_node.image = s.image
        _apply_source_settings(image_node, s)
    else:
        image_node.image = None

    flip_x = -1.0 if s.flip_x else 1.0
    flip_y = -1.0 if s.flip_y else 1.0
    mapn.inputs["Location"].default_value = (s.offset_x, s.offset_y, 0.0)
    mapn.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(s.rotation))
    mapn.inputs["Scale"].default_value = (
        max(s.tiling_x, 0.001) * s.scale * flip_x,
        max(s.tiling_y, 0.001) * s.scale * flip_y,
        1.0,
    )

    invert.inputs["Factor"].default_value = 1.0 if s.invert else 0.0
    mono_mix.inputs["Factor"].default_value = s.grayscale
    hsv.inputs["Hue"].default_value = 0.5 + s.hue * 0.5
    hsv.inputs["Saturation"].default_value = s.saturation
    hsv.inputs["Value"].default_value = s.brightness
    gamma.inputs["Gamma"].default_value = max(s.gamma, 0.01)
    bc.inputs["Brightness"].default_value = 0.0
    bc.inputs["Contrast"].default_value = s.contrast - 1.0
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs["Color2"].default_value = _tint_color(s.temperature, s.tint)
    amount.inputs["Factor"].default_value = s.amount

    levels = s.posterize
    on = levels >= 2
    lv = float(levels if on else 8)
    post_mul.inputs[1].default_value = (lv, lv, lv)
    post_div.inputs[1].default_value = (1.0 / lv,) * 3
    post_mix.inputs["Factor"].default_value = 1.0 if on else 0.0

    glow.inputs["Factor"].default_value = 1.0
    glow.inputs["Color2"].default_value = s.glow_color
    glow_mul.inputs[1].default_value = s.emission
    strength = bsdf.inputs.get("Emission Strength")
    if strength is not None:
        if s.glow_mask:
            _link_single(nt, strength, glow_mul.outputs["Value"])
        else:
            _link_single(nt, strength, None)
            strength.default_value = s.emission

    bump.invert = s.relief_invert
    bump.inputs["Strength"].default_value = s.relief
    bump.inputs["Distance"].default_value = 0.02 + 0.5 * s.depth
    displacement.inputs["Scale"].default_value = 0.02 + 0.35 * s.depth
    displacement.inputs["Midlevel"].default_value = 0.5

    if s.relief_source == "IMAGE":
        detail_mix.inputs["Factor"].default_value = s.detail
    else:
        detail_mix.inputs["Factor"].default_value = 1.0
    proc_mix.inputs["Factor"].default_value = 1.0 if s.relief_source == "WAVE" else 0.0
    noise.inputs["Scale"].default_value = max(s.detail_scale, 0.1)
    wave.inputs["Scale"].default_value = max(s.detail_scale, 0.1)
    wave.inputs["Distortion"].default_value = 1.5

    if s.normal_image is not None:
        normal_img.image = s.normal_image
        _link_single(nt, normal_map.inputs["Color"], normal_img.outputs["Color"])
    else:
        normal_img.image = None
        _link_single(nt, normal_map.inputs["Color"], normal_flat.outputs["Color"])
    normal_map.inputs["Strength"].default_value = s.normal_strength

    _set_input(bsdf, "Roughness", s.roughness)
    _set_input(bsdf, "Metallic", s.metallic)
    _set_input(bsdf, "Specular IOR Level", s.specular)
    _set_input(bsdf, "IOR", s.ior)
    _set_input(bsdf, "Coat Weight", s.coat)
    _set_input(bsdf, "Coat Roughness", s.coat_roughness)
    _set_input(bsdf, "Sheen Weight", s.sheen)
    _set_input(bsdf, "Sheen Roughness", s.sheen_roughness)
    _set_input(bsdf, "Anisotropic", s.anisotropic)
    _set_input(bsdf, "Subsurface Weight", s.subsurface)
    _set_input(bsdf, "Transmission Weight", s.transmission)
    _set_input(bsdf, "Alpha", s.alpha)

    _link_single(nt, out.inputs["Displacement"], displacement.outputs["Displacement"] if s.relief_mode == "DISPLACEMENT" else None)


def _set_displacement_modifier(obj, s):
    modifier = obj.modifiers.get(MODIFIER_NAME)
    if s.relief_mode == "DISPLACEMENT":
        if modifier is None:
            modifier = obj.modifiers.new(MODIFIER_NAME, "SUBSURF")
            modifier.subdivision_type = "SIMPLE"
        level = max(0, min(6, int(s.subdivision_level)))
        modifier.levels = level
        modifier.render_levels = level
    elif modifier is not None:
        obj.modifiers.remove(modifier)


def _apply(context, rebuild=False, obj=None):
    obj = obj or getattr(context, "active_object", None)
    if obj is None or obj.type != "MESH":
        return False
    s = _settings_for(obj)
    if s is None:
        return False
    mat = _get_material(obj)
    nt = mat.node_tree
    stale = nt.get("mt_version") != GRAPH_VERSION
    if rebuild or stale or nt.nodes.get("MT_BSDF") is None:
        _build(mat, s)
    else:
        _set_values(nt, s)
    _set_displacement_modifier(obj, s)
    if s.preview_on_selected:
        _show_material_preview()
    try:
        blended = s.alpha < 0.999 or s.transmission > 0.0
        mat.surface_render_method = "BLENDED" if blended else "DITHERED"
    except Exception:
        pass
    try:
        mat.displacement_method = "BOTH" if s.relief_mode == "DISPLACEMENT" else "BUMP"
    except Exception:
        pass
    if nt.animation_data is not None and nt.animation_data.action is not None:
        context.scene.frame_set(context.scene.frame_current)
    return True


def _on_update(self, context):
    if _SUSPEND_UPDATES:
        return
    obj = getattr(context, "active_object", None)
    if obj is None or obj.type != "MESH":
        return
    if getattr(obj, "motion_texture", None) is None:
        return
    _apply(context, rebuild=False, obj=obj)


def _on_interpolation(self, context):
    if _SUSPEND_UPDATES:
        return
    obj = getattr(context, "active_object", None)
    if obj is None or obj.type != "MESH":
        return
    action = _action_for(obj)
    _set_interpolation(action, self.interpolation)


def _on_fps(self, context):
    try:
        context.scene.render.fps = max(1, int(round(self.fps)))
    except Exception:
        pass


def _iter_fcurves(action):
    if action is None:
        return
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        try:
            for fcurve in fcurves:
                yield fcurve
            return
        except Exception:
            pass
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            if getattr(strip, "type", "") != "KEYFRAME":
                continue
            for channelbag in getattr(strip, "channelbags", ()):
                for fcurve in getattr(channelbag, "fcurves", ()):
                    yield fcurve


def _action_for(obj):
    mat = _find_material(obj)
    if mat is None or mat.node_tree is None:
        return None
    animation_data = mat.node_tree.animation_data
    if animation_data is None:
        return None
    return animation_data.action


def _key_socket(node, socket_name, frame, value=None):
    if node is None:
        return
    socket = node.inputs.get(socket_name)
    if socket is None:
        return
    if value is not None:
        socket.default_value = value
    socket.keyframe_insert(data_path="default_value", frame=frame)


def _key_all(obj, context, frame=None):
    mat = _find_material(obj)
    if mat is None:
        return False
    nt = mat.node_tree
    s = _settings_for(obj)
    _set_values(nt, s)
    frame = context.scene.frame_current if frame is None else frame
    _key_socket(nt.nodes["MT_Map"], "Location", frame)
    _key_socket(nt.nodes["MT_Map"], "Rotation", frame)
    _key_socket(nt.nodes["MT_Map"], "Scale", frame)
    _key_socket(nt.nodes["MT_HueSat"], "Hue", frame)
    _key_socket(nt.nodes["MT_HueSat"], "Saturation", frame)
    _key_socket(nt.nodes["MT_HueSat"], "Value", frame)
    _key_socket(nt.nodes["MT_Gamma"], "Gamma", frame)
    _key_socket(nt.nodes["MT_BC"], "Contrast", frame)
    _key_socket(nt.nodes["MT_Amount"], "Factor", frame)
    _key_socket(nt.nodes["MT_Bump"], "Strength", frame)
    _key_socket(nt.nodes["MT_Bump"], "Distance", frame)
    _key_socket(nt.nodes["MT_Detail_Mix"], "Factor", frame)
    _key_socket(nt.nodes["MT_Noise"], "Scale", frame)
    _key_socket(nt.nodes["MT_Wave"], "Scale", frame)
    _key_socket(nt.nodes["MT_BSDF"], "Roughness", frame)
    _key_socket(nt.nodes["MT_BSDF"], "Metallic", frame)
    _key_socket(nt.nodes["MT_BSDF"], "Specular IOR Level", frame)
    _key_socket(nt.nodes["MT_Displace"], "Scale", frame)
    _set_interpolation(_action_for(obj), s.interpolation)
    _add_cycles(_action_for(obj))
    return True


def _clear_animation(obj):
    mat = _find_material(obj)
    if mat is None or mat.node_tree is None:
        return
    if mat.node_tree.animation_data is not None:
        mat.node_tree.animation_data_clear()


def _set_interpolation(action, mode):
    if action is None:
        return
    for fcurve in _iter_fcurves(action):
        for point in fcurve.keyframe_points:
            point.interpolation = mode
        fcurve.update()


def _add_cycles(action):
    if action is None:
        return
    for fcurve in _iter_fcurves(action):
        if not any(modifier.type == "CYCLES" for modifier in fcurve.modifiers):
            fcurve.modifiers.new("CYCLES")


def _delete_key_at_frame(obj, frame):
    action = _action_for(obj)
    if action is None:
        return 0
    removed = 0
    for fcurve in list(_iter_fcurves(action)):
        for point in list(fcurve.keyframe_points):
            if abs(point.co.x - frame) < 0.5:
                fcurve.keyframe_points.remove(point)
                removed += 1
        fcurve.update()
    return removed


def _copy_settings(source, target):
    global _SUSPEND_UPDATES
    if source is None or target is None:
        return
    previous = _SUSPEND_UPDATES
    _SUSPEND_UPDATES = True
    try:
        for prop in source.bl_rna.properties:
            key = prop.identifier
            if key == "rna_type":
                continue
            try:
                setattr(target, key, getattr(source, key))
            except Exception:
                pass
    finally:
        _SUSPEND_UPDATES = previous


def _preset_directory():
    directory = bpy.utils.user_resource("SCRIPTS", path="presets/motion_texture_studio", create=True)
    os.makedirs(directory, exist_ok=True)
    return directory


def _preset_files():
    directory = _preset_directory()
    files = []
    try:
        for name in os.listdir(directory):
            if name.lower().endswith(".json"):
                files.append(os.path.join(directory, name))
    except OSError:
        pass
    return sorted(files, key=lambda value: os.path.basename(value).lower())


def _safe_filename(name):
    cleaned = re.sub(r"[^A-Za-z0-9_\- ]+", "_", name).strip()
    return cleaned or "Preset"


def _settings_dict(s):
    data = {"format": "motion-texture-studio", "version": 1}
    for key in DEFAULTS:
        value = getattr(s, key, None)
        if hasattr(value, "__len__") and not isinstance(value, str):
            value = list(value)
        data[key] = value
    for key in (
        "source_mode", "frame_start", "frame_end", "fps", "frame_offset",
        "loop_mode", "color_space", "enable_animation", "interpolation",
        "relief_mode", "relief_source", "animate_relief", "subdivision_level",
    ):
        data[key] = getattr(s, key, None)
    data["image_path"] = bpy.path.abspath(s.image.filepath) if s.image is not None else ""
    data["normal_image_path"] = bpy.path.abspath(s.normal_image.filepath) if s.normal_image is not None else ""
    return data


def _write_preset(path, s):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_settings_dict(s), handle, indent=2)


def _apply_settings_dict(s, data):
    global _SUSPEND_UPDATES
    previous = _SUSPEND_UPDATES
    _SUSPEND_UPDATES = True
    image_path = ""
    normal_path = ""
    try:
        for key, value in data.items():
            if key in {"format", "version", "image_path", "normal_image_path"}:
                continue
            prop = s.bl_rna.properties.get(key)
            if prop is None:
                continue
            try:
                if key == "glow_color" and isinstance(value, list):
                    value = tuple(value)
                setattr(s, key, value)
            except Exception:
                pass
        image_path = data.get("image_path", "")
        normal_path = data.get("normal_image_path", "")
        if image_path and os.path.exists(bpy.path.abspath(image_path)):
            image = bpy.data.images.load(bpy.path.abspath(image_path), check_existing=True)
            s.image = image
            s.source_path = bpy.path.abspath(image_path)
        if normal_path and os.path.exists(bpy.path.abspath(normal_path)):
            s.normal_image = bpy.data.images.load(bpy.path.abspath(normal_path), check_existing=True)
    finally:
        _SUSPEND_UPDATES = previous


def _apply_settings_file(context, path, warn=True):
    obj = getattr(context, "active_object", None)
    s = _settings_for(obj)
    if s is None:
        return False, "Select a mesh object first"
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        return False, "Could not read preset: %s" % exc
    if data.get("format") != "motion-texture-studio":
        return False, "That file is not a Motion Texture preset"
    _apply_settings_dict(s, data)
    if s.source_mode in {"SEQUENCE", "MOVIE"}:
        context.scene.frame_start = max(1, s.frame_start)
        context.scene.frame_end = max(s.frame_start, s.frame_end)
    _apply(context, rebuild=False, obj=obj)
    return True, ""


def _load_source(context, path, mode):
    obj = getattr(context, "active_object", None)
    s = _settings_for(obj)
    if s is None:
        return False, "Select a mesh object first"
    if not path or not os.path.exists(path):
        return False, "File not found"
    try:
        image = bpy.data.images.load(path, check_existing=True)
    except Exception as exc:
        return False, "Could not load source: %s" % exc
    global _SUSPEND_UPDATES
    previous = _SUSPEND_UPDATES
    _SUSPEND_UPDATES = True
    try:
        s.image = image
        s.source_path = path
        s.source_mode = mode
        if mode == "SEQUENCE":
            detected = _sequence_range(path)
            if detected is not None:
                s.frame_start, s.frame_end = detected
            else:
                s.frame_start = 1
                s.frame_end = max(1, context.scene.frame_end)
            s.enable_animation = True
        elif mode == "MOVIE":
            try:
                image.source = "MOVIE"
                image.reload()
            except Exception:
                pass
            s.frame_start = 1
            duration = int(getattr(image, "frame_duration", 0) or 0)
            s.frame_end = duration if duration > 1 else max(1, context.scene.frame_end)
            s.enable_animation = True
        else:
            s.frame_start = 1
            s.frame_end = 1
        s.frame_offset = 0
    finally:
        _SUSPEND_UPDATES = previous
    if mode in {"SEQUENCE", "MOVIE"}:
        context.scene.frame_start = s.frame_start
        context.scene.frame_end = s.frame_end
        context.scene.frame_set(s.frame_start)
    _apply(context, rebuild=False, obj=obj)
    return True, ""


class MotionTextureSettings(bpy.types.PropertyGroup):
    image: bpy.props.PointerProperty(name="Image", type=bpy.types.Image, update=_on_update)
    normal_image: bpy.props.PointerProperty(name="Normal Map", type=bpy.types.Image, update=_on_update)
    source_path: bpy.props.StringProperty(name="Source", default="", subtype="FILE_PATH")
    source_mode: bpy.props.EnumProperty(name="Source Type", items=SOURCE_MODE_ITEMS, default="STILL", update=_on_update)
    frame_start: bpy.props.IntProperty(name="Source Start", min=1, default=1, update=_on_update)
    frame_end: bpy.props.IntProperty(name="Source End", min=1, default=1, update=_on_update)
    fps: bpy.props.FloatProperty(name="FPS", min=1.0, max=240.0, default=24.0, update=_on_fps)
    frame_offset: bpy.props.IntProperty(name="Frame Offset", default=0, update=_on_update)
    loop_mode: bpy.props.EnumProperty(name="Loop", items=LOOP_ITEMS, default="LOOP", update=_on_update)
    color_space: bpy.props.EnumProperty(name="Color Space", items=COLOR_SPACE_ITEMS, default="sRGB", update=_on_update)
    preview_on_selected: bpy.props.BoolProperty(name="Preview on Selected", default=True, update=_on_update)

    enable_animation: bpy.props.BoolProperty(name="Enable Animation", default=False, update=_on_update)
    interpolation: bpy.props.EnumProperty(name="Interpolation", items=INTERPOLATION_ITEMS, default="BEZIER", update=_on_interpolation)
    animate_relief: bpy.props.BoolProperty(name="Animate Relief with Presets", default=True, update=_on_update)

    invert: bpy.props.BoolProperty(name="Invert", default=False, update=_on_update)
    grayscale: bpy.props.FloatProperty(name="Desaturate", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    hue: bpy.props.FloatProperty(name="Hue", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    saturation: bpy.props.FloatProperty(name="Saturation", min=0.0, max=2.0, default=1.0, subtype="FACTOR", update=_on_update)
    brightness: bpy.props.FloatProperty(name="Brightness", min=0.0, max=2.0, default=1.0, subtype="FACTOR", update=_on_update)
    contrast: bpy.props.FloatProperty(name="Contrast", min=0.0, max=2.0, default=1.0, subtype="FACTOR", update=_on_update)
    gamma: bpy.props.FloatProperty(name="Gamma / Midtones", min=0.2, max=4.0, default=1.0, update=_on_update)
    temperature: bpy.props.FloatProperty(name="Temperature", min=-1.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    tint: bpy.props.FloatProperty(name="Tint", min=-1.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    posterize: bpy.props.IntProperty(name="Posterize", min=0, max=16, default=0, update=_on_update)
    amount: bpy.props.FloatProperty(name="Amount", min=0.0, max=1.0, default=1.0, subtype="FACTOR", update=_on_update)

    scale: bpy.props.FloatProperty(name="Scale", min=0.05, max=16.0, default=1.0, update=_on_update)
    tiling_x: bpy.props.FloatProperty(name="Tiling X", min=0.05, max=50.0, default=1.0, update=_on_update)
    tiling_y: bpy.props.FloatProperty(name="Tiling Y", min=0.05, max=50.0, default=1.0, update=_on_update)
    rotation: bpy.props.FloatProperty(name="Rotation", min=-180.0, max=180.0, default=0.0, update=_on_update)
    offset_x: bpy.props.FloatProperty(name="Offset X", min=-4.0, max=4.0, default=0.0, subtype="FACTOR", update=_on_update)
    offset_y: bpy.props.FloatProperty(name="Offset Y", min=-4.0, max=4.0, default=0.0, subtype="FACTOR", update=_on_update)
    flip_x: bpy.props.BoolProperty(name="Flip X", default=False, update=_on_update)
    flip_y: bpy.props.BoolProperty(name="Flip Y", default=False, update=_on_update)

    relief_mode: bpy.props.EnumProperty(name="Relief Mode", items=RELIEF_MODE_ITEMS, default="BUMP", update=_on_update)
    relief_source: bpy.props.EnumProperty(name="Relief Source", items=RELIEF_SOURCE_ITEMS, default="IMAGE", update=_on_update)
    relief: bpy.props.FloatProperty(name="Relief", min=0.0, max=1.0, default=0.5, subtype="FACTOR", update=_on_update)
    depth: bpy.props.FloatProperty(name="Depth", min=0.0, max=2.0, default=0.5, subtype="FACTOR", update=_on_update)
    relief_invert: bpy.props.BoolProperty(name="Invert Relief", default=False, update=_on_update)
    detail: bpy.props.FloatProperty(name="Detail", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    detail_scale: bpy.props.FloatProperty(name="Detail Scale", min=0.5, max=40.0, default=8.0, update=_on_update)
    relief_speed: bpy.props.FloatProperty(name="Relief Speed", min=0.05, max=3.0, default=0.5, update=_on_update)
    relief_amplitude: bpy.props.FloatProperty(name="Relief Amplitude", min=0.0, max=1.0, default=0.5, subtype="FACTOR", update=_on_update)
    relief_phase: bpy.props.FloatProperty(name="Relief Phase", min=0.0, max=6.283, default=0.0, update=_on_update)
    subdivision_level: bpy.props.IntProperty(name="Subdivision Level", min=0, max=6, default=2, update=_on_update)

    roughness: bpy.props.FloatProperty(name="Roughness", min=0.0, max=1.0, default=0.5, subtype="FACTOR", update=_on_update)
    metallic: bpy.props.FloatProperty(name="Metallic", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    specular: bpy.props.FloatProperty(name="Specular", min=0.0, max=1.0, default=0.5, subtype="FACTOR", update=_on_update)
    ior: bpy.props.FloatProperty(name="IOR", min=1.0, max=3.0, default=1.5, update=_on_update)
    coat: bpy.props.FloatProperty(name="Coat", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    coat_roughness: bpy.props.FloatProperty(name="Coat Roughness", min=0.0, max=1.0, default=0.03, subtype="FACTOR", update=_on_update)
    sheen: bpy.props.FloatProperty(name="Sheen", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    sheen_roughness: bpy.props.FloatProperty(name="Sheen Roughness", min=0.0, max=1.0, default=0.5, subtype="FACTOR", update=_on_update)
    anisotropic: bpy.props.FloatProperty(name="Anisotropic", min=-1.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    subsurface: bpy.props.FloatProperty(name="Subsurface", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    transmission: bpy.props.FloatProperty(name="Transmission", min=0.0, max=1.0, default=0.0, subtype="FACTOR", update=_on_update)
    alpha: bpy.props.FloatProperty(name="Alpha", min=0.0, max=1.0, default=1.0, subtype="FACTOR", update=_on_update)
    normal_strength: bpy.props.FloatProperty(name="Normal Strength", min=0.0, max=3.0, default=1.0, update=_on_update)

    emission: bpy.props.FloatProperty(name="Glow", min=0.0, max=5.0, default=0.0, update=_on_update)
    glow_mask: bpy.props.BoolProperty(name="Glow From Image", default=False, update=_on_update)
    glow_color: bpy.props.FloatVectorProperty(
        name="Glow Tint", subtype="COLOR", size=4, min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0, 1.0), update=_on_update,
    )


class MOTIONTEXTURE_OT_apply(bpy.types.Operator):
    bl_idname = "motiontexture.apply"
    bl_label = "Apply to Selected"
    bl_description = "Build or refresh the animated material on the active mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        _apply(context, rebuild=False, obj=obj)
        self.report({"INFO"}, "Applied Motion Texture to %s" % obj.name)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_apply_all(bpy.types.Operator):
    bl_idname = "motiontexture.apply_all"
    bl_label = "Apply to All Selected"
    bl_description = "Copy the active object's motion setup to every selected mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        source = _settings(context)
        if source is None:
            self.report({"WARNING"}, "Select the source mesh first")
            return {"CANCELLED"}
        targets = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not targets:
            self.report({"WARNING"}, "No mesh objects are selected")
            return {"CANCELLED"}
        active = context.active_object
        for obj in targets:
            if obj != active:
                _copy_settings(source, _settings_for(obj))
            _apply(context, rebuild=False, obj=obj)
        self.report({"INFO"}, "Applied to %d mesh objects" % len(targets))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_rebuild(bpy.types.Operator):
    bl_idname = "motiontexture.rebuild"
    bl_label = "Rebuild Material"
    bl_description = "Rebuild the node graph from scratch. This clears existing animation"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        _clear_animation(obj)
        _apply(context, rebuild=True, obj=obj)
        self.report({"INFO"}, "Rebuilt material; animation cleared")
        return {"FINISHED"}


class MOTIONTEXTURE_OT_revert_still(bpy.types.Operator):
    bl_idname = "motiontexture.revert_still"
    bl_label = "Revert to Still"
    bl_description = "Remove animation and return to the static texture values"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        s = _settings_for(obj)
        _clear_animation(obj)
        _SUSPEND_UPDATES = True
        s.enable_animation = False
        _SUSPEND_UPDATES = False
        _apply(context, rebuild=False, obj=obj)
        self.report({"INFO"}, "Animation cleared")
        return {"FINISHED"}


class MOTIONTEXTURE_OT_play(bpy.types.Operator):
    bl_idname = "motiontexture.play"
    bl_label = "Play / Pause"
    bl_description = "Play or pause the scene timeline"

    def execute(self, context):
        try:
            bpy.ops.screen.animation_play()
        except Exception as exc:
            self.report({"WARNING"}, "Playback is not available: %s" % exc)
            return {"CANCELLED"}
        return {"FINISHED"}


class MOTIONTEXTURE_OT_frame_step(bpy.types.Operator):
    bl_idname = "motiontexture.frame_step"
    bl_label = "Step Frame"
    bl_description = "Move the scene one frame backward or forward"
    direction: bpy.props.IntProperty(default=1)

    def execute(self, context):
        context.scene.frame_set(context.scene.frame_current + self.direction)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_preview_render(bpy.types.Operator):
    bl_idname = "motiontexture.preview_render"
    bl_label = "Preview Render"
    bl_description = "Render the current frame to a temporary PNG"
    bl_options = {"REGISTER"}

    def execute(self, context):
        scene = context.scene
        path = os.path.join(bpy.app.tempdir, "motion_texture_preview.png")
        scene.render.filepath = path
        scene.render.image_settings.file_format = "PNG"
        try:
            bpy.ops.render.render(write_still=True)
        except Exception as exc:
            self.report({"ERROR"}, "Render failed: %s" % exc)
            return {"CANCELLED"}
        self.report({"INFO"}, "Preview rendered to %s" % path)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_key_all(bpy.types.Operator):
    bl_idname = "motiontexture.key_all"
    bl_label = "Key at Current Frame"
    bl_description = "Key the main texture, surface, and relief controls at the current frame"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        _apply(context, rebuild=False, obj=obj)
        if not _key_all(obj, context):
            self.report({"WARNING"}, "No Motion Texture material found")
            return {"CANCELLED"}
        s = _settings_for(obj)
        _SUSPEND_UPDATES = True
        s.enable_animation = True
        _SUSPEND_UPDATES = False
        self.report({"INFO"}, "Keyed at frame %d" % context.scene.frame_current)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_copy_still(bpy.types.Operator):
    bl_idname = "motiontexture.copy_still"
    bl_label = "Copy Still Values to Frame 1"
    bl_description = "Key the current values at frame 1"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        _apply(context, rebuild=False, obj=obj)
        if not _key_all(obj, context, frame=1):
            self.report({"WARNING"}, "No Motion Texture material found")
            return {"CANCELLED"}
        s = _settings_for(obj)
        _SUSPEND_UPDATES = True
        s.enable_animation = True
        _SUSPEND_UPDATES = False
        self.report({"INFO"}, "Copied still values to frame 1")
        return {"FINISHED"}


class MOTIONTEXTURE_OT_delete_key(bpy.types.Operator):
    bl_idname = "motiontexture.delete_key"
    bl_label = "Delete Key"
    bl_description = "Delete animation keys at the current frame"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        removed = _delete_key_at_frame(obj, context.scene.frame_current)
        self.report({"INFO"}, "Removed %d keyframes" % removed)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_clear_animation(bpy.types.Operator):
    bl_idname = "motiontexture.clear_animation"
    bl_label = "Clear Animation"
    bl_description = "Remove all animation from this object's material"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        _clear_animation(obj)
        s = _settings_for(obj)
        _SUSPEND_UPDATES = True
        s.enable_animation = False
        _SUSPEND_UPDATES = False
        _apply(context, rebuild=False, obj=obj)
        self.report({"INFO"}, "Animation cleared")
        return {"FINISHED"}


class MOTIONTEXTURE_OT_motion_preset(bpy.types.Operator):
    bl_idname = "motiontexture.motion_preset"
    bl_label = "Motion Preset"
    bl_description = "Create a ready-made motion animation"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(items=MOTION_PRESET_ITEMS)

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        s = _settings_for(obj)
        _apply(context, rebuild=False, obj=obj)
        mat = _find_material(obj)
        if mat is None:
            self.report({"WARNING"}, "No Motion Texture material found")
            return {"CANCELLED"}
        nt = mat.node_tree
        _clear_animation(obj)
        _SUSPEND_UPDATES = True
        s.enable_animation = True
        _SUSPEND_UPDATES = False
        start = max(1, context.scene.frame_start)
        end = max(start + 1, context.scene.frame_end)
        middle = int(round((start + end) * 0.5))
        mapping = nt.nodes["MT_Map"]
        motion_map = nt.nodes["MT_MotionMap"]
        bump = nt.nodes["MT_Bump"]
        displacement = nt.nodes["MT_Displace"]
        hsv = nt.nodes["MT_HueSat"]
        glow_mul = nt.nodes["MT_Glow_Mul"]
        speed = max(0.05, s.relief_speed)
        amplitude = max(0.0, s.relief_amplitude)
        mode = s.interpolation

        if self.preset == "SCROLL_X":
            _key_socket(mapping, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(mapping, "Location", end, (1.0, 0.0, 0.0))
            mode = "LINEAR"
            if s.animate_relief:
                _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
                _key_socket(motion_map, "Location", end, (speed, 0.0, 0.0))
        elif self.preset == "SCROLL_Y":
            _key_socket(mapping, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(mapping, "Location", end, (0.0, 1.0, 0.0))
            mode = "LINEAR"
            if s.animate_relief:
                _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
                _key_socket(motion_map, "Location", end, (0.0, speed, 0.0))
        elif self.preset == "DRIFT":
            _key_socket(mapping, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(mapping, "Location", end, (1.0, 0.5, 0.0))
            mode = "LINEAR"
            if s.animate_relief:
                _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
                _key_socket(motion_map, "Location", end, (speed, speed * 0.5, 0.0))
        elif self.preset == "PULSE":
            _key_socket(bump, "Strength", start, 0.15)
            _key_socket(bump, "Strength", middle, 0.15 + 0.85 * amplitude)
            _key_socket(bump, "Strength", end, 0.15)
            _key_socket(displacement, "Scale", start, 0.01)
            _key_socket(displacement, "Scale", middle, 0.01 + 0.25 * amplitude)
            _key_socket(displacement, "Scale", end, 0.01)
            mode = "BEZIER"
        elif self.preset == "BREATHE":
            _key_socket(mapping, "Scale", start, (1.0, 1.0, 1.0))
            _key_socket(mapping, "Scale", middle, (1.0 + 0.08 * amplitude, 1.0 + 0.08 * amplitude, 1.0))
            _key_socket(mapping, "Scale", end, (1.0, 1.0, 1.0))
            mode = "BEZIER"
        elif self.preset == "RIPPLE":
            _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(motion_map, "Location", end, (speed, 0.0, 0.0))
            _key_socket(bump, "Strength", start, 0.2)
            _key_socket(bump, "Strength", middle, 0.2 + 0.8 * amplitude)
            _key_socket(bump, "Strength", end, 0.2)
            mode = "BEZIER"
        elif self.preset == "FLICKER":
            values = (1.0, 0.55, 1.25, 0.75, 1.1, 0.6, 1.0, 0.8)
            span = max(1, end - start)
            for index, value in enumerate(values):
                frame = start + int(round(span * index / max(1, len(values) - 1)))
                _key_socket(hsv, "Value", frame, value)
                _key_socket(glow_mul, "Value", frame, value * 0.5)
            mode = "CONSTANT"
        elif self.preset == "STOP_MOTION":
            steps = 6
            for index in range(steps):
                frame = start + int(round((end - start) * index / max(1, steps - 1)))
                _key_socket(mapping, "Location", frame, (index / max(1, steps - 1), 0.0, 0.0))
            mode = "CONSTANT"

        _set_interpolation(_action_for(obj), mode)
        _add_cycles(_action_for(obj))
        _SUSPEND_UPDATES = True
        s.interpolation = mode
        _SUSPEND_UPDATES = False
        context.scene.frame_set(start)
        self.report({"INFO"}, "Applied %s motion" % self.preset)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_relief_motion(bpy.types.Operator):
    bl_idname = "motiontexture.relief_motion"
    bl_label = "Relief Motion"
    bl_description = "Animate the moving raised surface over the scene range"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(items=RELIEF_MOTION_ITEMS)

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        s = _settings_for(obj)
        _apply(context, rebuild=False, obj=obj)
        mat = _find_material(obj)
        if mat is None:
            self.report({"WARNING"}, "No Motion Texture material found")
            return {"CANCELLED"}
        nt = mat.node_tree
        _clear_animation(obj)
        _SUSPEND_UPDATES = True
        s.enable_animation = True
        _SUSPEND_UPDATES = False
        start = max(1, context.scene.frame_start)
        end = max(start + 1, context.scene.frame_end)
        middle = int(round((start + end) * 0.5))
        motion_map = nt.nodes["MT_MotionMap"]
        bump = nt.nodes["MT_Bump"]
        speed = max(0.05, s.relief_speed)
        amplitude = max(0.0, s.relief_amplitude)
        base = max(0.05, s.relief)
        phase = s.relief_phase

        if self.preset == "DRIFT":
            _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(motion_map, "Location", end, (speed, 0.0, 0.0))
            mode = "LINEAR"
        elif self.preset == "PULSE":
            _key_socket(bump, "Strength", start, base * 0.35)
            _key_socket(bump, "Strength", middle, base * 0.35 + amplitude * 0.9)
            _key_socket(bump, "Strength", end, base * 0.35)
            mode = "BEZIER"
        elif self.preset == "RIPPLE":
            _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(motion_map, "Location", end, (speed, 0.0, 0.0))
            _key_socket(bump, "Strength", start, base * 0.3)
            _key_socket(bump, "Strength", middle, base * 0.3 + amplitude)
            _key_socket(bump, "Strength", end, base * 0.3)
            mode = "BEZIER"
        else:
            _key_socket(motion_map, "Location", start, (0.0, 0.0, 0.0))
            _key_socket(motion_map, "Location", end, (speed, speed * 0.4, 0.0))
            mode = "LINEAR"

        _set_interpolation(_action_for(obj), mode)
        _add_cycles(_action_for(obj))
        _SUSPEND_UPDATES = True
        s.interpolation = mode
        _SUSPEND_UPDATES = False
        context.scene.frame_set(start)
        self.report({"INFO"}, "Applied %s relief motion" % self.preset)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_rotate(bpy.types.Operator):
    bl_idname = "motiontexture.rotate"
    bl_label = "Rotate Image"
    bl_description = "Nudge the image rotation by a fixed step"
    angle: bpy.props.FloatProperty(default=90.0)

    def execute(self, context):
        s = _settings(context)
        if s is None:
            return {"CANCELLED"}
        s.rotation = ((s.rotation + self.angle + 180.0) % 360.0) - 180.0
        return {"FINISHED"}


class MOTIONTEXTURE_OT_surface_preset(bpy.types.Operator):
    bl_idname = "motiontexture.surface_preset"
    bl_label = "Surface Preset"
    bl_description = "Apply a ready-made surface look"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(items=PRESET_ITEMS)

    def execute(self, context):
        s = _settings(context)
        if s is None:
            return {"CANCELLED"}
        values = SURFACE_PRESETS.get(self.preset)
        if not values:
            return {"CANCELLED"}
        global _SUSPEND_UPDATES
        previous = _SUSPEND_UPDATES
        _SUSPEND_UPDATES = True
        try:
            for key, value in values.items():
                if key != "label":
                    setattr(s, key, value)
        finally:
            _SUSPEND_UPDATES = previous
        _apply(context, rebuild=False, obj=context.active_object)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_reset_section(bpy.types.Operator):
    bl_idname = "motiontexture.reset_section"
    bl_label = "Reset Section"
    bl_description = "Reset a group of controls to their defaults"
    bl_options = {"REGISTER", "UNDO"}

    section: bpy.props.EnumProperty(items=(
        ("COLOR", "Color", ""),
        ("TRANSFORM", "Transform", ""),
        ("SURFACE", "Surface", ""),
        ("ANIMATION", "Animation", ""),
        ("ALL", "Everything", ""),
    ), default="ALL")

    def execute(self, context):
        obj = context.active_object
        s = _settings_for(obj)
        if s is None:
            return {"CANCELLED"}
        global _SUSPEND_UPDATES
        previous = _SUSPEND_UPDATES
        _SUSPEND_UPDATES = True
        try:
            for key in RESET_SECTIONS.get(self.section, ()):
                setattr(s, key, DEFAULTS[key])
            if self.section in {"ANIMATION", "ALL"}:
                s.enable_animation = False
                s.animate_relief = True
        finally:
            _SUSPEND_UPDATES = previous
        if self.section in {"ANIMATION", "ALL"}:
            _clear_animation(obj)
        _apply(context, rebuild=self.section == "ALL", obj=obj)
        return {"FINISHED"}


class MOTIONTEXTURE_MT_reset(bpy.types.Menu):
    bl_idname = "MOTIONTEXTURE_MT_reset"
    bl_label = "Reset"

    def draw(self, context):
        for key, label in (("COLOR", "Color"), ("TRANSFORM", "Transform"),
                           ("SURFACE", "Surface"), ("ANIMATION", "Animation"),
                           ("ALL", "Everything")):
            operator = self.layout.operator("motiontexture.reset_section", text=label)
            operator.section = key


class MOTIONTEXTURE_OT_open_still(bpy.types.Operator):
    bl_idname = "motiontexture.open_still"
    bl_label = "Open Still"
    bl_description = "Load a single image as the texture"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default=IMAGE_FILTER, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        ok, message = _load_source(context, self.filepath, "STILL")
        if not ok:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "Loaded still %s" % os.path.basename(self.filepath))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_open_sequence(bpy.types.Operator):
    bl_idname = "motiontexture.open_sequence"
    bl_label = "Open Image Sequence"
    bl_description = "Load a numbered image sequence. Pick any frame; the range is detected"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default=IMAGE_FILTER, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        ok, message = _load_source(context, self.filepath, "SEQUENCE")
        if not ok:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "Loaded sequence from %s" % os.path.basename(self.filepath))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_open_movie(bpy.types.Operator):
    bl_idname = "motiontexture.open_movie"
    bl_label = "Open Movie"
    bl_description = "Load a movie file as an animated texture"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default=MOVIE_FILTER, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        ok, message = _load_source(context, self.filepath, "MOVIE")
        if not ok:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "Loaded movie %s" % os.path.basename(self.filepath))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_refresh_source(bpy.types.Operator):
    bl_idname = "motiontexture.refresh_source"
    bl_label = "Refresh Source"
    bl_description = "Reload the source image from disk"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        s = _settings_for(obj)
        if s is None or s.image is None:
            self.report({"WARNING"}, "No source image to refresh")
            return {"CANCELLED"}
        try:
            s.image.reload()
        except Exception as exc:
            self.report({"ERROR"}, "Could not reload source: %s" % exc)
            return {"CANCELLED"}
        _apply(context, rebuild=False, obj=obj)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_clear_source(bpy.types.Operator):
    bl_idname = "motiontexture.clear_source"
    bl_label = "Clear Source"
    bl_description = "Remove the source image from this object"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = context.active_object
        s = _settings_for(obj)
        if s is None:
            return {"CANCELLED"}
        _SUSPEND_UPDATES = True
        s.image = None
        s.source_path = ""
        s.source_mode = "STILL"
        s.frame_start = 1
        s.frame_end = 1
        _SUSPEND_UPDATES = False
        _apply(context, rebuild=False, obj=obj)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_open_normal(bpy.types.Operator):
    bl_idname = "motiontexture.open_normal"
    bl_label = "Load Normal Map"
    bl_description = "Load a normal map image"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default=IMAGE_FILTER, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        s = _settings(context)
        if s is None:
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        try:
            image = bpy.data.images.load(self.filepath, check_existing=True)
        except Exception as exc:
            self.report({"ERROR"}, "Could not load normal map: %s" % exc)
            return {"CANCELLED"}
        try:
            image.colorspace_settings.name = "Non-Color"
        except Exception:
            pass
        s.normal_image = image
        _apply(context, rebuild=False, obj=context.active_object)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_drop_source(bpy.types.Operator):
    bl_idname = "motiontexture.drop_source"
    bl_label = "Motion Texture: Drop Source"
    bl_description = "Load a dragged-and-dropped image or movie as the texture"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", options={"SKIP_SAVE"})

    def execute(self, context):
        if not self.filepath:
            return {"CANCELLED"}
        extension = os.path.splitext(self.filepath)[1].lower()
        mode = "MOVIE" if extension.lstrip(".") in MOVIE_EXTENSIONS else "STILL"
        ok, message = _load_source(context, self.filepath, mode)
        if not ok:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "Loaded %s" % os.path.basename(self.filepath))
        return {"FINISHED"}


class MOTIONTEXTURE_FH_source_drop(bpy.types.FileHandler):
    bl_idname = "MOTIONTEXTURE_FH_source_drop"
    bl_label = "Motion Texture Source"
    bl_import_operator = "motiontexture.drop_source"
    bl_file_extensions = DROP_EXTENSIONS

    @classmethod
    def poll_drop(cls, context):
        area = getattr(context, "area", None)
        return area is not None and area.type in {"VIEW_3D", "IMAGE_EDITOR"}


class MOTIONTEXTURE_OT_save_preset(bpy.types.Operator):
    bl_idname = "motiontexture.save_preset"
    bl_label = "Save Motion Preset"
    bl_description = "Save the current source, motion, relief, and surface setup to disk"
    bl_options = {"REGISTER"}

    preset_name: bpy.props.StringProperty(name="Preset Name", default="My Motion")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        s = _settings(context)
        if s is None:
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        filename = _safe_filename(self.preset_name) + ".json"
        path = os.path.join(_preset_directory(), filename)
        try:
            _write_preset(path, s)
        except Exception as exc:
            self.report({"ERROR"}, "Could not save preset: %s" % exc)
            return {"CANCELLED"}
        self.report({"INFO"}, "Saved preset %s" % filename)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_load_preset(bpy.types.Operator):
    bl_idname = "motiontexture.load_preset"
    bl_label = "Load Motion Preset"
    bl_description = "Load a saved motion preset"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.StringProperty()

    def execute(self, context):
        ok, message = _apply_settings_file(context, self.preset)
        if not ok:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "Loaded preset %s" % os.path.basename(self.preset))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_delete_preset(bpy.types.Operator):
    bl_idname = "motiontexture.delete_preset"
    bl_label = "Delete Motion Preset"
    bl_description = "Delete a saved motion preset from disk"
    bl_options = {"REGISTER"}

    preset: bpy.props.StringProperty()

    def execute(self, context):
        try:
            os.remove(self.preset)
        except Exception as exc:
            self.report({"ERROR"}, "Could not delete preset: %s" % exc)
            return {"CANCELLED"}
        self.report({"INFO"}, "Deleted %s" % os.path.basename(self.preset))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_export_preset(bpy.types.Operator):
    bl_idname = "motiontexture.export_preset"
    bl_label = "Export Motion Preset"
    bl_description = "Export the current setup as a portable JSON preset"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        self.filepath = "motion_texture_preset.json"
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        s = _settings(context)
        if s is None:
            self.report({"WARNING"}, "Select a mesh object first")
            return {"CANCELLED"}
        path = self.filepath if self.filepath.lower().endswith(".json") else self.filepath + ".json"
        try:
            _write_preset(path, s)
        except Exception as exc:
            self.report({"ERROR"}, "Could not export preset: %s" % exc)
            return {"CANCELLED"}
        self.report({"INFO"}, "Exported %s" % path)
        return {"FINISHED"}


class MOTIONTEXTURE_OT_import_preset(bpy.types.Operator):
    bl_idname = "motiontexture.import_preset"
    bl_label = "Import Motion Preset"
    bl_description = "Import a portable JSON motion preset"
    bl_options = {"REGISTER", "UNDO"}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        ok, message = _apply_settings_file(context, self.filepath)
        if not ok:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, "Imported %s" % os.path.basename(self.filepath))
        return {"FINISHED"}


class MOTIONTEXTURE_OT_undo(bpy.types.Operator):
    bl_idname = "motiontexture.undo"
    bl_label = "Undo"
    bl_description = "Undo the last operation"

    def execute(self, context):
        try:
            bpy.ops.ed.undo()
        except Exception as exc:
            self.report({"WARNING"}, "Undo failed: %s" % exc)
            return {"CANCELLED"}
        return {"FINISHED"}


class MOTIONTEXTURE_OT_redo(bpy.types.Operator):
    bl_idname = "motiontexture.redo"
    bl_label = "Redo"
    bl_description = "Redo the last undone operation"

    def execute(self, context):
        try:
            bpy.ops.ed.redo()
        except Exception as exc:
            self.report({"WARNING"}, "Redo failed: %s" % exc)
            return {"CANCELLED"}
        return {"FINISHED"}


class MOTIONTEXTURE_MT_presets(bpy.types.Menu):
    bl_idname = "MOTIONTEXTURE_MT_presets"
    bl_label = "Load Motion Preset"

    def draw(self, context):
        files = _preset_files()
        if not files:
            self.layout.label(text="No saved presets")
            return
        for path in files:
            operator = self.layout.operator("motiontexture.load_preset", text=os.path.splitext(os.path.basename(path))[0])
            operator.preset = path


class MOTIONTEXTURE_MT_delete_preset(bpy.types.Menu):
    bl_idname = "MOTIONTEXTURE_MT_delete_preset"
    bl_label = "Delete Motion Preset"

    def draw(self, context):
        files = _preset_files()
        if not files:
            self.layout.label(text="No saved presets")
            return
        for path in files:
            operator = self.layout.operator("motiontexture.delete_preset", text=os.path.splitext(os.path.basename(path))[0])
            operator.preset = path


def _no_mesh(layout):
    layout.label(text="Select a mesh object", icon="INFO")


def _ui_apply(layout, s):
    row = layout.row(align=True)
    row.operator("motiontexture.apply", icon="PLAY")
    row.operator("motiontexture.rebuild", text="", icon="FILE_REFRESH")
    row = layout.row(align=True)
    row.operator("motiontexture.apply_all", icon="DUPLICATE")
    row.operator("motiontexture.revert_still", icon="LOOP_BACK")
    row = layout.row(align=True)
    row.operator("motiontexture.undo", text="Undo", icon="UNDO")
    row.operator("motiontexture.redo", text="Redo", icon="REDO")


def _ui_source(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.operator("motiontexture.open_still", icon="IMAGE_DATA")
    col.operator("motiontexture.open_sequence", icon="SEQUENCE")
    col.operator("motiontexture.open_movie", icon="FILE_MOVIE")
    if s.source_path:
        col.label(text=os.path.basename(s.source_path), icon="FILE")
    row = col.row(align=True)
    row.operator("motiontexture.refresh_source", icon="FILE_REFRESH")
    row.operator("motiontexture.clear_source", icon="X")
    col.prop(s, "source_mode")
    if s.source_mode in {"SEQUENCE", "MOVIE"}:
        row = col.row(align=True)
        row.prop(s, "frame_start")
        row.prop(s, "frame_end")
        col.prop(s, "frame_offset")
        col.prop(s, "loop_mode")
    col.prop(s, "fps")
    col.prop(s, "color_space")
    if s.image is not None:
        try:
            width, height = s.image.size
            col.label(text="%d x %d px" % (width, height), icon="INFO")
        except Exception:
            pass
    col.label(text="Drop an image or movie into the viewport", icon="IMPORT")


def _ui_playback(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    row = col.row(align=True)
    row.operator("motiontexture.play", text="Play / Pause", icon="PLAY")
    previous = row.operator("motiontexture.frame_step", text="", icon="TRIA_LEFT")
    previous.direction = -1
    following = row.operator("motiontexture.frame_step", text="", icon="TRIA_RIGHT")
    following.direction = 1
    col.prop(context.scene, "frame_current", text="Frame")
    row = col.row(align=True)
    row.prop(context.scene, "frame_start")
    row.prop(context.scene, "frame_end")
    col.prop(s, "preview_on_selected", toggle=True)
    col.operator("motiontexture.preview_render", icon="RENDER_STILL")


def _ui_animation(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.prop(s, "enable_animation", toggle=True)
    col.prop(s, "interpolation")
    col.prop(s, "animate_relief", toggle=True)
    col.label(text="Motion Presets", icon="PRESET")
    grid = col.grid_flow(columns=2, even_columns=True, align=True)
    for key, label, description in MOTION_PRESETS:
        operator = grid.operator("motiontexture.motion_preset", text=label)
        operator.preset = key
        try:
            operator.description = description
        except Exception:
            pass
    col.separator()
    row = col.row(align=True)
    row.operator("motiontexture.key_all", text="Key at Current Frame", icon="KEY_HLT")
    row.operator("motiontexture.delete_key", text="Delete Key", icon="KEY_DEHLT")
    col.operator("motiontexture.copy_still", text="Copy Still Values to Frame 1", icon="DUPLICATE")
    col.operator("motiontexture.clear_animation", text="Clear Animation", icon="X")
    if s.enable_animation:
        col.label(text="Animation is active", icon="ANIM")


def _ui_raised(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.prop(s, "relief_mode")
    col.prop(s, "relief_source")
    col.prop(s, "relief", slider=True)
    col.prop(s, "depth", slider=True)
    row = col.row(align=True)
    row.prop(s, "relief_invert", toggle=True)
    row.prop(s, "detail", slider=True)
    col.prop(s, "detail_scale")
    if s.relief_mode == "DISPLACEMENT":
        col.prop(s, "subdivision_level")
        col.label(text="Displacement is most reliable in Cycles", icon="INFO")
    col.separator()
    col.label(text="Moving Raised Texture", icon="MODIFIER")
    grid = col.grid_flow(columns=2, even_columns=True, align=True)
    for key, label, description in RELIEF_MOTION_ITEMS:
        operator = grid.operator("motiontexture.relief_motion", text=label)
        operator.preset = key
        try:
            operator.description = description
        except Exception:
            pass
    col.prop(s, "relief_speed")
    col.prop(s, "relief_amplitude", slider=True)
    col.prop(s, "relief_phase")
    col.separator()
    col.prop(s, "normal_image", text="Normal")
    col.operator("motiontexture.open_normal", text="Load Normal Map", icon="FILE_IMAGE")
    col.prop(s, "normal_strength", slider=True)


def _ui_surface(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.prop(s, "roughness", slider=True)
    col.prop(s, "metallic", slider=True)
    row = col.row(align=True)
    row.prop(s, "specular", slider=True)
    row.prop(s, "ior", slider=True)


def _ui_surface_advanced(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.prop(s, "coat", slider=True)
    col.prop(s, "coat_roughness", slider=True)
    row = col.row(align=True)
    row.prop(s, "sheen", slider=True)
    row.prop(s, "sheen_roughness", slider=True)
    col.prop(s, "anisotropic", slider=True)
    col.prop(s, "subsurface", slider=True)
    col.prop(s, "transmission", slider=True)
    col.prop(s, "alpha", slider=True)


def _ui_color(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    row = col.row(align=True)
    row.prop(s, "invert", toggle=True)
    row.prop(s, "grayscale")
    col.prop(s, "amount")
    col.separator()
    group = _get_hue_group_readonly()
    if group is not None:
        col.template_color_ramp(group.nodes["Hue"], "color_ramp", expand=True)
    col.prop(s, "hue", slider=True)
    col.prop(s, "saturation")
    col.prop(s, "brightness")
    col.prop(s, "contrast")
    col.prop(s, "gamma")
    row = col.row(align=True)
    row.prop(s, "temperature")
    row.prop(s, "tint")
    col.prop(s, "posterize")


def _ui_transform(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.prop(s, "scale")
    row = col.row(align=True)
    row.prop(s, "tiling_x")
    row.prop(s, "tiling_y")
    col.separator()
    col.prop(s, "rotation")
    row = col.row(align=True)
    back = row.operator("motiontexture.rotate", text="", icon="LOOP_BACK")
    back.angle = -90.0
    forward = row.operator("motiontexture.rotate", text="", icon="LOOP_FORWARDS")
    forward.angle = 90.0
    row = col.row(align=True)
    row.prop(s, "offset_x")
    row.prop(s, "offset_y")
    row = col.row(align=True)
    row.prop(s, "flip_x", toggle=True)
    row.prop(s, "flip_y", toggle=True)


def _ui_emission(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.prop(s, "emission", slider=True)
    col.prop(s, "glow_mask", toggle=True)
    col.prop(s, "glow_color", text="")


def _ui_presets(layout, context, s):
    if s is None:
        _no_mesh(layout)
        return
    col = layout.column()
    col.label(text="Surface Presets", icon="MATERIAL")
    grid = col.grid_flow(columns=3, even_columns=True, align=True)
    for key in SURFACE_PRESETS:
        operator = grid.operator("motiontexture.surface_preset", text=SURFACE_PRESETS[key]["label"])
        operator.preset = key
    col.separator()
    col.label(text="Saved Motion Presets", icon="PRESET")
    col.operator("motiontexture.save_preset", text="Save Motion Preset", icon="ADD")
    col.menu("MOTIONTEXTURE_MT_presets", text="Load Motion Preset", icon="PRESET")
    row = col.row(align=True)
    row.operator("motiontexture.import_preset", text="Import", icon="IMPORT")
    row.operator("motiontexture.export_preset", text="Export", icon="EXPORT")
    col.menu("MOTIONTEXTURE_MT_delete_preset", text="Delete Motion Preset", icon="TRASH")
    col.separator()
    col.menu("MOTIONTEXTURE_MT_reset", text="Reset", icon="LOOP_BACK")


class MOTIONTEXTURE_PT_main(bpy.types.Panel):
    bl_label = "Motion Texture"
    bl_idname = "MOTIONTEXTURE_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Motion Texture"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        s = _settings(context)
        if s is None:
            layout.label(text="Select a mesh object", icon="INFO")
            return
        layout.label(text="Object: %s" % obj.name, icon="OBJECT_DATAMODE")
        if s.image is not None:
            layout.label(text=s.image.name, icon="IMAGE_DATA")
        if s.enable_animation:
            layout.label(text="Animated", icon="ANIM")
        _ui_apply(layout, s)


def _make_section(name, label, icon, order, draw_fn):
    def draw(self, context):
        draw_fn(self.layout, context, _settings(context))
    return type("MOTIONTEXTURE_PT_%s" % name, (bpy.types.Panel,), {
        "bl_label": label,
        "bl_idname": "MOTIONTEXTURE_PT_%s" % name,
        "bl_parent_id": "MOTIONTEXTURE_PT_main",
        "bl_space_type": "VIEW_3D",
        "bl_region_type": "UI",
        "bl_options": {"DEFAULT_CLOSED"},
        "bl_order": order,
        "draw": draw,
    })


MOTIONTEXTURE_PT_source = _make_section("source", "Source", "IMAGE_DATA", 0, _ui_source)
MOTIONTEXTURE_PT_playback = _make_section("playback", "Playback", "PLAY", 1, _ui_playback)
MOTIONTEXTURE_PT_animation = _make_section("animation", "Animate Texture", "ANIM", 2, _ui_animation)
MOTIONTEXTURE_PT_raised = _make_section("raised", "Raised Surface", "MODIFIER", 3, _ui_raised)
MOTIONTEXTURE_PT_colour = _make_section("colour", "Color", "COLOR", 4, _ui_color)
MOTIONTEXTURE_PT_transform = _make_section("transform", "Transform", "UV", 5, _ui_transform)
MOTIONTEXTURE_PT_surface = _make_section("surface", "Surface", "MATERIAL", 6, _ui_surface)
MOTIONTEXTURE_PT_surface_advanced = _make_section("surface_advanced", "Surface Advanced", "SHADERFX", 7, _ui_surface_advanced)
MOTIONTEXTURE_PT_emission = _make_section("emission", "Emission", "LIGHT", 8, _ui_emission)
MOTIONTEXTURE_PT_presets = _make_section("presets", "Presets", "PRESET", 9, _ui_presets)


_classes = (
    MotionTextureSettings,
    MOTIONTEXTURE_OT_apply,
    MOTIONTEXTURE_OT_apply_all,
    MOTIONTEXTURE_OT_rebuild,
    MOTIONTEXTURE_OT_revert_still,
    MOTIONTEXTURE_OT_play,
    MOTIONTEXTURE_OT_frame_step,
    MOTIONTEXTURE_OT_preview_render,
    MOTIONTEXTURE_OT_key_all,
    MOTIONTEXTURE_OT_copy_still,
    MOTIONTEXTURE_OT_delete_key,
    MOTIONTEXTURE_OT_clear_animation,
    MOTIONTEXTURE_OT_motion_preset,
    MOTIONTEXTURE_OT_relief_motion,
    MOTIONTEXTURE_OT_rotate,
    MOTIONTEXTURE_OT_surface_preset,
    MOTIONTEXTURE_OT_reset_section,
    MOTIONTEXTURE_MT_reset,
    MOTIONTEXTURE_OT_open_still,
    MOTIONTEXTURE_OT_open_sequence,
    MOTIONTEXTURE_OT_open_movie,
    MOTIONTEXTURE_OT_refresh_source,
    MOTIONTEXTURE_OT_clear_source,
    MOTIONTEXTURE_OT_open_normal,
    MOTIONTEXTURE_OT_drop_source,
    MOTIONTEXTURE_FH_source_drop,
    MOTIONTEXTURE_OT_save_preset,
    MOTIONTEXTURE_OT_load_preset,
    MOTIONTEXTURE_OT_delete_preset,
    MOTIONTEXTURE_OT_export_preset,
    MOTIONTEXTURE_OT_import_preset,
    MOTIONTEXTURE_OT_undo,
    MOTIONTEXTURE_OT_redo,
    MOTIONTEXTURE_MT_presets,
    MOTIONTEXTURE_MT_delete_preset,
    MOTIONTEXTURE_PT_main,
    MOTIONTEXTURE_PT_source,
    MOTIONTEXTURE_PT_playback,
    MOTIONTEXTURE_PT_animation,
    MOTIONTEXTURE_PT_raised,
    MOTIONTEXTURE_PT_colour,
    MOTIONTEXTURE_PT_transform,
    MOTIONTEXTURE_PT_surface,
    MOTIONTEXTURE_PT_surface_advanced,
    MOTIONTEXTURE_PT_emission,
    MOTIONTEXTURE_PT_presets,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Object.motion_texture = bpy.props.PointerProperty(type=MotionTextureSettings)


def unregister():
    _remove_hue_group()
    if hasattr(bpy.types.Object, "motion_texture"):
        del bpy.types.Object.motion_texture
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
