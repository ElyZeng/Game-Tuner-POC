"""Parse key graphics settings from game config file content.

Extracts 8 standardised settings from various config formats:
1. Resolution
2. Screen Mode
3. V-Sync
4. Frame Limit
5. Dynamic Resolution
6. Upscaling (DLSS / FSR / XeSS)
7. Frame Generation / Multi Frame Generation
8. Quick Preset
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional


# Result key constants
RESOLUTION = "resolution"
SCREEN_MODE = "screen_mode"
VSYNC = "vsync"
FRAME_LIMIT = "frame_limit"
DYNAMIC_RESOLUTION = "dynamic_resolution"
UPSCALING = "upscaling"
FRAME_GENERATION = "frame_generation"
QUICK_PRESET = "quick_preset"

ALL_KEYS = [
    RESOLUTION,
    SCREEN_MODE,
    VSYNC,
    FRAME_LIMIT,
    DYNAMIC_RESOLUTION,
    UPSCALING,
    FRAME_GENERATION,
    QUICK_PRESET,
]

# Human-readable display names (Chinese)
DISPLAY_NAMES = {
    RESOLUTION: "解析度",
    SCREEN_MODE: "螢幕模式",
    VSYNC: "垂直同步",
    FRAME_LIMIT: "幀率限制",
    DYNAMIC_RESOLUTION: "動態解析度",
    UPSCALING: "升頻技術",
    FRAME_GENERATION: "畫格生成",
    QUICK_PRESET: "畫質預設",
}

DISPLAY_NAMES_EN = {
    RESOLUTION: "Resolution",
    SCREEN_MODE: "Screen Mode",
    VSYNC: "V-Sync",
    FRAME_LIMIT: "Frame Limit",
    DYNAMIC_RESOLUTION: "Dynamic Resolution",
    UPSCALING: "Upscaling",
    FRAME_GENERATION: "Frame Generation",
    QUICK_PRESET: "Quick Preset",
}

# Dropdown options for each setting.  The first value is the default /
# "no change" sentinel shown when the user has not explicitly picked a
# value.  The rest are the selectable choices.
SETTING_OPTIONS: Dict[str, List[str]] = {
    RESOLUTION: [
        "—",
        "1280x720",
        "1600x900",
        "1920x1080",
        "2560x1080",
        "2560x1440",
        "3440x1440",
        "3840x2160",
    ],
    SCREEN_MODE: [
        "—",
        "Fullscreen",
        "Borderless Windowed",
        "Windowed",
    ],
    VSYNC: [
        "—",
        "On",
        "Off",
    ],
    FRAME_LIMIT: [
        "—",
        "Unlimited",
        "30 FPS",
        "60 FPS",
        "120 FPS",
        "144 FPS",
        "240 FPS",
    ],
    DYNAMIC_RESOLUTION: [
        "—",
        "On",
        "Off",
    ],
    UPSCALING: [
        "—",
        "Off",
        "XeSS",
        "DLSS",
        "FSR",
    ],
    FRAME_GENERATION: [
        "—",
        "Off",
        "On",
    ],
    # Quick Preset uses per-game options; this is the generic fallback.
    QUICK_PRESET: [
        "—",
    ],
}

# Per-game Quick Preset option lists keyed by parser-type string.
QUICK_PRESET_OPTIONS: Dict[str, List[str]] = {
    # Cyberpunk 2077 — QuickPresets field in UserSettings.json; known values from game UI
    "cyberpunk": [
        "—",
        "Low",
        "Medium",
        "High",
        "Ultra",
        "Ray Tracing Medium",
        "Ray Tracing High",
        "Ray Tracing Ultra",
        "Path Tracing",
    ],
    # Unreal Engine games using GPUConfigPreset integer (Hogwarts Legacy, etc.)
    "unreal_ini": [
        "—",
        "Low",
        "Medium",
        "High",
        "Ultra",
    ],
    # Forza Horizon XML — no single overall preset field
    "forza_xml": ["—"],
    # Registry-based games — no known preset field
    "registry_json": ["—"],
    # CS2 — no preset support
    "cs2": ["—"],
    # Unknown / generic
    "default": ["—"],
}


def _empty_result() -> Dict[str, Optional[str]]:
    return {k: None for k in ALL_KEYS}


# ── Cyberpunk 2077 (UserSettings.json) ───────────────────────────────

def _parse_cyberpunk(content: str) -> Dict[str, Optional[str]]:
    r = _empty_result()
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return r

    groups = data.get("data", [])
    options_map: Dict[str, Any] = {}
    for group in groups:
        gname = group.get("group_name", "")
        for opt in group.get("options", []):
            key = f"{gname}/{opt['name']}"
            options_map[opt["name"]] = opt
            options_map[key] = opt

    # Resolution
    res_opt = options_map.get("/video/display/Resolution")
    if res_opt:
        r[RESOLUTION] = str(res_opt.get("value", ""))

    # Screen Mode
    wm = options_map.get("WindowMode") or options_map.get("/video/display/WindowMode")
    if wm:
        mode = wm.get("value", "")
        mode_map = {0: "Fullscreen", 1: "Borderless Windowed", 2: "Windowed"}
        r[SCREEN_MODE] = mode_map.get(mode, str(mode))

    # VSync
    vs = options_map.get("VSync") or options_map.get("/video/display/VSync")
    if vs:
        val = str(vs.get("value", ""))
        if "Off" in val:
            r[VSYNC] = "Off"
        elif "On" in val:
            r[VSYNC] = "On"
        else:
            r[VSYNC] = val

    # Frame Limit
    fps_on = options_map.get("MaximumFPS_OnOff")
    fps_val = options_map.get("MaximumFPS")
    if fps_on is not None:
        on = fps_on.get("value", False)
        limit = fps_val.get("value", "") if fps_val else ""
        r[FRAME_LIMIT] = f"{limit}" if on else "Off"

    # Dynamic Resolution
    drs = options_map.get("DynamicResolutionScaling")
    drs_fps = options_map.get("DRS_TargetFPS")
    if drs is not None:
        on = drs.get("value", False)
        target = drs_fps.get("value", "") if drs_fps else ""
        r[DYNAMIC_RESOLUTION] = f"On (Target: {target} FPS)" if on else "Off"

    # Upscaling
    rs = options_map.get("ResolutionScaling")
    if rs:
        method = str(rs.get("value", "Off"))
        quality = ""
        method_opt = options_map.get(method.upper()) or options_map.get(method)
        if method_opt:
            quality = f" ({method_opt.get('value', '')})"
        r[UPSCALING] = f"{method}{quality}"

    # Frame Generation
    fg = options_map.get("FrameGeneration")
    mfg = options_map.get("DLSS_MultiFrameGeneration")
    parts = []
    if fg:
        parts.append(str(fg.get("value", "Off")))
    if mfg:
        parts.append(f"MFG: {mfg.get('value', '')}")
    if parts:
        r[FRAME_GENERATION] = " / ".join(parts)

    # Quick Preset — stored under /graphics/presets/QuickPresets
    qp = options_map.get("/graphics/presets/QuickPresets") or options_map.get("QuickPresets")
    if qp is not None:
        r[QUICK_PRESET] = str(qp.get("value", "Custom"))

    return r


def _parse_black_myth(content: str) -> Dict[str, Optional[str]]:
    """Parse Black Myth: Wukong's Unreal config and UISettingData tuple."""
    r = _parse_unreal_ini(content)
    ui_values = dict(re.findall(r'\("([^"]+)",\s*"([^"]*)"\)', content))

    screen_mode = ui_values.get("ScreenMode")
    if screen_mode is not None:
        r[SCREEN_MODE] = {
            "0": "Fullscreen",
            "1": "Borderless Windowed",
            "2": "Windowed",
        }.get(screen_mode, f"Mode {screen_mode}")

    vsync = ui_values.get("Vsync")
    if vsync is not None:
        r[VSYNC] = "On" if vsync in {"1", "true", "True"} else "Off"

    quality = ui_values.get("QualityLevel")
    if quality is not None:
        r[QUICK_PRESET] = {
            "0": "Low",
            "1": "Medium",
            "2": "High",
            "3": "Very High",
            "4": "Cinematic",
        }.get(quality, f"Quality Level {quality}")

    dlss = ui_values.get("Dlss")
    super_resolution = ui_values.get("SuperResolutionSampling")
    if dlss in {"1", "true", "True"}:
        r[UPSCALING] = f"DLSS (mode {super_resolution})" if super_resolution else "DLSS"
    elif super_resolution not in {None, "0"}:
        r[UPSCALING] = f"Super Resolution (mode {super_resolution})"

    insert_frame = ui_values.get("InsertFrame")
    if insert_frame is not None:
        r[FRAME_GENERATION] = "On" if insert_frame in {"1", "true", "True"} else "Off"

    return r


