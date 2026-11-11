bl_info = {
    "name": "Any Kitchen Mask",
    "author": "Kitchen Prompt Generator project",
    "version": (3, 0, 0),
    "blender": (3, 6, 0),
    "location": "3D Viewport > Sidebar (N) > Any Kitchen Mask",
    "description": "Assign kitchen objects to mask groups and export a flat-colour material-ID mask (PNG) plus a JSON legend",
    "category": "Render",
}
# Install: Edit > Preferences > Add-ons > Install... > pick this file > enable "Any Kitchen Mask".
# Nothing renders on load. Assignments (custom property "akm_group" on each object) and the 16 colours are saved in the .blend.
# V3.0: schema-3 JSON. Editable component names (keys never change), custom components (own colour with CIEDE2000 >= 5 to every other
#       mask colour, name patterns, delete button), "Mask All Scene" (register components hidden behind other geometry; absent/disabled
#       components are never exported).
# V2.9: unique canonical colour names (color_name in the JSON), optional black wireframe outlines (Freestyle),
#       unassigned/background colour moved from black to white so black only means an outline, labels aligned with the dashboard.
# V2.7: Cabinet Hardware is handles only; Pendant Lights are a separate group/colour next to Ceiling Spotlights ("Lighting Fixtures").
# Output: <blendname>_mask.png and <blendname>_mask.json next to the saved .blend (overwritten on each export).

import bpy, json, os, re, math, uuid, fnmatch
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty, StringProperty, CollectionProperty
from bpy.app.handlers import persistent

VERSION = "3.0.0"
SCHEMA = 3
PROP, MARK, SNAP = "akm_group", "akm_orig_color", "akm_restore"
UNMATCHED = "#FFFFFF"   # unassigned objects + background
OUTLINE = "#000000"     # wireframe outlines (reserved, never a component colour)
RENDERABLE = {"MESH", "CURVE", "SURFACE", "META", "FONT", "CURVES", "VOLUME", "POINTCLOUD"}

# key: (label, default sRGB hex, [fallback regex patterns matched against object / collection / material names])
COMPONENTS = {
    "base":     ("Base Cabinets & Plinth",            "#FF0000", [r"base", r"plinth"]),
    "upper":    ("Upper Cabinets",                    "#0000FF", [r"upper", r"wall.?cab"]),
    "transom":  ("Transom Cabinets",                  "#FFFF00", [r"transom"]),
    "terminal": ("Terminal & Corner Pantry Cabinets", "#FF8000", [r"terminal", r"pantry", r"corner"]),
    "island":   ("Island Back Face",                  "#00FF00", [r"island.*(back|face)", r"island"]),
    "itop":     ("Island Countertop",                 "#8000FF", [r"island.*(top|counter)"]),
    "counter":  ("Main Kitchen Countertop & Backsplash", "#00FFFF", [r"counter", r"worktop", r"backsplash", r"splash"]),
    # Handles only (no light words). Catches e.g. kitchen_door_1_panel0_handle, door_1_leaf_handle.004, _door_*_handle.
    "hw":       ("Cabinet Hardware",                  "#FF00FF", [r"handle", r"(?<![a-z])pulls?(?![a-z])", r"(?<![a-z])knobs?(?![a-z])", r"_door_.*_handle"]),
    "wall":     ("Wall Surface",                      "#808080", [r"wall", r"paint"]),
    # Catches door_glass and door_glass_1_panel0_frame (steel-door glass is claimed earlier by the steel rule).
    "glass":    ("Glass-Display Cabinets",            "#FF0080", [r"door.?glass", r"glass.?(disp|cab)", r"display"]),
    "floor":    ("Flooring",                          "#804000", [r"floor"]),
    "plumb":    ("Plumbing Fixtures",                 "#00FF80", [r"sink", r"faucet", r"\btap\b", r"basin"]),
    "door":     ("Steel Doors",                       "#4040FF", [r"door", r"frame"]),
    # Lighting Fixtures umbrella: Ceiling Spotlights and Pendant Lights, each with its own colour.
    "spot":     ("Ceiling Spotlights",                "#FFFF80", [r"spot", r"downlight", r"ceiling"]),
    "pendant":  ("Pendant Lights",                    "#C080FF", [r"pendant", r"light.?fixture", r"(?<![a-z])lamps?(?![a-z])"]),
    "accent":   ("Light Accents",                      "#80FF00", [r"(?<![a-z])led(?![a-z])", r"accent", r"strip.?light", r"under.?cab", r"hood.?light", r"shelf.?light"]),
}
LIGHTING_GROUP = ("Lighting Fixtures", ["spot", "pendant"])
# "@steel" is a pseudo-step: object/collection names containing "steel" (or a steel door/frame material) go to Steel Doors,
# after plumbing (stainless-steel sinks) but before everything else. Handles then glass then the cabinet runs follow.
ORDER = ["pendant", "accent", "spot", "plumb", "@steel", "hw", "glass", "itop", "terminal", "transom", "upper", "base", "island", "counter", "door", "floor", "wall"]
STEEL_MAT = re.compile(r"steel.*(door|frame)|(door|frame).*steel")