def _parse_expedition_33(content: str) -> Dict[str, Optional[str]]:
    """Parse Expedition 33's Unreal settings and scalability preset."""
    r = _parse_unreal_ini(content)
    kv = _parse_ini_kv(content)
    quality_values = {
        value
        for key, value in kv.items()
        if key.startswith("sg.")
        and key.endswith("Quality")
        and key != "sg.ResolutionQuality"
    }
    quality_map = {"0": "Low", "1": "Medium", "2": "High", "3": "Epic", "4": "Cinematic"}
    if len(quality_values) == 1:
        value = next(iter(quality_values))
        r[QUICK_PRESET] = quality_map.get(value, f"Quality Level {value}")
    elif quality_values:
        r[QUICK_PRESET] = "Custom"
    return r


# ── Unreal Engine INI (ARC Raiders, Hogwarts Legacy, etc.) ───────────

def _parse_ini_kv(content: str) -> Dict[str, str]:
    """Parse simple key=value lines from INI-like content."""
    kv: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("[") and not line.startswith(";"):
            key, _, val = line.partition("=")
            kv[key.strip()] = val.strip()
    return kv


def _parse_unreal_ini(content: str) -> Dict[str, Optional[str]]:
    r = _empty_result()
    kv = _parse_ini_kv(content)

    # Resolution
    rx, ry = kv.get("ResolutionSizeX"), kv.get("ResolutionSizeY")
    if rx and ry:
        r[RESOLUTION] = f"{rx}x{ry}"

    # Screen Mode
    fm = kv.get("FullscreenMode")
    mode_map = {"0": "Fullscreen", "1": "Borderless Windowed", "2": "Windowed"}
    if fm is not None:
        r[SCREEN_MODE] = mode_map.get(fm, f"Mode {fm}")

    # VSync
    vs = kv.get("bUseVSync")
    if vs is not None:
        r[VSYNC] = "On" if vs.lower() == "true" else "Off"

    # Frame Limit
    frl = kv.get("FrameRateLimit")
    if frl is not None:
        try:
            val = float(frl)
            r[FRAME_LIMIT] = "Unlimited" if val <= 0 else f"{val:.0f} FPS"
        except ValueError:
            r[FRAME_LIMIT] = frl

    # Dynamic Resolution
    dr = kv.get("bUseDynamicResolution")
    if dr is not None:
        r[DYNAMIC_RESOLUTION] = "On" if dr.lower() == "true" else "Off"

    # Upscaling
    method = kv.get("ResolutionScalingMethod", "")
    selected_upscaler = kv.get("CurrentSelectedUpscaler", "")
    dlss = kv.get("DLSSMode", "")
    fsr = kv.get("FSRMode", "")
    xess = kv.get("XeSSMode", "")
    if selected_upscaler:
        quality_mode = kv.get("CurrentSelectedUpscalerQualityMode", "")
        r[UPSCALING] = f"{selected_upscaler} (mode {quality_mode})" if quality_mode else selected_upscaler
    elif method:
        quality = {"DLSS": dlss, "FSR": fsr, "XeSS": xess}.get(method, "")
        r[UPSCALING] = f"{method} ({quality})" if quality else method

    # Frame Generation
    dlss_fg = kv.get("DLSSFrameGenerationMode", "")
    fsr_fg = kv.get("FSRFrameGenerationMode", "")
    selected_fg = kv.get("CurrentSelectedFrameGenerationMode", "")
    parts = []
    if dlss_fg and dlss_fg != "Off":
        parts.append(f"DLSS FG: {dlss_fg}")
    if fsr_fg and fsr_fg != "Off":
        parts.append(f"FSR FG: {fsr_fg}")
    if selected_fg:
        r[FRAME_GENERATION] = "Off" if selected_fg in {"0", "Off", "false", "False"} else f"On (mode {selected_fg})"
    elif dlss_fg or fsr_fg:
        r[FRAME_GENERATION] = " / ".join(parts) if parts else "Off"

    # Quick Preset — GPUConfigPreset: -1=Custom, 0=Low, 1=Medium, 2=High, 3=Ultra
    gcp = kv.get("GPUConfigPreset")
    if gcp is not None:
        preset_map = {"-1": "Custom", "0": "Low", "1": "Medium", "2": "High", "3": "Ultra"}
        r[QUICK_PRESET] = preset_map.get(gcp, f"Preset {gcp}")

    return r


# ── Street Fighter 6 config.ini ─────────────────────────────────────

def _parse_sf6(content: str) -> Dict[str, Optional[str]]:
    r = _empty_result()
    kv = _parse_ini_kv(content)

    # SF6 stores the selected display mode as an index into DisplayModeN_*.
    display_mode = kv.get("FullScreenDisplayMode")
    if display_mode is not None:
        width = kv.get(f"DisplayMode{display_mode}_Width")
        height = kv.get(f"DisplayMode{display_mode}_Height")
        if width and height:
            r[RESOLUTION] = f"{width}x{height}"

    fullscreen = kv.get("FullScreenMode", "").lower()
    window_mode = kv.get("WindowMode", "").lower()
    if fullscreen in {"true", "1", "yes"}:
        r[SCREEN_MODE] = "Fullscreen"
    elif window_mode in {"borderless", "borderlesswindow", "borderless_window"}:
        r[SCREEN_MODE] = "Borderless Windowed"
    elif fullscreen or window_mode:
        r[SCREEN_MODE] = "Windowed"

    vsync = kv.get("VSync")
    if vsync is not None:
        r[VSYNC] = "On" if vsync.lower() in {"true", "1", "yes"} else "Off"

    max_framerate = kv.get("MaxFramerate")
    if max_framerate is not None:
        try:
            value = float(max_framerate)
            r[FRAME_LIMIT] = "Unlimited" if value <= 0 else f"{value:.0f} FPS"
        except ValueError:
            r[FRAME_LIMIT] = max_framerate

    preset = kv.get("GlobalSettings")
    if preset:
        r[QUICK_PRESET] = preset.replace("_", " ").title()

    upscale = kv.get("UpscaleType")
    if upscale is not None:
        r[UPSCALING] = "Off" if upscale.lower() in {"none", "off", "0"} else upscale

    # This config has no explicit frame-generation switch.
    r[FRAME_GENERATION] = "N/A"
    return r