# Every scene setting that can change a pixel. Snapshotted before export, restored afterwards.
LOCK = {
    "render.engine": "BLENDER_WORKBENCH", "render.resolution_percentage": 100, "render.film_transparent": False,
    "render.use_file_extension": True, "render.dither_intensity": 0.0, "render.use_compositing": False,
    "render.use_sequencer": False, "render.use_stamp": False,
    "render.image_settings.file_format": "PNG", "render.image_settings.color_mode": "RGB",
    "render.image_settings.color_depth": "8", "render.image_settings.color_management": "FOLLOW_SCENE",
    "view_settings.view_transform": "Standard", "view_settings.look": "None", "view_settings.exposure": 0.0,
    "view_settings.gamma": 1.0, "view_settings.use_curve_mapping": False, "display_settings.display_device": "sRGB",
    "display.render_aa": "OFF", "display.shading.light": "FLAT", "display.shading.color_type": "OBJECT",
    "display.shading.show_object_outline": False, "display.shading.show_cavity": False,
    "display.shading.show_specular_highlight": False, "display.shading.show_shadows": False,
    "display.shading.show_xray": False,
}
CRITICAL = {"render.engine", "view_settings.view_transform", "display.render_aa", "display.shading.color_type", "display.shading.light"}
SNAP_PATHS = list(LOCK) + ["render.filepath", "render.use_freestyle", "render.line_thickness_mode", "render.line_thickness"]
OUTLINE_LS = "AKM_outline"


# ---------------------------------------------------------------- colour helpers
def hex_to_srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def rgb_to_hex(c):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(v * 255)))) for v in c[:3])

def hex_ints(h):
    return tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- canonical colour names (unique per export)
NAME_PALETTE = [  # the 16 defaults map to themselves exactly; the rest name custom colours
    ("red", "#FF0000"), ("blue", "#0000FF"), ("yellow", "#FFFF00"), ("orange", "#FF8000"), ("green", "#00FF00"),
    ("violet", "#8000FF"), ("cyan", "#00FFFF"), ("magenta", "#FF00FF"), ("mid grey", "#808080"), ("rose", "#FF0080"),
    ("brown", "#804000"), ("spring green", "#00FF80"), ("indigo", "#4040FF"), ("pale yellow", "#FFFF80"),
    ("lavender", "#C080FF"), ("chartreuse", "#80FF00"),
    ("crimson", "#DC143C"), ("maroon", "#800000"), ("coral", "#FF7F50"), ("gold", "#FFD700"), ("olive", "#808000"),
    ("forest green", "#228B22"), ("teal", "#008080"), ("turquoise", "#40E0D0"), ("sky blue", "#87CEEB"),
    ("navy", "#000080"), ("purple", "#800080"), ("pink", "#FFC0CB"), ("peach", "#FFDAB9"), ("tan", "#D2B48C"),
    ("light grey", "#C0C0C0"), ("dark grey", "#404040"), ("charcoal", "#36454F"), ("slate blue", "#6A5ACD"),
    ("steel blue", "#4682B4"), ("mint", "#98FF98"), ("salmon", "#FA8072"), ("khaki", "#C3B091"), ("plum", "#DDA0DD"),
    ("burgundy", "#800020"),
]
_CANDS = None

def _lab(h):
    r, g, b = (srgb_to_linear(v) for v in hex_to_srgb(h))
    x, y, z = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, 0.2126 * r + 0.7152 * g + 0.0722 * b, (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    f = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))

def _dist(a, b):
    return sum((p - q) ** 2 for p, q in zip(a, b)) ** 0.5

def _candidates():
    global _CANDS
    if _CANDS is None:
        c = []
        for n, h in NAME_PALETTE:
            c.append((n, h))
            if not n.startswith(("light", "dark", "pale", "mid")):
                rgb = hex_to_srgb(h)
                c.append(("light " + n, rgb_to_hex(tuple(v + (1 - v) * 0.35 for v in rgb))))
                c.append(("dark " + n, rgb_to_hex(tuple(v * 0.65 for v in rgb))))
        _CANDS = [(n, h, _lab(h)) for n, h in c]
    return _CANDS

def assign_names(hx):
    """One unique canonical name per distinct colour (closest unused name in CIELAB; closest matches claim names first).
    Components that deliberately share a colour share its name."""
    cand = _candidates()
    uniq = sorted(set(hx.values()))
    labs = {h: _lab(h) for h in uniq}
    ranked = sorted(uniq, key=lambda h: min(_dist(labs[h], c[2]) for c in cand))
    used, by_hex = set(), {}
    for h in ranked:
        for n, _, l in sorted(cand, key=lambda c: _dist(labs[h], c[2])):
            if n not in used:
                used.add(n)
                by_hex[h] = n
                break
    return {k: by_hex[h] for k, h in hx.items()}


# ---------------------------------------------------------------- V3 component model (keys are permanent, labels are display text)
DE_MIN = 5.0  # minimum CIEDE2000 between a custom colour and every other mask colour (same metric as the dashboard)

def _de2000(l1, l2):
    L1, a1, b1 = l1
    L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    A1, A2 = (1 + G) * a1, (1 + G) * a2
    P1, P2 = math.hypot(A1, b1), math.hypot(A2, b2)

    def hp(b, a):
        if not b and not a:
            return 0.0
        h = math.degrees(math.atan2(b, a))
        return h + 360 if h < 0 else h
    h1, h2 = hp(b1, A1), hp(b2, A2)
    dL, dC, dh = L2 - L1, P2 - P1, 0.0
    if P1 * P2:
        dh = h2 - h1
        if dh > 180:
            dh -= 360
        if dh < -180:
            dh += 360
    dH = 2 * math.sqrt(P1 * P2) * math.sin(math.radians(dh / 2))
    Lb, Pb, hb = (L1 + L2) / 2, (P1 + P2) / 2, h1 + h2
    if P1 * P2:
        hb = (h1 + h2 + (360 if h1 + h2 < 360 else -360)) / 2 if abs(h1 - h2) > 180 else (h1 + h2) / 2
    r = math.radians
    T = 1 - .17 * math.cos(r(hb - 30)) + .24 * math.cos(r(2 * hb)) + .32 * math.cos(r(3 * hb + 6)) - .2 * math.cos(r(4 * hb - 63))
    SL = 1 + .015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2)
    SC, SH = 1 + .045 * Pb, 1 + .015 * Pb * T
    RT = -2 * math.sqrt(Pb ** 7 / (Pb ** 7 + 25 ** 7)) * math.sin(r(60 * math.exp(-(((hb - 275) / 25) ** 2))))
    return math.sqrt(max(0.0, (dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH)))