# ── Forza Horizon XML (UserConfigSelections) ─────────────────────────

def _parse_forza_xml(content: str) -> Dict[str, Optional[str]]:
    r = _empty_result()

    def _xml_val(tag: str) -> Optional[str]:
        m = re.search(rf'<{tag}\b[^>]*\bvalue="([^"]*)"', content)
        return m.group(1) if m else None

    def _sel_val(option_id: str) -> Optional[str]:
        m = re.search(rf'<option\s+id="{option_id}"\s+value="([^"]*)"', content)
        return m.group(1) if m else None

    # Resolution
    rw, rh = _xml_val("ResolutionWidth"), _xml_val("ResolutionHeight")
    if rw and rh:
        r[RESOLUTION] = f"{rw}x{rh}"

    # Screen Mode
    fs = _xml_val("Fullscreen")
    if fs is not None:
        r[SCREEN_MODE] = "Fullscreen" if fs == "1" else "Windowed"

    # VSync
    vs = _sel_val("VSync")
    pi = _xml_val("PresentInterval")
    if vs is not None:
        r[VSYNC] = "On" if vs != "0" else "Off"
    elif pi is not None:
        r[VSYNC] = "Off" if pi == "0" else "On"

    # Frame Limit
    fr = _sel_val("FrameRate")
    if fr is not None:
        fr_map = {"0": "30 FPS", "1": "40 FPS", "2": "60 FPS", "3": "120 FPS", "4": "Unlimited"}
        r[FRAME_LIMIT] = fr_map.get(fr, f"Preset {fr}")

    # Dynamic Resolution
    dopt = _sel_val("UseDynamicOptimization")
    if dopt is not None:
        r[DYNAMIC_RESOLUTION] = "On" if dopt != "0" else "Off"

    # Upscaling
    dlss_sel = _sel_val("DLSSMode")
    fsr3_sel = _sel_val("FSR3Mode")
    xess_sel = _sel_val("XeSSMode")
    active = []
    if xess_sel and xess_sel != "0":
        active.append(f"XeSS (preset {xess_sel})")
    if dlss_sel and dlss_sel != "0":
        active.append(f"DLSS (preset {dlss_sel})")
    if fsr3_sel and fsr3_sel != "0":
        active.append(f"FSR3 (preset {fsr3_sel})")
    r[UPSCALING] = ", ".join(active) if active else "Off"

    # Frame Generation
    dlssg = _sel_val("DLSSGMode")
    parts = []
    if dlssg and dlssg != "0":
        parts.append("DLSS FG: On")
    r[FRAME_GENERATION] = ", ".join(parts) if parts else "Off"

    # Forza has no single overall preset field. Infer Custom when the quality
    # selections are mixed; preserve a uniform numeric level without guessing
    # its game-specific display name.
    quality_ids = {
        "CarLOD", "EnvStreamingTex", "GeometryQuality", "ReflectionQuality",
        "SSRQuality", "ShadowQuality", "ShaderQuality", "DeformableSnowQuality",
        "ParticlesSettings", "VolumetricFogQuality", "LensEffects",
    }
    options = dict(re.findall(r'<option\s+id="([^"]+)"\s+value="([^"]*)"', content))
    quality_values = {
        options[option_id]
        for option_id in quality_ids
        if option_id in options
    }
    if len(quality_values) > 1:
        r[QUICK_PRESET] = "Custom"
    elif len(quality_values) == 1:
        r[QUICK_PRESET] = f"Preset Level {next(iter(quality_values))}"
    else:
        r[QUICK_PRESET] = "N/A"

    return r