def de_hex(a, b):
    return _de2000(_lab(a), _lab(b))

def custom_keys(s):
    return [it.key for it in s.custom]

def all_keys(s):
    return list(COMPONENTS) + custom_keys(s)

def label_of(s, k):
    if k in COMPONENTS:
        return getattr(s, "l_" + k, "") or COMPONENTS[k][0]
    for it in s.custom:
        if it.key == k:
            return it.label or "Custom"
    return k

def color_hex(s, k):
    if k in COMPONENTS:
        return rgb_to_hex(getattr(s, "c_" + k))
    for it in s.custom:
        if it.key == k:
            return rgb_to_hex(it.color)
    return UNMATCHED

def valid_key(s, k):
    return isinstance(k, str) and (k in COMPONENTS or k in custom_keys(s))

def active_key(s):
    g = s.active_group
    return g if valid_key(s, g) else "base"

def _clean_label(raw, default):
    return " ".join(str(raw or "").split())[:80] or default

def _unique_label(s, key, text):
    taken = {label_of(s, k).strip().lower() for k in all_keys(s) if k != key}
    if text.lower() not in taken:
        return text
    n = 2
    while ("%s (%d)" % (text, n)).lower() in taken:
        n += 1
    return "%s (%d)" % (text, n)

_GRID = None

def allocate_color(s):
    """Deterministic free sRGB slot: the grid colour farthest (CIEDE2000) from every reserved/used mask colour, or None if none reaches DE_MIN."""
    global _GRID
    if _GRID is None:
        v = range(0, 256, 17)
        _GRID = [("#%02X%02X%02X" % (r, g, b), _lab("#%02X%02X%02X" % (r, g, b))) for r in v for g in v for b in v]
    rl = [_lab(h) for h in [UNMATCHED, OUTLINE] + [color_hex(s, k) for k in all_keys(s)]]
    pool = sorted(((min(_dist(lb, x) for x in rl), h, lb) for h, lb in _GRID), key=lambda t: (-t[0], t[1]))
    best = None
    for _, h, lb in pool[:96]:
        d = min(_de2000(lb, x) for x in rl)
        if best is None or d > best[0] + 1e-9:
            best = (d, h)
    return best[1] if best and best[0] >= DE_MIN else None

def _new_key(s):
    used = set(custom_keys(s))
    while True:
        k = "cx_" + uuid.uuid4().hex[:8]
        if k not in used:
            return k

def _split_patterns(text):
    return [p.strip().lower() for p in re.split(r"[,;\n]+", text or "") if p.strip()]

def _pat_hit(pat, names):
    if any(ch in pat for ch in "*?["):
        return any(fnmatch.fnmatchcase(n, pat) for n in names)
    return any(pat in n for n in names)

def custom_group(ob, s):
    names = [ob.name.lower()] + [c.name.lower() for c in ob.users_collection]
    for it in s.custom:
        if any(_pat_hit(p, names) for p in _split_patterns(it.patterns)):
            return it.key
    return None

def _enabled_collections(vl):
    ok = set()
    def walk(lc, parent_ok):
        on = parent_ok and not lc.exclude and not lc.collection.hide_render
        if on:
            ok.add(lc.collection.as_pointer())
        for ch in lc.children:
            walk(ch, on)
    walk(vl.layer_collection, True)
    return ok

def _render_enabled(ob, ok):
    return (not ob.hide_render) and any(c.as_pointer() in ok for c in ob.users_collection)


# ---------------------------------------------------------------- assignment logic
def auto_group(ob, s=None):
    if s is not None:
        k = custom_group(ob, s)  # explicit user patterns beat the built-in fallbacks
        if k:
            return k
    own = " ".join([ob.name] + [c.name for c in ob.users_collection]).lower()
    mats = " ".join(s.material.name for s in ob.material_slots if s.material).lower()
    text = own + " " + mats
    for k in ORDER:
        if k == "@steel":
            if "steel" in own or STEEL_MAT.search(mats):
                return "door"
            continue
        if any(re.search(p, text) for p in COMPONENTS[k][2]):
            return k
    return None

def group_of(ob, s=None):
    """Manual assignment (single-valued custom property) always beats the name-matching fallback."""
    g = ob.get(PROP)
    if isinstance(g, str) and (g in COMPONENTS or (s is not None and g in custom_keys(s))):
        return g, "manual"
    return auto_group(ob, s), "auto"

def check_colors(s):
    ks = all_keys(s)
    cust = set(custom_keys(s))
    hx = {k: color_hex(s, k) for k in ks}
    errs, warns = [], []
    for k in ks:
        for res, why in ((UNMATCHED, "unassigned objects and the background"), (OUTLINE, "wireframe outlines")):
            if hx[k] == res:
                errs.append(f"'{label_of(s, k)}' uses {res}, which is reserved for {why}.")
            elif k in cust and de_hex(hx[k], res) < DE_MIN:
                errs.append(f"'{label_of(s, k)}' ({hx[k]}) is too close to {res} (reserved for {why}).")
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            a, b = hex_ints(hx[ks[i]]), hex_ints(hx[ks[j]])
            la, lb = label_of(s, ks[i]), label_of(s, ks[j])
            if a == b:
                warns.append(f"'{la}' and '{lb}' share {hx[ks[i]]} (merged on purpose?).")
            elif (ks[i] in cust or ks[j] in cust) and de_hex(hx[ks[i]], hx[ks[j]]) < DE_MIN:
                errs.append(f"'{la}' and '{lb}' are too close in colour (CIEDE2000 < {DE_MIN:g}: {hx[ks[i]]} / {hx[ks[j]]}).")
            elif max(abs(x - y) for x, y in zip(a, b)) < 6:
                warns.append(f"'{la}' and '{lb}' are nearly identical ({hx[ks[i]]} / {hx[ks[j]]}).")
    return hx, errs, warns


# ---------------------------------------------------------------- scene state snapshot / lock / restore
def _owner(sc, path):
    *parts, attr = path.split(".")
    o = sc
    for p in parts:
        o = getattr(o, p)
    return o, attr

def snapshot(sc):
    d = {}
    for p in SNAP_PATHS:
        try:
            o, a = _owner(sc, p)
            d[p] = getattr(o, a)
        except Exception:
            pass
    return d

def apply_settings(sc, d):
    for p, v in d.items():
        try:
            o, a = _owner(sc, p)
            setattr(o, a, v)
        except Exception:
            pass

def lock_settings(sc):
    """Force the flat-colour pipeline; return the paths that did not take the requested value."""
    bad = []
    for p, v in LOCK.items():
        try:
            o, a = _owner(sc, p)
            setattr(o, a, v)
            now = getattr(o, a)
            if (abs(now - v) > 1e-6) if isinstance(v, float) else (now != v):
                bad.append(p)
        except Exception:
            bad.append(p)
    return bad

def recover():
    """Undo any half-finished export (object colours, scene settings, temp world)."""
    for ob in bpy.data.objects:
        if MARK in ob:
            try:
                ob.color = tuple(ob[MARK])
                del ob[MARK]
            except Exception:
                pass
    for sc in bpy.data.scenes:
        if SNAP in sc:
            try:
                d = json.loads(sc[SNAP])
                apply_settings(sc, d.get("settings", {}))
                for vl in sc.view_layers:
                    fs = vl.freestyle_settings
                    for ls in [l for l in fs.linesets if l.name == OUTLINE_LS]:
                        st = ls.linestyle
                        fs.linesets.remove(ls)
                        if st is not None and st.users == 0:
                            bpy.data.linestyles.remove(st)
                    vd = d.get("view_layers", {}).get(vl.name)
                    if vd:
                        vl.use_freestyle = vd["use"]
                        for l in fs.linesets:
                            if l.name in vd["show"]:
                                l.show_render = vd["show"][l.name]
                sc.world = bpy.data.worlds.get(d.get("world") or "")
                del sc[SNAP]
            except Exception:
                pass
    for w in list(bpy.data.worlds):
        if w.name.startswith("AKM_tmp") and w.users == 0:
            bpy.data.worlds.remove(w)

@persistent
def _on_load(_):
    recover()


# ---------------------------------------------------------------- export
def _materials():
    out = []
    for m in bpy.data.materials:
        e = {"name": m.name}
        try:
            n = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes and m.node_tree else None
            if n:
                e["base_color_linear"] = [round(v, 4) for v in n.inputs["Base Color"].default_value[:3]]
                e["roughness"] = round(n.inputs["Roughness"].default_value, 3)
        except Exception:
            pass
        out.append(e)
    return out

def outline_begin(vl):
    """Add a temporary black Freestyle line set (other line sets are switched off for the render). Returns restore info."""
    fs = vl.freestyle_settings
    info = {"vl": vl, "use": vl.use_freestyle, "show": [(ls, ls.show_render) for ls in fs.linesets], "ls": None, "style": None}
    try:
        for ls, _ in info["show"]:
            ls.show_render = False
        vl.use_freestyle = True
        ls = fs.linesets.new(OUTLINE_LS)
        info["ls"] = ls
        ls.select_silhouette = True
        ls.select_border = True
        ls.select_crease = True
        ls.select_by_visibility = True
        ls.visibility = "VISIBLE"
        info["style"] = ls.linestyle
        ls.linestyle.color = (0.0, 0.0, 0.0)
        ls.linestyle.thickness = 1.5
    except Exception:
        outline_end(info)
        raise
    return info

def outline_end(info):
    if not info:
        return
    try:
        if info["ls"] is not None:
            info["vl"].freestyle_settings.linesets.remove(info["ls"])
        st = info["style"]
        if st is not None and st.users == 0:
            bpy.data.linestyles.remove(st)
    except Exception:
        pass
    for ls, show in info["show"]:
        try:
            ls.show_render = show
        except Exception:
            pass
    try:
        info["vl"].use_freestyle = info["use"]
    except Exception:
        pass