# ── F1 25 hardware_settings_config.xml ─────────────────────────────

def _parse_f1_xml(content: str) -> Dict[str, Optional[str]]:
    r = _empty_result()
    try:
        root = ET.fromstring(content)
    except (ET.ParseError, ValueError):
        return r

    def find_node(name: str) -> Optional[ET.Element]:
        return next((node for node in root.iter(name)), None)

    resolution = find_node("resolution")
    if resolution is not None:
        width = resolution.get("width")
        height = resolution.get("height")
        if width and height:
            r[RESOLUTION] = f"{width}x{height}"

        display_mode = resolution.get("displayMode")
        display_modes = {
            "0": "Windowed",
            "1": "Fullscreen",
            "2": "Borderless Windowed",
        }
        if display_mode in display_modes:
            r[SCREEN_MODE] = display_modes[display_mode]

        vsync = resolution.get("vsync")
        if vsync is not None:
            r[VSYNC] = "On" if vsync.lower() in {"true", "1", "yes"} else "Off"

        limiter_enabled = resolution.get("frameRateLimiterEnabled")
        limiter_value = resolution.get("frameRateLimiterValue")
        if limiter_enabled is not None and limiter_enabled.lower() in {"false", "0", "no"}:
            r[FRAME_LIMIT] = "Unlimited"
        elif limiter_value:
            r[FRAME_LIMIT] = f"{limiter_value} FPS"

    anti_aliasing = find_node("antialiasing")
    if anti_aliasing is not None:
        dlss = anti_aliasing.get("dlss", "false").lower() in {"true", "1", "yes"}
        fsr3 = anti_aliasing.get("fsr3", "0")
        xess = anti_aliasing.get("xess", "false").lower() in {"true", "1", "yes"}
        if dlss:
            r[UPSCALING] = "DLSS"
        elif fsr3 not in {"0", "", "false", "off"}:
            r[UPSCALING] = f"FSR3 ({fsr3})"
        elif xess:
            r[UPSCALING] = "XeSS"
        else:
            r[UPSCALING] = "Off"

    frame_gen = find_node("frame_gen")
    multi_frame_gen = find_node("multi_frame_gen")
    frame_gen_value = frame_gen.get("mode", "0") if frame_gen is not None else "0"
    multi_frame_value = multi_frame_gen.get("value", "0") if multi_frame_gen is not None else "0"
    r[FRAME_GENERATION] = "Off" if frame_gen_value in {"0", "", "off"} and multi_frame_value in {"0", "", "off"} else "On"

    dynamic = find_node("dynamicresolution_enabled")
    if dynamic is not None:
        enabled = dynamic.get("value", "false").lower() in {"true", "1", "yes"}
        target = find_node("dynamicresolution_target_fps")
        target_value = target.get("value", "") if target is not None else ""
        r[DYNAMIC_RESOLUTION] = f"On (Target: {target_value} FPS)" if enabled and target_value else ("On" if enabled else "Off")

    # F1 25 has no single overall preset. Infer one from the quality-bearing
    # component values when possible; mixed component levels are Custom.
    quality_values = []
    for node_name, attribute in (
        ("lighting", "quality"),
        ("ssrt", "quality"),
        ("shadows", "sampling"),
        ("weather_effects", "proceduralCloudQuality"),
    ):
        node = find_node(node_name)
        if node is not None and node.get(attribute) is not None:
            quality_values.append(node.get(attribute))
    if len(set(quality_values)) > 1:
        r[QUICK_PRESET] = "Custom"
    elif quality_values:
        r[QUICK_PRESET] = f"Preset Level {quality_values[0]}"
    else:
        r[QUICK_PRESET] = "N/A"
    return r