def verify_png(path, key_hex, outlines=False):
    """Read the PNG back and report pixels that are not exactly a legend colour, the unmatched colour or (if drawn) the outline colour."""
    try:
        import numpy as np
    except ImportError:
        return {"skipped": "numpy not available"}
    img = None
    try:
        img = bpy.data.images.load(path, check_existing=False)
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        arr = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(arr)
        px = np.rint(arr.reshape(-1, 4)[:, :3] * 255).astype(np.uint32)
        vals, counts = np.unique((px[:, 0] << 16) | (px[:, 1] << 8) | px[:, 2], return_counts=True)
        found = {"#%06X" % int(v): int(c) for v, c in zip(vals, counts)}
        expected = set(key_hex.values()) | {UNMATCHED} | ({OUTLINE} if outlines else set())
        stray = sum(c for k, c in found.items() if k not in expected)
        top = dict(sorted(found.items(), key=lambda kv: -kv[1])[:40])
        return {"size": [int(w), int(h)], "unexpected_pixel_fraction": round(stray / float(w * h), 6), "colours_found": top,
                "pixels_by_component": {k: found.get(h, 0) for k, h in key_hex.items()},
                "outline_pixels": found.get(OUTLINE, 0) if outlines else None}
    except Exception as e:
        return {"skipped": str(e)}
    finally:
        if img is not None:
            try:
                bpy.data.images.remove(img)
            except Exception:
                pass

def run_export(context, sc, hx):
    recover()  # clear leftovers from an earlier interrupted run
    st = sc.akm
    keys, cust = all_keys(st), set(custom_keys(st))
    mask_all = bool(st.mask_all)
    blend = bpy.data.filepath
    base = os.path.join(os.path.dirname(blend), os.path.splitext(os.path.basename(blend))[0] + "_mask")
    png, js = base + ".png", base + ".json"
    prefs = context.preferences.view
    snap, world, old_disp = snapshot(sc), sc.world, prefs.render_display_type
    vl = context.view_layer
    wf = bool(getattr(sc.akm, "wireframe", False))
    outline, outline_err = None, ""
    originals, legend, assigned_manual, unassigned, skipped = {}, {k: [] for k in keys}, 0, [], []
    tmp_world, summary = None, {}
    try:
        sc[SNAP] = json.dumps({"settings": snap, "world": world.name if world else None,
                               "view_layers": {vl.name: {"use": vl.use_freestyle, "show": {l.name: l.show_render for l in vl.freestyle_settings.linesets}}}})  # crash-recovery marker
        ok_colls = _enabled_collections(vl)  # objects hidden from render, or in excluded / render-disabled collections, do not exist for the mask
        for ob in [o for o in context.view_layer.objects if o.type in RENDERABLE and _render_enabled(o, ok_colls)]:
            try:
                orig = tuple(ob.color)
                ob[MARK] = list(orig)
                originals[ob] = orig
            except Exception:  # e.g. linked library data
                skipped.append(ob.name)
        for ob in originals:
            k, how = group_of(ob, st)
            if k:
                legend[k].append(ob.name)
                assigned_manual += how == "manual"
                c = hex_to_srgb(hx[k])
            else:
                unassigned.append(ob.name)
                c = hex_to_srgb(UNMATCHED)
            ob.color = tuple(srgb_to_linear(v) for v in c) + (1.0,)
        bad = lock_settings(sc)
        if CRITICAL & set(bad):
            raise RuntimeError("Could not set required render settings: " + ", ".join(sorted(CRITICAL & set(bad))))
        sc.render.use_freestyle = wf
        if wf:
            try:
                sc.render.line_thickness_mode = "ABSOLUTE"
                sc.render.line_thickness = 1.5
                outline = outline_begin(vl)
            except Exception as e:
                outline, outline_err = None, str(e)
                sc.render.use_freestyle = False
        tmp_world = bpy.data.worlds.new("AKM_tmp")
        tmp_world.color = (1.0, 1.0, 1.0)
        sc.world = tmp_world
        sc.render.filepath = base
        prefs.render_display_type = "NONE"
        bpy.ops.render.render(write_still=True)
        if not os.path.exists(png):
            raise RuntimeError("Render finished but no PNG was written: " + png)
        key_hex = {k: hx[k] for k in keys if legend[k]}
        ver = verify_png(png, key_hex, outline is not None)
        names = assign_names(hx)
        pbc = ver.get("pixels_by_component", {}) if isinstance(ver, dict) else {}
        comps, absent, hidden = [], [], []
        for k in keys:
            if not legend[k]:  # no enabled object: never exported as colour data, so it cannot reach the dashboard's pixel-presence logic
                absent.append({"key": k, "label": label_of(st, k), "custom": k in cust})
                continue
            px = pbc.get(k)
            e = {"key": k, "label": label_of(st, k), "hex": hx[k], "color_name": names[k], "objects": legend[k],
                 "custom": k in cust, "in_scene": True, "visible_pixels": px}
            if mask_all and px == 0:  # exists and is enabled, but nothing of it reaches the camera: keep it registered
                e["hidden_registered"] = True
                hidden.append(k)
            comps.append(e)
        data = {
            "schema": SCHEMA, "version": VERSION, "blend": os.path.basename(blend), "camera": sc.camera.name,
            "resolution": [sc.render.resolution_x, sc.render.resolution_y],
            "aspect_ratio": round(sc.render.resolution_x / float(sc.render.resolution_y), 4),
            "mask_all_scene": mask_all,
            "outline": {"requested": wf, "applied": outline is not None, "hex": OUTLINE, "thickness_px": 1.5, "error": outline_err},
            "components": comps, "absent_components": absent,
            "groups": {LIGHTING_GROUP[0]: LIGHTING_GROUP[1]},
            "unmatched_hex": UNMATCHED, "outline_hex": OUTLINE, "unassigned_objects": unassigned, "skipped_objects": skipped,
            "materials": _materials(), "verification": ver,
        }
        with open(js + ".tmp", "w") as f:
            json.dump(data, f, indent=1)
        os.replace(js + ".tmp", js)
        summary = {"png": png, "json": js, "unassigned": unassigned, "skipped": skipped, "manual": assigned_manual,
                   "total": len(originals), "verification": ver, "outline_applied": outline is not None, "outline_requested": wf, "outline_error": outline_err, "names": names,
                   "hidden_registered": [label_of(st, k) for k in hidden], "absent": [label_of(st, a["key"]) for a in absent],
                   "not_visible": [label_of(st, k) for k in key_hex if pbc.get(k, 1) == 0 and k not in hidden]}
    finally:  # always put everything back, whether the render succeeded or not
        outline_end(outline)
        for ob, orig in originals.items():
            try:
                ob.color = orig
                if MARK in ob:
                    del ob[MARK]
            except Exception:
                pass
        apply_settings(sc, snap)
        try:
            sc.world = world
            if tmp_world is not None:
                bpy.data.worlds.remove(tmp_world)
        except Exception:
            pass
        try:
            prefs.render_display_type = old_disp
        except Exception:
            pass
        if SNAP in sc:
            del sc[SNAP]
    return summary


# ---------------------------------------------------------------- properties
_ENUM_CACHE = []

def _group_items(self, context):
    """Dynamic 'Assign objects' list: always reads the current labels, so a rename shows up the moment it is confirmed."""
    global _ENUM_CACHE
    _ENUM_CACHE = [(k, label_of(self, k), "") for k in all_keys(self)]
    return _ENUM_CACHE

def _redraw_all():
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                a.tag_redraw()
    except Exception:
        pass

def _mk_label_update(k):
    def upd(self, context):
        cur = getattr(self, "l_" + k)
        new = _unique_label(self, k, _clean_label(cur, COMPONENTS[k][0]))
        if new != cur:
            setattr(self, "l_" + k, new)
        _redraw_all()
    return upd

def _custom_label_update(self, context):
    st = self.id_data.akm
    new = _unique_label(st, self.key, _clean_label(self.label, "Custom"))
    if new != self.label:
        self.label = new
    _redraw_all()


class AKM_Custom(bpy.types.PropertyGroup):
    key: StringProperty(name="Key", description="Permanent internal key (never changes when the name is edited)", default="")
    label: StringProperty(name="Name", description="Display name; shown in the dashboard's region map and prompt", default="Custom", update=_custom_label_update)
    patterns: StringProperty(name="Patterns", description="Comma-separated name patterns matched against object and collection names (plain text = contains; * and ? wildcards)", default="")
    color: FloatVectorProperty(name="Colour", subtype="COLOR_GAMMA", size=3, min=0.0, max=1.0, default=(1.0, 0.0, 1.0))


def _make_settings():
    ann = {"active_group": EnumProperty(name="Group", items=_group_items)}
    for k, (label, hx, _) in COMPONENTS.items():
        ann["c_" + k] = FloatVectorProperty(name=label, subtype="COLOR_GAMMA", size=3, min=0.0, max=1.0, default=hex_to_srgb(hx))
        ann["l_" + k] = StringProperty(name="Name", description="Display name (the internal key never changes)", default=label, update=_mk_label_update(k))
    ann["custom"] = CollectionProperty(type=AKM_Custom)
    ann["new_label"] = StringProperty(name="Name", description="Name of the new custom component", default="")
    ann["new_patterns"] = StringProperty(name="Patterns", description="Comma-separated name patterns (plain text = contains; * and ? wildcards)", default="")
    ann["mask_all"] = BoolProperty(name="Mask All Scene", description="Also register components whose objects exist and are render-enabled but are hidden behind other geometry. Absent or disabled components are never exported", default=False)
    ann["wireframe"] = BoolProperty(name="Wireframe outlines", description="Draw black outlines over the colour regions (temporary Freestyle line set)", default=True)
    return type("AKM_Settings", (bpy.types.PropertyGroup,), {"__annotations__": ann})

AKM_Settings = _make_settings()


# ---------------------------------------------------------------- operators
class AKM_OT_assign_selected(bpy.types.Operator):
    bl_idname = "akm.assign_selected"
    bl_label = "Assign Selected to Mask"
    bl_description = "Put the selected objects in the chosen mask group (replaces any previous group)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        st = context.scene.akm
        g = active_key(st)
        n = skipped = 0
        for ob in context.selected_objects:
            if ob.type in RENDERABLE:
                ob[PROP] = g  # single-valued: this also clears any previous group
                n += 1
            else:
                skipped += 1
        if not n:
            self.report({"WARNING"}, "Select at least one mesh/curve/text object first.")
            return {"CANCELLED"}
        self.report({"INFO"}, f"{n} object(s) -> {label_of(st, g)}" + (f" ({skipped} non-renderable skipped)" if skipped else ""))
        return {"FINISHED"}


class AKM_OT_clear_manual(bpy.types.Operator):
    bl_idname = "akm.clear_manual"
    bl_label = "Clear Manual Assignment"
    bl_description = "Remove the manual group from selected objects so name-matching applies again"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = 0
        for ob in context.selected_objects:
            if PROP in ob:
                del ob[PROP]
                n += 1
        self.report({"INFO"}, f"Cleared {n} object(s)")
        return {"FINISHED"}