# ── Registry JSON (HZD, Shadow of TR) ───────────────────────────────

def _parse_registry_json(content: str, game_hint: str = "") -> Dict[str, Optional[str]]:
    r = _empty_result()
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return r

    gfx = data.get("Graphics", data)

    # Resolution
    fw = gfx.get("FullscreenWidth", gfx.get("WindowWidth"))
    fh = gfx.get("FullscreenHeight", gfx.get("WindowHeight"))
    if fw is not None and fh is not None:
        r[RESOLUTION] = f"{fw}x{fh}"

    # Screen Mode
    fs = gfx.get("Fullscreen")
    efs = gfx.get("ExclusiveFullscreen")
    if fs is not None:
        if fs == 1:
            r[SCREEN_MODE] = "Exclusive Fullscreen" if efs == 1 else "Borderless Fullscreen"
        else:
            r[SCREEN_MODE] = "Windowed"

    # VSync
    vs = gfx.get("VSync")
    if vs is not None:
        r[VSYNC] = "On" if vs != 0 else "Off"

    # Frame Limit
    drt = gfx.get("DynamicResolutionTargetFPS")
    fhr = gfx.get("ForceHalfRefreshRate")
    if drt is not None:
        r[FRAME_LIMIT] = f"{drt} FPS" if drt > 0 else "Unlimited"
    elif fhr is not None:
        r[FRAME_LIMIT] = "Half Refresh Rate" if fhr else "Unlimited"

    # Dynamic Resolution
    if drt is not None:
        r[DYNAMIC_RESOLUTION] = f"On (Target: {drt} FPS)" if drt > 0 else "Off"
    else:
        rm = gfx.get("ResolutionModifier")
        if rm is not None:
            pct = rm / 10 if rm > 100 else rm
            r[DYNAMIC_RESOLUTION] = f"{pct:.0f}%" if pct != 100 else "Off (100%)"

    # Upscaling
    um = gfx.get("UpscaleMethod")
    uq = gfx.get("UpscaleQuality")
    dlss = gfx.get("DLSS")
    xess = gfx.get("XESS")
    cas = gfx.get("CAS")
    if um is not None:
        method_map = {0: "Off", 1: "DLSS", 2: "FSR", 3: "CAS", 4: "XeSS"}
        quality_map = {0: "Ultra Performance", 1: "Performance", 2: "Balanced", 3: "Quality", 4: "Ultra Quality"}
        m = method_map.get(um, f"Method {um}")
        q = quality_map.get(uq, "") if uq is not None else ""
        r[UPSCALING] = f"{m} ({q})" if q else m
    elif dlss is not None or xess is not None:
        parts = []
        if xess and xess != 0:
            parts.append("XeSS: On")
        if dlss and dlss != 0:
            parts.append("DLSS: On")
        if cas and cas != 0:
            parts.append("CAS: On")
        r[UPSCALING] = ", ".join(parts) if parts else "Off"

    # Frame Generation
    fg = gfx.get("FrameGen")
    dlssg = gfx.get("DLSSG")
    parts = []
    if fg and fg != 0:
        parts.append("Frame Gen: On")
    if dlssg and dlssg != 0:
        parts.append("DLSS-G: On")
    if fg is None and dlssg is None:
        r[FRAME_GENERATION] = "N/A"
    else:
        r[FRAME_GENERATION] = ", ".join(parts) if parts else "Off"

    # Quick Preset — registry-based games have no known preset field
    r[QUICK_PRESET] = "N/A"

    return r


# ── CS2 (cs2_video.txt + convars) ───────────────────────────────────