class AKM_OT_reset_colors(bpy.types.Operator):
    bl_idname = "akm.reset_colors"
    bl_label = "Reset Colours"
    bl_description = "Restore the 16 default mask colours (custom components keep theirs)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for k in COMPONENTS:
            context.scene.akm.property_unset("c_" + k)
        return {"FINISHED"}


class AKM_OT_reset_labels(bpy.types.Operator):
    bl_idname = "akm.reset_labels"
    bl_label = "Reset Names"
    bl_description = "Restore the default names of the 16 built-in components (custom components keep theirs)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        st = context.scene.akm
        for k in COMPONENTS:
            st.property_unset("l_" + k)
        _redraw_all()
        return {"FINISHED"}


class AKM_OT_add_custom(bpy.types.Operator):
    bl_idname = "akm.add_custom"
    bl_label = "Add Component"
    bl_description = "Create a custom mask component with its own free colour (CIEDE2000 >= 5 from every other mask colour)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        st = context.scene.akm
        label = _clean_label(st.new_label, "")
        if not label:
            self.report({"ERROR"}, "Type a name for the new component first.")
            return {"CANCELLED"}
        if label.lower() in {label_of(st, k).strip().lower() for k in all_keys(st)}:
            self.report({"ERROR"}, f"The name '{label}' is already used by another component.")
            return {"CANCELLED"}
        if len(st.custom) >= 48:
            self.report({"ERROR"}, "At most 48 custom components.")
            return {"CANCELLED"}
        hx = allocate_color(st)
        if hx is None:
            self.report({"ERROR"}, f"No free colour slot is left (every candidate is within CIEDE2000 {DE_MIN:g} of an existing mask colour).")
            return {"CANCELLED"}
        it = st.custom.add()
        it.key = _new_key(st)  # set first: the label update callback looks the key up
        it.color = hex_to_srgb(hx)
        it.patterns = st.new_patterns.strip()
        it.label = label
        st.new_label = ""
        st.new_patterns = ""
        _redraw_all()
        self.report({"INFO"}, f"Added '{label}' ({hx}).")
        return {"FINISHED"}


class AKM_OT_remove_custom(bpy.types.Operator):
    bl_idname = "akm.remove_custom"
    bl_label = "Remove Custom Component"
    bl_description = "Delete this custom component (objects assigned to it become unassigned / name-matched again)"
    bl_options = {"REGISTER", "UNDO"}
    key: StringProperty()

    def execute(self, context):
        st = context.scene.akm
        idx = next((i for i, it in enumerate(st.custom) if it.key == self.key), -1)
        if idx < 0:
            return {"CANCELLED"}
        for ob in bpy.data.objects:
            if ob.get(PROP) == self.key:
                del ob[PROP]
        st.custom.remove(idx)
        _redraw_all()
        return {"FINISHED"}