def _parse_cs2(all_configs: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """Parse CS2 settings from multiple config file entries."""
    r = _empty_result()

    video_kv: Dict[str, str] = {}
    convar_kv: Dict[str, str] = {}

    for cfg in all_configs:
        content = cfg.get("content") or ""
        path = cfg.get("expanded_path", "")
        if "cs2_video" in path.lower():
            video_kv = {}
            for line in content.splitlines():
                line = line.strip()
                m = re.match(r'"([^"]+)"\s+"([^"]*)"', line)
                if m:
                    video_kv[m.group(1)] = m.group(2)
        elif "machine_convars" in path.lower() or "user_convars" in path.lower():
            for line in content.splitlines():
                line = line.strip()
                m = re.match(r'"([^"]+)"\s+"([^"]*)"', line)
                if m:
                    convar_kv[m.group(1)] = m.group(2)

    # Resolution
    w = video_kv.get("setting.defaultres")
    h = video_kv.get("setting.defaultresheight")
    if w and h:
        r[RESOLUTION] = f"{w}x{h}"

    # Screen Mode
    fs = video_kv.get("setting.fullscreen", "0")
    nwb = video_kv.get("setting.nowindowborder", "0")
    if fs == "1":
        r[SCREEN_MODE] = "Fullscreen"
    elif nwb == "1":
        r[SCREEN_MODE] = "Borderless Windowed"
    else:
        r[SCREEN_MODE] = "Windowed"

    # VSync
    vs = video_kv.get("setting.mat_vsync")
    if vs is not None:
        r[VSYNC] = "On" if vs != "0" else "Off"

    # Frame Limit
    fps = convar_kv.get("fps_max")
    if fps:
        try:
            val = float(fps)
            r[FRAME_LIMIT] = "Unlimited" if val <= 0 else f"{val:.0f} FPS"
        except ValueError:
            r[FRAME_LIMIT] = fps

    # Upscaling
    fsr = video_kv.get("setting.videocfg_fsr_detail")
    if fsr is not None:
        fsr_map = {"0": "Off", "1": "Ultra Quality", "2": "Quality", "3": "Balanced", "4": "Performance"}
        r[UPSCALING] = f"FSR ({fsr_map.get(fsr, fsr)})" if fsr != "0" else "Off"

    # CS2 has no Dynamic Resolution, Frame Generation, or Quick Preset
    r[DYNAMIC_RESOLUTION] = "N/A"
    r[FRAME_GENERATION] = "N/A"
    r[QUICK_PRESET] = "N/A"

    return r


# ── Main dispatcher ─────────────────────────────────────────────────

def extract_key_settings(
    game_name: str,
    config_files: List[Dict[str, Any]],
) -> Dict[str, Optional[str]]:
    """Extract the 8 key graphics settings from a game's config files.

    Parameters
    ----------
    game_name:
        The name of the game (used to select the appropriate parser).
    config_files:
        The ``config_files`` list from the export JSON, where each entry
        has ``expanded_path``, ``content``, ``found``, ``error``, etc.

    Returns
    -------
    dict
        A dict mapping each of the 8 setting keys to a human-readable
        value string, or ``None`` if not found.
    """
    readable = [c for c in config_files if c.get("content") and c.get("found")]
    if not readable:
        return _empty_result()

    name_lower = game_name.lower()

    if "cyberpunk" in name_lower:
        return _parse_cyberpunk(readable[0]["content"])

    if "black myth" in name_lower or "wukong" in name_lower:
        return _parse_black_myth(readable[0]["content"])

    if "clair obscur" in name_lower or "expedition 33" in name_lower:
        return _parse_expedition_33(readable[0]["content"])

    if "street fighter" in name_lower or "streetfighter" in name_lower:
        return _parse_sf6(readable[0]["content"])

    if "counter-strike" in name_lower or "cs2" in name_lower:
        return _parse_cs2(readable)

    if "forza" in name_lower:
        return _parse_forza_xml(readable[0]["content"])

    if name_lower in {"f1 25", "f1® 25"} or "f1 25" in name_lower:
        return _parse_f1_xml(readable[0]["content"])

    for cfg in readable:
        if cfg.get("type") == "registry":
            return _parse_registry_json(cfg["content"], game_hint=name_lower)

    for cfg in readable:
        content = cfg["content"]
        if "ResolutionSizeX" in content or "FullscreenMode" in content:
            return _parse_unreal_ini(content)

    # Generic fallback: try all parsers and return the one with most results
    best = _empty_result()
    best_count = 0
    for parser in [_parse_unreal_ini, _parse_forza_xml]:
        for cfg in readable:
            try:
                result = parser(cfg["content"])
                count = sum(1 for v in result.values() if v is not None)
                if count > best_count:
                    best = result
                    best_count = count
            except Exception:
                pass
    return best