class AKM_OT_pick_object(bpy.types.Operator):
    bl_idname = "akm.pick_object"
    bl_label = "Pick From Viewport"
    bl_description = "Click one object in the 3D viewport to assign it to the chosen group (Esc / right-click cancels)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.area is not None and context.area.type == "VIEW_3D"

    def _finish(self, context):
        context.window.cursor_modal_restore()
        context.workspace.status_text_set(None)

    def invoke(self, context, event):
        context.window.cursor_modal_set("EYEDROPPER")
        st = context.scene.akm
        context.workspace.status_text_set(f"Click an object to assign it to '{label_of(st, active_key(st))}'  |  Esc / right-click: cancel")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type in {"ESC", "RIGHTMOUSE"}:
            self._finish(context)
            return {"CANCELLED"}
        if event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"} or event.type.startswith("NDOF") or event.type.startswith("TRACKPAD"):
            return {"PASS_THROUGH"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            from bpy_extras import view3d_utils
            region = next((r for r in context.area.regions if r.type == "WINDOW"), None)
            inside = region and region.x <= event.mouse_x < region.x + region.width and region.y <= event.mouse_y < region.y + region.height
            if not inside:
                return {"RUNNING_MODAL"}  # clicks on the sidebar/header are ignored while picking
            rv3d = context.area.spaces.active.region_3d
            co = (event.mouse_x - region.x, event.mouse_y - region.y)
            hit, _loc, _nrm, _idx, obj, _mat = context.scene.ray_cast(
                context.evaluated_depsgraph_get(), view3d_utils.region_2d_to_origin_3d(region, rv3d, co),
                view3d_utils.region_2d_to_vector_3d(region, rv3d, co))
            self._finish(context)
            if not hit or obj is None:
                self.report({"WARNING"}, "Nothing under the cursor.")
                return {"CANCELLED"}
            ob = obj.original
            if ob.type not in RENDERABLE:
                self.report({"WARNING"}, f"'{ob.name}' is not a renderable geometry object.")
                return {"CANCELLED"}
            st = context.scene.akm
            g = active_key(st)
            ob[PROP] = g
            context.area.tag_redraw()
            self.report({"INFO"}, f"'{ob.name}' -> {label_of(st, g)}")
            return {"FINISHED"}
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        self._finish(context)


class AKM_OT_export(bpy.types.Operator):
    bl_idname = "akm.export_mask"
    bl_label = "Export Mask"
    bl_description = "Render the flat-colour mask (with optional wireframe outlines) and write the JSON legend next to the saved .blend"
    bl_options = {"REGISTER"}

    def execute(self, context):
        sc = context.scene
        if not bpy.data.filepath:
            self.report({"ERROR"}, "Save the .blend first: the mask is written next to it.")
            return {"CANCELLED"}
        if sc.camera is None:
            self.report({"ERROR"}, "The scene has no active camera.")
            return {"CANCELLED"}
        if context.mode != "OBJECT":
            self.report({"ERROR"}, "Switch to Object Mode before exporting.")
            return {"CANCELLED"}
        hx, errs, warns = check_colors(sc.akm)
        if errs:
            self.report({"ERROR"}, errs[0])
            return {"CANCELLED"}
        try:
            r = run_export(context, sc, hx)
        except Exception as e:
            self.report({"ERROR"}, f"Export failed; scene restored. {e}")
            return {"CANCELLED"}
        for w in warns[:3]:
            self.report({"WARNING"}, w)
        if r["unassigned"]:
            self.report({"WARNING"}, f"{len(r['unassigned'])} object(s) unassigned (render as {UNMATCHED}): " + ", ".join(r["unassigned"][:6]) + ("..." if len(r["unassigned"]) > 6 else ""))
        if r["skipped"]:
            self.report({"WARNING"}, f"{len(r['skipped'])} linked/read-only object(s) could not be coloured: " + ", ".join(r["skipped"][:4]))
        v = r["verification"]
        if r.get("outline_requested") and not r.get("outline_applied"):
            self.report({"WARNING"}, "Wireframe outlines could not be added (" + (r.get("outline_error") or "unknown") + "); exported flat colours only.")
        if v.get("unexpected_pixel_fraction", 0) > (0.02 if r.get("outline_applied") else 0):
            self.report({"WARNING"}, f"{v['unexpected_pixel_fraction'] * 100:.3f}% of pixels are not exact legend colours; check the PNG.")
        if r["not_visible"]:
            self.report({"INFO"}, "Groups with objects but not visible from this camera (left out of the dashboard): " + ", ".join(r["not_visible"]))
        if r["hidden_registered"]:
            self.report({"INFO"}, "Mask All Scene: registered although hidden from this camera: " + ", ".join(r["hidden_registered"]))
        self.report({"INFO"}, f"Exported {os.path.basename(r['png'])} + .json ({r['total']} objects, {r['manual']} manual)")
        return {"FINISHED"}


# ---------------------------------------------------------------- panel
class AKM_PT_panel(bpy.types.Panel):
    bl_idname = "AKM_PT_panel"
    bl_label = "Any Kitchen Mask"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Any Kitchen Mask"

    def draw(self, context):
        s, lay = context.scene.akm, self.layout
        keys = all_keys(s)
        counts = {}
        for o in context.scene.objects:
            g = o.get(PROP)
            if isinstance(g, str) and g in keys:
                counts[g] = counts.get(g, 0) + 1
        names = assign_names({k: color_hex(s, k) for k in keys})
        box = lay.box()
        box.label(text="Mask colours (click a name to rename)", icon="COLOR")
        col = box.column(align=True)
        for k in COMPONENTS:
            if k == LIGHTING_GROUP[1][0]:
                col.separator()
                col.label(text=LIGHTING_GROUP[0] + ":")
            sp = col.split(factor=0.52, align=True)
            sp.prop(s, "l_" + k, text="")
            row = sp.row(align=True)
            row.prop(s, "c_" + k, text="")
            row.label(text="%d  %s" % (counts.get(k, 0), names[k]))
        row = box.row(align=True)
        row.operator("akm.reset_colors", icon="LOOP_BACK")
        row.operator("akm.reset_labels", icon="LOOP_BACK")
        cb = lay.box()
        cb.label(text="Custom components", icon="ADD")
        for it in s.custom:
            c = cb.column(align=True)
            sp = c.split(factor=0.52, align=True)
            sp.prop(it, "label", text="")
            row = sp.row(align=True)
            row.prop(it, "color", text="")
            row.label(text="%d  %s" % (counts.get(it.key, 0), names.get(it.key, "")))
            op = row.operator("akm.remove_custom", text="", icon="TRASH")
            op.key = it.key
            c.prop(it, "patterns", text="Patterns")
        cb.prop(s, "new_label", text="Name")
        cb.prop(s, "new_patterns", text="Patterns")
        cb.operator("akm.add_custom", icon="ADD")
        box = lay.box()
        box.label(text="Assign objects", icon="RESTRICT_SELECT_OFF")
        box.prop(s, "active_group", text="")
        box.operator("akm.assign_selected", icon="CHECKMARK")
        box.operator("akm.pick_object", icon="EYEDROPPER")
        box.operator("akm.clear_manual", icon="X")
        lay.prop(s, "mask_all")
        lay.prop(s, "wireframe")
        lay.separator()
        if not bpy.data.filepath:
            lay.label(text="Save the .blend to enable export", icon="ERROR")
        row = lay.row()
        row.scale_y = 1.6
        row.operator("akm.export_mask", icon="RENDER_STILL")


# ---------------------------------------------------------------- registration
CLASSES = (AKM_Custom, AKM_Settings, AKM_OT_assign_selected, AKM_OT_clear_manual, AKM_OT_reset_colors, AKM_OT_reset_labels, AKM_OT_add_custom, AKM_OT_remove_custom, AKM_OT_pick_object, AKM_OT_export, AKM_PT_panel)

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.akm = PointerProperty(type=AKM_Settings)
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)
    try:
        recover()
    except Exception:
        pass

def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    del bpy.types.Scene.akm
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
