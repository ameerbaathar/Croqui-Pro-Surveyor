# -*- coding: utf-8 -*-
"""
Croqui Pro Surveyor - v9.3 (Final)
====================================
- 💾 الكاش في D:\croqui_cache\ (ثابت)
- 🔧 حفظ صحيح للتايلات (fsync + فحص)
- 📊 تقارير تشخيص في terminal
- 🎯 موقع الأرض في المصغرة دقيق
- 🛣️ تحديد الشارع/البحر على ضلع محدد
- 📏 كل ضلع مستقل تماماً (لا تعارض)
- ✋ سحب البحر والطريق العام بالماوس
- 🗺️ الخريطة الكبيرة = OSM | المصغرة = Satellite

التثبيت:
    pip install requests pillow matplotlib pyproj ezdxf
"""

import io
import os
import re
import csv
import glob
import math
import json
import time
import queue
import platform
import traceback
import threading
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Circle
from matplotlib.gridspec import GridSpec
from matplotlib import font_manager as fm

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

from pyproj import CRS, Transformer, Geod


# ============================================================
# 💾 الكاش
# ============================================================
def _detect_cache_dir():
    if platform.system() == "Windows":
        d_drive = Path("D:/")
        if d_drive.exists() and d_drive.is_dir():
            return Path("D:/croqui_cache")
        c_drive = Path("C:/")
        if c_drive.exists():
            return Path("C:/croqui_cache")
        return Path.home() / "croqui_cache"
    else:
        return Path.home() / "croqui_cache"


CACHE_DIR = _detect_cache_dir()
TILE_CACHE_DIR = CACHE_DIR / "tiles"

try:
    TILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[Cache] مجلد الكاش: {CACHE_DIR}")
except Exception as e:
    print(f"[Cache] تحذير: فشل إنشاء {CACHE_DIR}: {e}")
    CACHE_DIR = Path.home() / "croqui_cache"
    TILE_CACHE_DIR = CACHE_DIR / "tiles"
    TILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[Cache] استخدام البديل: {CACHE_DIR}")


MAX_CACHE_MB = 500


def get_cache_path(z, x, y, source="osm"):
    short = "osm" if source == "osm" else "sat"
    folder = TILE_CACHE_DIR / short / str(z) / str(x)
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return folder / f"{y}.png"


def get_cache_size():
    total = 0
    try:
        for f in TILE_CACHE_DIR.rglob("*.png"):
            try:
                total += f.stat().st_size
            except Exception:
                pass
    except Exception as e:
        print(f"[Cache] خطأ: {e}")
    return total / 1024 / 1024


def clear_cache():
    try:
        import shutil
        if TILE_CACHE_DIR.exists():
            shutil.rmtree(TILE_CACHE_DIR)
            TILE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            return True
    except Exception as e:
        print(f"[Cache] فشل الحذف: {e}")
    return False


# ============================================================
# الخطوط
# ============================================================
KNOWN_ARABIC_FONTS = {
    "Windows": [
        ("Tahoma", "C:/Windows/Fonts/tahoma.ttf"),
        ("Segoe UI", "C:/Windows/Fonts/segoeui.ttf"),
        ("Arial", "C:/Windows/Fonts/arial.ttf"),
        ("Traditional Arabic", "C:/Windows/Fonts/trado.ttf"),
        ("Simplified Arabic", "C:/Windows/Fonts/simpo.ttf"),
        ("Arabic Typesetting", "C:/Windows/Fonts/arabtype.ttf"),
        ("Sakkal Majalla", "C:/Windows/Fonts/majalla.ttf"),
        ("Andalus", "C:/Windows/Fonts/andlso.ttf"),
        ("Dubai", "C:/Windows/Fonts/Dubai-Regular.ttf"),
        ("Noto Naskh Arabic", "C:/Windows/Fonts/NotoNaskhArabic-Regular.ttf"),
        ("Noto Sans Arabic", "C:/Windows/Fonts/NotoSansArabic-Regular.ttf"),
        ("Amiri", "C:/Windows/Fonts/amiri-regular.ttf"),
        ("Cairo", "C:/Windows/Fonts/Cairo-Regular.ttf"),
    ],
    "Darwin": [
        ("Tahoma", "/Library/Fonts/Tahoma.ttf"),
        ("Geeza Pro", "/System/Library/Fonts/GeezaPro.ttc"),
        ("Arial", "/Library/Fonts/Arial.ttf"),
    ],
    "Linux": [
        ("Noto Naskh Arabic", "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"),
        ("Noto Sans Arabic", "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf"),
        ("Amiri", "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf"),
        ("Tahoma", "/usr/share/fonts/truetype/msttcorefonts/Tahoma.ttf"),
        ("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ],
}


def find_arabic_fonts():
    print("[Font] البحث...")
    t0 = time.time()
    system = platform.system()
    found = {}

    for name, path in KNOWN_ARABIC_FONTS.get(system, []):
        if os.path.exists(path):
            try:
                fm.fontManager.addfont(path)
                fp = fm.FontProperties(fname=path)
                found[fp.get_name()] = path
            except Exception:
                pass

    if not found:
        patterns = {
            "Windows": ["C:/Windows/Fonts/*.ttf"],
            "Darwin": ["/Library/Fonts/*.ttf", "/System/Library/Fonts/*.ttf"],
        }.get(system, ["/usr/share/fonts/**/*.ttf"])
        keywords = ["naskh", "arabic", "amiri", "cairo", "tahoma", "segoe"]
        for pattern in patterns:
            try:
                for path in glob.glob(pattern, recursive=True)[:500]:
                    fname = os.path.basename(path).lower()
                    if any(k in fname for k in keywords):
                        try:
                            fm.fontManager.addfont(path)
                            fp = fm.FontProperties(fname=path)
                            found[fp.get_name()] = path
                        except Exception:
                            pass
            except Exception:
                pass

    print(f"[Font] {len(found)} خط في {time.time() - t0:.2f}ث")
    return found


CURRENT_FONT_NAME = None
CURRENT_FONT_PATH = None
TABLE_HEADER_COLOR = "#1e3a5f"
TABLE_CELL_COLOR = "#f0f4f8"


def set_current_font(font_name, font_path):
    global CURRENT_FONT_NAME, CURRENT_FONT_PATH
    try:
        if font_path and os.path.exists(font_path):
            fm.fontManager.addfont(font_path)
            CURRENT_FONT_NAME = font_name
            CURRENT_FONT_PATH = font_path
            matplotlib.rcParams["font.family"] = font_name
            matplotlib.rcParams["axes.unicode_minus"] = False
            return True
    except Exception as e:
        print(f"[Font] {e}")
    return False


def get_arabic_font(size=10):
    if CURRENT_FONT_PATH and os.path.exists(CURRENT_FONT_PATH):
        try:
            return fm.FontProperties(fname=CURRENT_FONT_PATH, size=size)
        except Exception:
            pass
    return fm.FontProperties(size=size)


_arabic_fonts = find_arabic_fonts()
if _arabic_fonts:
    for fname, fpath in _arabic_fonts.items():
        if set_current_font(fname, fpath):
            print(f"[Font] ✓ {fname}")
            break


# ============================================================
# الحسابات
# ============================================================
geod = Geod(ellps="WGS84")


def clean_number(v):
    s = str(v).strip().replace("،", ".").replace(",", ".").replace("−", "-")
    return float(s)


def precise_measurements(corners):
    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    area, perimeter = geod.polygon_area_perimeter(lons, lats)

    def dist(p1, p2):
        _, _, d = geod.inv(p1[1], p1[0], p2[1], p2[0])
        return d

    return {
        "area": abs(area),
        "perimeter": perimeter,
        "top": dist(corners[0], corners[1]),
        "right": dist(corners[0], corners[3]),
        "bottom": dist(corners[3], corners[2]),
        "left": dist(corners[1], corners[2]),
    }


def move_point_along_line(p1, p2, new_distance):
    _, azimuth, _ = geod.inv(p1[1], p1[0], p2[1], p2[0])
    lon_new, lat_new, _ = geod.fwd(p1[1], p1[0], azimuth, new_distance)
    return (lat_new, lon_new)


def get_utm_epsg(lat, lon):
    zone = int((lon + 180) / 6) + 1
    zone = max(1, min(60, zone))
    return 32600 + zone if lat >= 0 else 32700 + zone


def to_utm(corners):
    lat_c = sum(c[0] for c in corners) / len(corners)
    lon_c = sum(c[1] for c in corners) / len(corners)
    epsg = get_utm_epsg(lat_c, lon_c)
    t = Transformer.from_crs("EPSG:4326", CRS.from_epsg(epsg),
                              always_xy=True)
    return [t.transform(lon, lat) for lat, lon in corners], epsg


def compute_site_center_and_radius(corners, margin=1.15):
    lats = [c[0] for c in corners]
    lons = [c[1] for c in corners]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    max_dist = 0
    for lat, lon in corners:
        _, _, d = geod.inv(center_lon, center_lat, lon, lat)
        if d > max_dist:
            max_dist = d
    return center_lat, center_lon, max_dist * margin


def lonlat_to_webmercator(lon, lat):
    R = 6378137.0
    x = math.radians(lon) * R
    lat = max(min(lat, 85.05112878), -85.05112878)
    y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def webmercator_to_lonlat(x, y):
    R = 6378137.0
    lon = math.degrees(x / R)
    lat = math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
    return lon, lat


# ============================================================
# جلب التايلات
# ============================================================
def _merc_to_tile(x, y, z):
    R = 6378137.0
    origin_shift = math.pi * R
    n = 2.0 ** z
    return ((x + origin_shift) / (2 * origin_shift) * n,
            (origin_shift - y) / (2 * origin_shift) * n)


def tile_to_merc(tx, ty, z):
    R = 6378137.0
    origin_shift = math.pi * R
    n = 2.0 ** z
    x = tx / n * (2 * origin_shift) - origin_shift
    y = origin_shift - ty / n * (2 * origin_shift)
    return x, y


def fetch_tile_with_cache(tile_url, cache_path, headers=None):
    if cache_path.exists():
        try:
            size = cache_path.stat().st_size
            if size > 200:
                img = Image.open(cache_path).convert("RGB")
                return img, True
            else:
                try:
                    cache_path.unlink()
                except Exception:
                    pass
        except Exception:
            try:
                cache_path.unlink()
            except Exception:
                pass

    try:
        if headers is None:
            headers = {"User-Agent": "CroquiProSurveyor/9.3"}
        r = requests.get(tile_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None, False

        data = r.content
        if not data or len(data) < 200:
            return None, False

        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            print(f"[Tile] صورة معطوبة: {e}")
            return None, False

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            if cache_path.exists():
                try:
                    if cache_path.stat().st_size < 200:
                        cache_path.unlink()
                except Exception:
                    pass

            with open(cache_path, "wb") as f:
                f.write(data)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
        except Exception as e:
            print(f"[Cache] ✗ فشل الحفظ: {e}")

        return img, False

    except requests.exceptions.Timeout:
        return None, False
    except Exception as e:
        print(f"[Tile] خطأ: {e}")
        return None, False


def fetch_tiles_generic(center_lon, center_lat, radius_m, size_px,
                         zoom, url_template, source_name="osm",
                         headers=None, max_tiles=200,
                         progress_cb=None, cancel_event=None):
    try:
        cx, cy = lonlat_to_webmercator(center_lon, center_lat)
        x0, y0 = cx - radius_m, cy - radius_m
        x1, y1 = cx + radius_m, cy + radius_m

        tx0, ty0 = _merc_to_tile(x0, y1, zoom)
        tx1, ty1 = _merc_to_tile(x1, y0, zoom)

        tile_x0, tile_y0 = int(math.floor(tx0)), int(math.floor(ty0))
        tile_x1, tile_y1 = int(math.floor(tx1)), int(math.floor(ty1))

        tiles_x = tile_x1 - tile_x0 + 1
        tiles_y = tile_y1 - tile_y0 + 1

        if tiles_x * tiles_y > max_tiles:
            return fetch_tiles_generic(center_lon, center_lat, radius_m,
                                        size_px, zoom - 1, url_template,
                                        source_name, headers, max_tiles,
                                        progress_cb, cancel_event)

        canvas = Image.new("RGB", (tiles_x * 256, tiles_y * 256),
                            (240, 240, 240))

        total = tiles_x * tiles_y
        done = 0
        hits = 0

        for tx in range(tile_x0, tile_x1 + 1):
            for ty in range(tile_y0, tile_y1 + 1):
                if cancel_event and cancel_event.is_set():
                    return None, 0, 0, 0, 0

                url = url_template.format(z=zoom, x=tx, y=ty)
                cache_path = get_cache_path(zoom, tx, ty, source_name)

                img, from_cache = fetch_tile_with_cache(url, cache_path, headers)
                if from_cache:
                    hits += 1
                if img is not None:
                    canvas.paste(img, ((tx - tile_x0) * 256,
                                        (ty - tile_y0) * 256))

                done += 1
                if progress_cb:
                    progress_cb(done, total,
                                f"{done}/{total} ({hits} كاش)")

        if cancel_event and cancel_event.is_set():
            return None, 0, 0, 0, 0

        px_left = (tx0 - tile_x0) * 256
        px_top = (ty0 - tile_y0) * 256
        px_right = (tx1 - tile_x0) * 256
        px_bottom = (ty1 - tile_y0) * 256

        cropped = canvas.crop((int(px_left), int(px_top),
                                int(px_right), int(px_bottom)))
        cropped = cropped.resize((size_px, size_px), Image.LANCZOS)

        exact_x0, exact_y1 = tile_to_merc(tx0, ty0, zoom)
        exact_x1, exact_y0 = tile_to_merc(tx1, ty1, zoom)

        print(f"[Tiles:{source_name}] z={zoom}  كاش: {hits}/{total}")

        return cropped, exact_x0, exact_y0, exact_x1, exact_y1

    except Exception as e:
        print(f"[Tiles:{source_name}] {e}")
        traceback.print_exc()
        return None, 0, 0, 0, 0


def fetch_osm(center_lon, center_lat, radius_m, size_px=1400, zoom=17,
              progress_cb=None, cancel_event=None):
    url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    headers = {
        "User-Agent": "CroquiProSurveyor/9.3 (Arabic Surveying)",
        "Accept": "image/png,image/*,*/*",
    }
    return fetch_tiles_generic(center_lon, center_lat, radius_m,
                                size_px, zoom, url, "osm", headers, 200,
                                progress_cb, cancel_event)


def fetch_satellite(center_lon, center_lat, radius_m,
                    size_px=1400, zoom=17,
                    progress_cb=None, cancel_event=None):
    url = ("https://server.arcgisonline.com/ArcGIS/rest/"
           "services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
    return fetch_tiles_generic(center_lon, center_lat, radius_m,
                                size_px, zoom, url, "satellite", None, 200,
                                progress_cb, cancel_event)


# ============================================================
# استيراد CSV
# ============================================================
CORNER_ALIASES = {
    "NE": ["north east", "northeast", "north_east", "north-east",
           "شمال شرق", "شمال_شرق", "شمالشرق", "شمال-شرق",
           "ne", "p1", "point 1", "point1", "نقطة 1", "ركن 1"],
    "NW": ["north west", "northwest", "north_west", "north-west",
           "شمال غرب", "شمال_غرب", "شمالغرب", "شمال-غرب",
           "nw", "p2", "point 2", "point2", "نقطة 2", "ركن 2"],
    "SW": ["south west", "southwest", "south_west", "south-west",
           "جنوب غرب", "جنوب_غرب", "جنوبغرب", "جنوب-غرب",
           "sw", "p3", "point 3", "point3", "نقطة 3", "ركن 3"],
    "SE": ["south east", "southeast", "south_east", "south-east",
           "جنوب شرق", "جنوب_شرق", "جنوبشرق", "جنوب-شرق",
           "se", "p4", "point 4", "point4", "نقطة 4", "ركن 4"],
}


def _normalize_arabic(s):
    s = str(s).strip()
    s = re.sub(r"[\u064B-\u0652]", "", s)
    s = re.sub(r"\s+", " ", s)
    s = s.replace("_", " ").replace("-", " ")
    return s.lower()


def _detect_corner_key(name):
    rn = _normalize_arabic(name)
    for key, aliases in CORNER_ALIASES.items():
        for a in aliases:
            if rn == _normalize_arabic(a):
                return key
    for key, aliases in CORNER_ALIASES.items():
        for a in aliases:
            na = _normalize_arabic(a)
            if len(na) >= 3 and na in rn:
                return key
    return None


def _detect_separator(line):
    if "\t" in line:
        return "\t"
    if "," in line:
        return ","
    if ";" in line:
        return ";"
    return None


def _parse_line(line):
    line = line.strip()
    if not line:
        return []
    sep = _detect_separator(line)
    if sep:
        parts = [p.strip() for p in line.split(sep)]
    else:
        parts = [p.strip() for p in line.split()]
    return [p for p in parts if p]


def _is_number(s):
    try:
        float(str(s).replace(",", ".").replace("،", "."))
        return True
    except Exception:
        return False


def read_corners_from_csv(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        raw_lines = [ln for ln in f.read().splitlines() if ln.strip()]

    if not raw_lines:
        raise ValueError("الملف فارغ")

    all_rows = []
    for ln in raw_lines:
        parts = _parse_line(ln)
        if parts:
            all_rows.append(parts)

    if not all_rows:
        raise ValueError("لا توجد بيانات")

    first = all_rows[0]
    has_header = False
    if len(first) >= 3:
        if sum(1 for x in first if _is_number(x)) < 2:
            has_header = True

    data_rows = all_rows[1:] if has_header else all_rows

    if len(data_rows) < 4:
        raise ValueError(f"يجب 4 صفوف (وُجد {len(data_rows)})")

    parsed = []
    for i, parts in enumerate(data_rows, 1):
        if len(parts) < 3:
            continue
        name = parts[0]
        numbers = [p for p in parts[1:] if _is_number(p)]
        if len(numbers) < 2:
            numbers = [p for p in parts if _is_number(p)]
            name_candidates = [p for p in parts if not _is_number(p)]
            name = name_candidates[0] if name_candidates else f"P{i}"
        if len(numbers) < 2:
            continue
        try:
            v1 = clean_number(numbers[0])
            v2 = clean_number(numbers[1])
        except Exception:
            continue
        if -90 <= v1 <= 90 and -180 <= v2 <= 180:
            lat, lon = v1, v2
        elif -90 <= v2 <= 90 and -180 <= v1 <= 180:
            lat, lon = v2, v1
        else:
            raise ValueError(f"صف {i}: خارج النطاق")
        parsed.append({"name": name, "lat": lat, "lon": lon, "row": i})

    if len(parsed) < 4:
        raise ValueError(f"{len(parsed)} زوايا فقط")

    return order_corners_smart(parsed)


def order_corners_smart(rows):
    matched = {}
    for row in rows:
        key = _detect_corner_key(row["name"])
        if key and key not in matched:
            matched[key] = row

    if len(matched) == 4:
        return [
            (matched["NE"]["lat"], matched["NE"]["lon"]),
            (matched["NW"]["lat"], matched["NW"]["lon"]),
            (matched["SW"]["lat"], matched["SW"]["lon"]),
            (matched["SE"]["lat"], matched["SE"]["lon"]),
        ]

    if len(rows) >= 4:
        four = rows[:4]
        lats = [r["lat"] for r in four]
        lons = [r["lon"] for r in four]
        lat_c = sum(lats) / 4
        lon_c = sum(lons) / 4

        ne = nw = sw = se = None
        for r in four:
            if r["lat"] >= lat_c and r["lon"] >= lon_c:
                ne = r
            elif r["lat"] >= lat_c and r["lon"] < lon_c:
                nw = r
            elif r["lat"] < lat_c and r["lon"] < lon_c:
                sw = r
            elif r["lat"] < lat_c and r["lon"] >= lon_c:
                se = r

        if all([ne, nw, sw, se]):
            return [
                (ne["lat"], ne["lon"]),
                (nw["lat"], nw["lon"]),
                (sw["lat"], sw["lon"]),
                (se["lat"], se["lon"]),
            ]

    raise ValueError("تعذر ترتيب الزوايا")


# ============================================================
# الألوان والثوابت
# ============================================================
C_BORDER = "#c00000"
C_TABLE_BORDER = "#333333"
C_SEA = "#1a4d6e"
C_ROAD = "#4a4a4a"

PIN_COLORS = ["#e31e24", "#2d6a4f", "#0066cc", "#f6a623"]
PIN_NAMES_AR = ["شمال شرق", "شمال غرب", "جنوب غرب", "جنوب شرق"]
PIN_NAMES_EN = ["NE", "NW", "SW", "SE"]

EDGE_LABELS_AR = {
    "top": "شمالي (P1↔P2)",
    "right": "شرقي (P1↔P4)",
    "bottom": "جنوبي (P3↔P4)",
    "left": "غربي (P2↔P3)",
}
EDGE_NAMES_AR = {
    "top": "الشمالي",
    "right": "الشرقي",
    "bottom": "الجنوبي",
    "left": "الغربي",
}


# ============================================================
# المُصمّم
# ============================================================
class CroquiDesigner:
    def __init__(self):
        self.points = []
        self.pin = {"lat": None, "lon": None, "radius": 200}
        self.measurements = None
        self.utm_coords = None
        self.utm_epsg = None
        self.basemap = None
        self.basemap_bounds = None
        self.satellite = None
        self.sat_bounds = None

        self.table_header_color = TABLE_HEADER_COLOR
        self.table_cell_color = TABLE_CELL_COLOR

        self.custom_logo_path = None
        self._logo_image = None

        self.has_road = False
        self.road_edge = "bottom"
        self.road_offset = 0.12
        self.has_sea = False
        self.sea_edge = "top"
        self.sea_offset = 0.12

        self.site_info = {
            "type": "أرض مخصصة لمجمع سياحي",
            "area": 0, "length": 0, "width": 0,
            "shape": "مستطيل",
            "sea_facing": "",
            "north_facing": "",
            "south_facing": "",
            "east_facing": "",
            "west_facing": "",
        }
        self.project_info = {
            "engineer": "م. وائل عبدالله",
            "specialty": "مهندس مدني - مساح",
            "date": datetime.now().strftime("%Y - %m - %d"),
            "license": "هيئة المهندسين",
            "logo_text": "مكتب الهندسة المساحية",
            "logo_sub": "رفع مساحي - تقسيم أراضي - كروكيات",
        }

    def set_corners(self, corners):
        names = ["1", "2", "3", "4"]
        self.points = [(names[i], lat, lon)
                       for i, (lat, lon) in enumerate(corners)]
        self.measurements = precise_measurements(corners)
        self.utm_coords, self.utm_epsg = to_utm(corners)
        self.site_info["area"] = round(self.measurements["area"], 2)
        self.site_info["length"] = round(
            max(self.measurements["top"], self.measurements["bottom"]), 2)
        self.site_info["width"] = round(
            max(self.measurements["left"], self.measurements["right"]), 2)

    def set_pin(self, lat, lon, radius):
        self.pin = {"lat": lat, "lon": lon, "radius": radius}

    def set_table_colors(self, header_color, cell_color):
        self.table_header_color = header_color
        self.table_cell_color = cell_color

    def set_custom_logo(self, path):
        self.custom_logo_path = path
        self._logo_image = None

    def set_road_sea(self, has_road, road_edge, has_sea, sea_edge,
                     road_offset=0.12, sea_offset=0.12):
        self.has_road = has_road
        self.road_edge = road_edge
        self.has_sea = has_sea
        self.sea_edge = sea_edge
        self.road_offset = road_offset
        self.sea_offset = sea_offset

    def load_basemap(self, progress_cb=None, cancel_event=None):
        if self.pin["lat"] is None:
            return False
        img, x0, y0, x1, y1 = fetch_osm(
            self.pin["lon"], self.pin["lat"],
            self.pin["radius"], size_px=1400, zoom=17,
            progress_cb=progress_cb, cancel_event=cancel_event)
        if img is None:
            return False
        self.basemap = img
        self.basemap_bounds = (x0, y0, x1, y1)
        return True

    def load_satellite(self, progress_cb=None, cancel_event=None):
        if self.pin["lat"] is None:
            return False
        img, x0, y0, x1, y1 = fetch_satellite(
            self.pin["lon"], self.pin["lat"],
            self.pin["radius"], size_px=1400, zoom=17,
            progress_cb=progress_cb, cancel_event=cancel_event)
        if img is None:
            return False
        self.satellite = img
        self.sat_bounds = (x0, y0, x1, y1)
        return True

    def draw_map(self, ax):
        ax.set_facecolor("#ffffff")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(C_TABLE_BORDER)
            spine.set_linewidth(1.2)

        if self.basemap is None or self.basemap_bounds is None:
            ax.text(0.5, 0.5, "لا توجد خريطة أساس",
                    ha="center", va="center", transform=ax.transAxes,
                    fontproperties=get_arabic_font(14), color="#888")
            return

        x0, y0, x1, y1 = self.basemap_bounds
        ax.imshow(self.basemap, extent=[x0, x1, y0, y1],
                  aspect="equal", zorder=0, interpolation="bilinear")

        def merc(lat, lon):
            return lonlat_to_webmercator(lon, lat)

        corner_merc = [merc(p[1], p[2]) for p in self.points]

        order = [0, 1, 2, 3, 0]
        xs = [corner_merc[i][0] for i in order]
        ys = [corner_merc[i][1] for i in order]
        ax.plot(xs, ys, color=C_BORDER, lw=2.2, zorder=10)

        cx = sum(p[0] for p in corner_merc) / 4
        cy = sum(p[1] for p in corner_merc) / 4
        ax.plot([cx, cx],
                [min(p[1] for p in corner_merc), max(p[1] for p in corner_merc)],
                color="#555", lw=0.7, ls=(0, (6, 4)), zorder=6)
        ax.plot([min(p[0] for p in corner_merc), max(p[0] for p in corner_merc)],
                [cy, cy],
                color="#555", lw=0.7, ls=(0, (6, 4)), zorder=6)

        for i, (x, y) in enumerate(corner_merc):
            ax.plot(x, y, "o", markersize=10,
                    markerfacecolor="white", markeredgecolor=C_BORDER,
                    markeredgewidth=2, zorder=12)
            ax.plot(x, y, "o", markersize=4,
                    color=C_BORDER, zorder=13)
            ax.annotate(str(i + 1), (x, y),
                        xytext=(12, 12), textcoords="offset points",
                        fontsize=11, fontweight="bold", color=C_BORDER,
                        bbox=dict(boxstyle="circle,pad=0.3",
                                  facecolor="white",
                                  edgecolor=C_BORDER, linewidth=1.5),
                        zorder=15)

        self._draw_dimension(ax, corner_merc[0], corner_merc[1],
                              self.measurements["top"], "up")
        self._draw_dimension(ax, corner_merc[2], corner_merc[3],
                              self.measurements["bottom"], "down")
        self._draw_dimension(ax, corner_merc[0], corner_merc[3],
                              self.measurements["right"], "right")
        self._draw_dimension(ax, corner_merc[1], corner_merc[2],
                              self.measurements["left"], "left")

        span_m = max(max(xs) - min(xs), max(ys) - min(ys))
        pin_h = span_m * 0.08
        ax.plot(cx, cy + pin_h * 0.5, marker="v", markersize=22,
                markerfacecolor=C_BORDER, markeredgecolor="white",
                markeredgewidth=2, zorder=20)
        ax.plot(cx, cy + pin_h * 1.2, marker="o", markersize=8,
                markerfacecolor=C_BORDER, markeredgecolor="white",
                markeredgewidth=1.5, zorder=21)

        box = dict(boxstyle="round,pad=0.4", facecolor="white",
                    edgecolor=C_BORDER, linewidth=1, alpha=0.95)
        ax.text(cx, cy - pin_h * 0.5, "المساحة الكلية",
                ha="center", va="top",
                fontproperties=get_arabic_font(11), fontweight="bold",
                color="#1a1a1a", bbox=box, zorder=22)
        ax.text(cx, cy - pin_h * 1.3,
                f"{self.measurements['area']:,.2f} م²",
                ha="center", va="top",
                fontproperties=get_arabic_font(13), fontweight="bold",
                color=C_BORDER, bbox=box, zorder=22)

        self._draw_north_arrow(ax, x0, x1, y0, y1)

        if self.has_sea:
            self._draw_side_feature(ax, corner_merc, self.sea_edge,
                                     "🌊 البحر", C_SEA, is_sea=True,
                                     offset_factor=self.sea_offset)
        if self.has_road:
            self._draw_side_feature(ax, corner_merc, self.road_edge,
                                     "الطريق العام (RR01)", C_ROAD,
                                     is_sea=False,
                                     offset_factor=self.road_offset)

    def _draw_side_feature(self, ax, corner_merc, edge, label, color,
                            is_sea=True, offset_factor=0.12):
        idx_map = {
            "top": (0, 1),
            "right": (0, 3),
            "bottom": (3, 2),
            "left": (1, 2),
        }
        i1, i2 = idx_map[edge]
        p1 = corner_merc[i1]
        p2 = corner_merc[i2]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1:
            return

        nx = -dy / L
        ny = dx / L

        cx = sum(p[0] for p in corner_merc) / 4
        cy = sum(p[1] for p in corner_merc) / 4
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        vx = mx - cx
        vy = my - cy
        if nx * vx + ny * vy < 0:
            nx, ny = -nx, -ny

        width = L * offset_factor

        a1 = (p1[0] + nx * width, p1[1] + ny * width)
        a2 = (p2[0] + nx * width, p2[1] + ny * width)

        if is_sea:
            ax.add_patch(plt.Polygon([p1, p2, a2, a1],
                                       closed=True,
                                       facecolor=color, edgecolor="white",
                                       linewidth=1.5, alpha=0.85,
                                       zorder=7))
        else:
            ax.add_patch(plt.Polygon([p1, p2, a2, a1],
                                       closed=True,
                                       facecolor=color, edgecolor="none",
                                       alpha=0.85, zorder=7))
            mid1 = ((p1[0] + a1[0]) / 2, (p1[1] + a1[1]) / 2)
            mid2 = ((p2[0] + a2[0]) / 2, (p2[1] + a2[1]) / 2)
            ax.plot([mid1[0], mid2[0]], [mid1[1], mid2[1]],
                    color="white", lw=1.5, ls=(0, (12, 10)), zorder=8)

        mx_label = (p1[0] + p2[0] + a1[0] + a2[0]) / 4
        my_label = (p1[1] + p2[1] + a1[1] + a2[1]) / 4
        angle = math.degrees(math.atan2(dy, dx))
        if angle > 90 or angle < -90:
            angle += 180

        ax.text(mx_label, my_label, label,
                ha="center", va="center",
                fontproperties=get_arabic_font(11), fontweight="bold",
                color="white", rotation=angle,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#2c3e50",
                          edgecolor="white", linewidth=1),
                zorder=9)

    def _draw_dimension(self, ax, p1, p2, length, position):
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L < 1:
            return
        offset = L * 0.13

        nx = -dy / L
        ny = dx / L
        if position not in ("right", "up"):
            nx, ny = -nx, -ny

        a = (x1 + nx * offset, y1 + ny * offset)
        b = (x2 + nx * offset, y2 + ny * offset)

        ax.plot([x1, a[0]], [y1, a[1]], color="#777", lw=0.7, zorder=4)
        ax.plot([x2, b[0]], [y2, b[1]], color="#777", lw=0.7, zorder=4)

        ax.annotate("", xy=b, xytext=a,
                    arrowprops=dict(arrowstyle="<|-|>", color="#222",
                                    lw=1.1, shrinkA=0, shrinkB=0,
                                    mutation_scale=12),
                    zorder=5)

        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        angle = math.degrees(math.atan2(dy, dx))
        if angle > 90 or angle < -90:
            angle += 180

        ax.text(mid[0], mid[1], f"{length:.2f} م",
                ha="center", va="center", rotation=angle,
                fontproperties=get_arabic_font(11), fontweight="bold",
                color="#1a1a1a",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#888", linewidth=0.8, alpha=0.95),
                zorder=6)

    def _draw_north_arrow(self, ax, x0, x1, y0, y1):
        w = x1 - x0
        h = y1 - y0
        cxx = x1 - w * 0.10
        cyy = y1 - h * 0.13
        radius = min(w, h) * 0.05

        ax.add_patch(Circle((cxx, cyy), radius,
                             facecolor="white", edgecolor="#1a1a1a",
                             linewidth=1.8, zorder=30))

        top_y = cyy + radius * 0.75
        bot_y = cyy - radius * 0.75
        mid_y = cyy - radius * 0.10
        half_w = radius * 0.32

        ax.fill([cxx, cxx - half_w, cxx, cxx],
                [top_y, mid_y, mid_y, top_y],
                color="#1a1a1a", zorder=31)
        ax.fill([cxx, cxx + half_w, cxx, cxx],
                [top_y, mid_y, mid_y, top_y],
                color="#1a1a1a", zorder=31)
        ax.fill([cxx, cxx - half_w * 0.7, cxx, cxx],
                [mid_y, mid_y - radius * 0.35, bot_y, mid_y],
                color="#888888", zorder=30)
        ax.fill([cxx, cxx + half_w * 0.7, cxx, cxx],
                [mid_y, mid_y - radius * 0.35, bot_y, mid_y],
                color="#888888", zorder=30)

        ax.text(cxx, cyy + radius * 1.35, "N",
                ha="center", va="bottom", fontsize=13,
                fontweight="bold", color="#1a1a1a", zorder=32,
                fontproperties=get_arabic_font(13))

    def draw_side_panel(self, ax):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        self._site_table(ax, 0, 0.60, 1.0, 0.40)
        self._location_map(ax, 0, 0.32, 1.0, 0.28)
        self._legend(ax, 0, 0.12, 1.0, 0.20)
        self._scale_bar(ax, 0, 0.0, 1.0, 0.12)

    def _site_table(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))
        th = 0.075
        ax.add_patch(Rectangle((x0, y0 + h - th), w, th,
                                facecolor=self.table_header_color,
                                edgecolor=C_TABLE_BORDER, linewidth=1.2,
                                transform=ax.transAxes, zorder=3))
        ax.text(x0 + w / 2, y0 + h - th / 2, "بيانات الأرض",
                ha="center", va="center",
                fontproperties=get_arabic_font(11), fontweight="bold",
                color="white", transform=ax.transAxes, zorder=4)

        rows = [
            ("نوع المخطط", self.site_info["type"]),
            ("المساحة", f"{self.site_info['area']:,.2f} م²"),
            ("الطول", f"{self.site_info['length']:.2f} م"),
            ("العرض", f"{self.site_info['width']:.2f} م"),
            ("الشكل", self.site_info["shape"]),
        ]
        for key, label in [
            ("sea_facing", "الواجهة البحرية"),
            ("north_facing", "الواجهة الشمالية"),
            ("south_facing", "الواجهة الجنوبية"),
            ("east_facing", "الواجهة الشرقية"),
            ("west_facing", "الواجهة الغربية"),
        ]:
            if self.site_info.get(key, "").strip():
                rows.append((label, self.site_info[key]))

        rh = (h - th) / len(rows)
        for i, (lbl, val) in enumerate(rows):
            ry = y0 + h - th - (i + 1) * rh
            ax.plot([x0, x0 + w], [ry, ry], color=C_TABLE_BORDER,
                    lw=0.5, transform=ax.transAxes, zorder=3)
            ax.add_patch(Rectangle((x0 + w * 0.55, ry), w * 0.45, rh,
                                    facecolor=self.table_cell_color,
                                    edgecolor=C_TABLE_BORDER, lw=0.5,
                                    transform=ax.transAxes, zorder=3))
            ax.text(x0 + w * 0.775, ry + rh / 2, lbl,
                    ha="center", va="center",
                    fontproperties=get_arabic_font(8.5), fontweight="bold",
                    color="#1a3a5c", transform=ax.transAxes, zorder=4)
            ax.text(x0 + w * 0.27, ry + rh / 2, val,
                    ha="center", va="center",
                    fontproperties=get_arabic_font(8.5), color="#222",
                    transform=ax.transAxes, zorder=4)

    def _location_map(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))
        th = 0.07
        ax.add_patch(Rectangle((x0, y0 + h - th), w, th,
                                facecolor=self.table_header_color,
                                edgecolor=C_TABLE_BORDER, linewidth=1.2,
                                transform=ax.transAxes, zorder=3))
        ax.text(x0 + w / 2, y0 + h - th / 2, "موقع الأرض",
                ha="center", va="center",
                fontproperties=get_arabic_font(9), fontweight="bold",
                color="white", transform=ax.transAxes, zorder=4)

        if self.satellite is None or self.sat_bounds is None:
            return

        mx0, my0, mx1, my1 = self.sat_bounds
        span_x = mx1 - mx0
        span_y = my1 - my0
        if span_x <= 0 or span_y <= 0:
            return

        img_x0 = x0 + 0.008
        img_x1 = x0 + w - 0.008
        img_y0 = y0 + 0.008
        img_y1 = y0 + h - th - 0.008

        ax.imshow(self.satellite,
                  extent=[img_x0, img_x1, img_y0, img_y1],
                  aspect="auto", zorder=2.5)

        def latlon_to_axes(lat, lon):
            x_m, y_m = lonlat_to_webmercator(lon, lat)
            nx = (x_m - mx0) / span_x
            ny = (y_m - my0) / span_y
            ax_x = img_x0 + nx * (img_x1 - img_x0)
            ax_y = img_y0 + ny * (img_y1 - img_y0)
            return ax_x, ax_y

        pts = []
        for point in self.points:
            lat, lon = point[1], point[2]
            ax_x, ax_y = latlon_to_axes(lat, lon)
            pts.append((ax_x, ax_y))

        if len(pts) == 4:
            poly_x = [p[0] for p in pts] + [pts[0][0]]
            poly_y = [p[1] for p in pts] + [pts[0][1]]
            ax.plot(poly_x, poly_y, color=C_BORDER, lw=2, zorder=6)
            ax.fill(poly_x, poly_y, color=C_BORDER, alpha=0.2, zorder=5)

            cx_ax = sum(p[0] for p in pts) / 4
            cy_ax = sum(p[1] for p in pts) / 4
            ax.text(cx_ax, cy_ax, "الأرض",
                    ha="center", va="center",
                    fontproperties=get_arabic_font(8), fontweight="bold",
                    color=C_BORDER,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor=C_BORDER, linewidth=0.8, alpha=0.9),
                    zorder=7)

    def _legend(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))
        th = 0.10
        ax.add_patch(Rectangle((x0, y0 + h - th), w, th,
                                facecolor=self.table_header_color,
                                edgecolor=C_TABLE_BORDER, linewidth=1.2,
                                transform=ax.transAxes, zorder=3))
        ax.text(x0 + w / 2, y0 + h - th / 2, "مفتاح الرموز",
                ha="center", va="center",
                fontproperties=get_arabic_font(9), fontweight="bold",
                color="white", transform=ax.transAxes, zorder=4)

        items = [("red_line", "حدود الأرض"),
                 ("dashed", "محور الأرض (تخيلي)")]
        if self.has_road:
            items.append(("gray", "الطريق العام (RR01)"))
        if self.has_sea:
            items.append(("blue", "البحر"))

        ih = (h - th) / len(items)
        for i, (kind, label) in enumerate(items):
            iy = y0 + h - th - (i + 0.5) * ih
            sx = x0 + w * 0.78
            if kind == "red_line":
                ax.plot([sx, sx + 0.06], [iy, iy], color=C_BORDER,
                        lw=2.2, transform=ax.transAxes, zorder=5)
            elif kind == "dashed":
                ax.plot([sx, sx + 0.06], [iy, iy], color="#555",
                        lw=1, ls=(0, (4, 3)),
                        transform=ax.transAxes, zorder=5)
            elif kind == "gray":
                ax.add_patch(Rectangle((sx, iy - 0.008), 0.06, 0.016,
                                        facecolor=C_ROAD, edgecolor="none",
                                        transform=ax.transAxes, zorder=5))
            elif kind == "blue":
                ax.add_patch(Rectangle((sx, iy - 0.008), 0.06, 0.016,
                                        facecolor=C_SEA, edgecolor="none",
                                        transform=ax.transAxes, zorder=5))
            ax.text(x0 + w * 0.40, iy, label,
                    ha="center", va="center",
                    fontproperties=get_arabic_font(8), color="#222",
                    transform=ax.transAxes, zorder=5)

    def _scale_bar(self, ax, x0, y0, w, h):
        ax.text(x0 + w / 2, y0 + h - 0.015, "مقياس الرسم",
                ha="center", va="top",
                fontproperties=get_arabic_font(9), fontweight="bold",
                color="#1a1a1a", transform=ax.transAxes, zorder=4)

        bounds = self.basemap_bounds or self.sat_bounds
        if bounds:
            span_m = (bounds[2] - bounds[0]) / 5
            for v in [10, 20, 25, 50, 100, 200, 500]:
                if abs(v - span_m) < span_m * 0.3:
                    span_m = v
                    break
            else:
                span_m = round(span_m / 10) * 10
        else:
            span_m = 50

        bar_y = y0 + h * 0.35
        bar_x0 = x0 + w * 0.15
        bar_x1 = x0 + w * 0.85
        bw = (bar_x1 - bar_x0) / 5

        for i in range(5):
            c = "#1a1a1a" if i % 2 == 0 else "white"
            ax.add_patch(Rectangle((bar_x0 + i * bw, bar_y), bw, 0.015,
                                    facecolor=c, edgecolor="#1a1a1a",
                                    linewidth=0.8,
                                    transform=ax.transAxes, zorder=5))

        steps = [0, span_m * 0.2, span_m * 0.4, span_m * 0.6,
                 span_m * 0.8, span_m]
        for i, s in enumerate(steps):
            ax.text(bar_x0 + i * bw, bar_y + 0.022,
                    f"{s:.0f}", ha="center", va="bottom",
                    fontsize=7, color="#1a1a1a",
                    transform=ax.transAxes, zorder=5)

        ax.text(bar_x1 + 0.015, bar_y + 0.008, "م",
                ha="left", va="center",
                fontproperties=get_arabic_font(8), fontweight="bold",
                color="#1a1a1a", transform=ax.transAxes, zorder=5)

    def draw_bottom_panel(self, ax):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        self._logo(ax, 0.0, 0.0, 0.22, 1.0)
        self._coords_table(ax, 0.225, 0.0, 0.35, 1.0)
        self._notes(ax, 0.58, 0.0, 0.22, 1.0)
        self._engineer(ax, 0.805, 0.0, 0.195, 1.0)

    def _logo(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))

        if self.custom_logo_path and os.path.exists(self.custom_logo_path):
            try:
                if self._logo_image is None:
                    self._logo_image = plt.imread(self.custom_logo_path)
                logo_ax = ax.inset_axes([x0 + 0.02, y0 + h * 0.38,
                                          w - 0.04, h * 0.55])
                logo_ax.imshow(self._logo_image)
                logo_ax.axis("off")
            except Exception:
                self._draw_default_logo_icon(ax, x0, y0, w, h)
        else:
            self._draw_default_logo_icon(ax, x0, y0, w, h)

        cx = x0 + w / 2
        ax.text(cx, y0 + h * 0.28, self.project_info["logo_text"],
                ha="center", va="center",
                fontproperties=get_arabic_font(9), fontweight="bold",
                color="#2b3a4a", transform=ax.transAxes, zorder=5,
                linespacing=1.3)
        ax.text(cx, y0 + h * 0.13, self.project_info["logo_sub"],
                ha="center", va="center",
                fontproperties=get_arabic_font(7), color="#555",
                transform=ax.transAxes, zorder=5,
                linespacing=1.3)

    def _draw_default_logo_icon(self, ax, x0, y0, w, h):
        cx = x0 + w / 2
        cy = y0 + h * 0.68
        tri = plt.Polygon([(cx - 0.06, cy - 0.05),
                            (cx + 0.06, cy - 0.05),
                            (cx, cy + 0.08)],
                          closed=True, facecolor="none",
                          edgecolor="#2b3a4a", linewidth=2,
                          transform=ax.transAxes, zorder=3)
        ax.add_patch(tri)
        ax.add_patch(plt.Circle((cx, cy + 0.01), 0.018,
                                 facecolor="#2b3a4a", edgecolor="none",
                                 transform=ax.transAxes, zorder=4))
        ax.plot([cx - 0.08, cx + 0.08], [cy - 0.08, cy - 0.08],
                color="#2b3a4a", lw=2,
                transform=ax.transAxes, zorder=3)

    def _coords_table(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))
        th = 0.20
        ax.add_patch(Rectangle((x0, y0 + h - th), w, th,
                                facecolor=self.table_header_color,
                                edgecolor=C_TABLE_BORDER, linewidth=1.2,
                                transform=ax.transAxes, zorder=3))
        ax.text(x0 + w / 2, y0 + h - th / 2,
                "إحداثيات أركان الأرض",
                ha="center", va="center",
                fontproperties=get_arabic_font(9), fontweight="bold",
                color="white", transform=ax.transAxes, zorder=4)

        hh = 0.18
        hy = y0 + h - th - hh
        cw = [0.16, 0.42, 0.42]
        cx_ = [x0, x0 + cw[0] * w, x0 + (cw[0] + cw[1]) * w]
        headers = ["ركن", "E (شرق)", "N (شمال)"]
        for cx, w_, t in zip(cx_, cw, headers):
            ax.add_patch(Rectangle((cx, hy), w_ * w, hh,
                                    facecolor=self.table_cell_color,
                                    edgecolor=C_TABLE_BORDER, lw=0.5,
                                    transform=ax.transAxes, zorder=3))
            ax.text(cx + w_ * w / 2, hy + hh / 2, t,
                    ha="center", va="center",
                    fontproperties=get_arabic_font(7.5), fontweight="bold",
                    color="#1a3a5c", transform=ax.transAxes, zorder=4)

        nr = 4
        rh = (hy - y0) / nr
        coords = self.utm_coords
        for r in range(nr):
            ry = hy - (r + 1) * rh
            for j, (cx, w_) in enumerate(zip(cx_, cw)):
                ax.add_patch(Rectangle((cx, ry), w_ * w, rh,
                                        facecolor="white",
                                        edgecolor=C_TABLE_BORDER, lw=0.5,
                                        transform=ax.transAxes, zorder=3))
                if j == 0:
                    txt = str(r + 1)
                else:
                    val = coords[r][j - 1] if coords else 0
                    txt = f"{val:,.3f}"
                ax.text(cx + w_ * w / 2, ry + rh / 2, txt,
                        ha="center", va="center",
                        fontproperties=get_arabic_font(7.5),
                        fontweight="bold" if j == 0 else "normal",
                        color="#1a1a1a",
                        transform=ax.transAxes, zorder=4)

        if self.utm_epsg:
            z = self.utm_epsg - (32600 if self.utm_epsg < 32700 else 32700)
            h_ = "N" if self.utm_epsg < 32700 else "S"
            txt = f"WGS 84 / UTM Zone {z}{h_}"
        else:
            txt = "WGS 84"
        ax.text(x0 + w / 2, y0 + 0.01, txt,
                ha="center", va="bottom",
                fontproperties=get_arabic_font(7), fontweight="bold",
                color="#1a3a5c", transform=ax.transAxes, zorder=4)

    def _notes(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))
        th = 0.20
        ax.add_patch(Rectangle((x0, y0 + h - th), w, th,
                                facecolor=self.table_header_color,
                                edgecolor=C_TABLE_BORDER, linewidth=1.2,
                                transform=ax.transAxes, zorder=3))
        ax.text(x0 + w / 2, y0 + h - th / 2, "ملاحظات عامة",
                ha="center", va="center",
                fontproperties=get_arabic_font(9), fontweight="bold",
                color="white", transform=ax.transAxes, zorder=4)

        notes = [
            "1. المخطط مقدم كروكي مبدئي استناداً إلى الرفع المساحي.",
            "2. الأبعاد محسوبة بدقة جيوديسية (WGS84).",
            "3. الحدود النهائية تتطلب تثبيت ميداني.",
            "4. المسؤولية القانونية على المالك.",
        ]
        txt = "\n".join(notes)
        ax.text(x0 + w - 0.01, y0 + h - th - 0.02, txt,
                ha="right", va="top",
                fontproperties=get_arabic_font(7), color="#222",
                transform=ax.transAxes, zorder=4, linespacing=1.6)

    def _engineer(self, ax, x0, y0, w, h):
        ax.add_patch(Rectangle((x0, y0), w, h, facecolor="white",
                                edgecolor=C_TABLE_BORDER, linewidth=1.5,
                                transform=ax.transAxes, zorder=2))

        ax.text(x0 + w / 2, y0 + h * 0.78,
                "المهندس المسؤول",
                ha="center", va="center",
                fontproperties=get_arabic_font(7.5), color="#666",
                transform=ax.transAxes, zorder=4)

        ax.text(x0 + w / 2, y0 + h * 0.63,
                self.project_info["engineer"],
                ha="center", va="center",
                fontproperties=get_arabic_font(11), fontweight="bold",
                color="#1a1a1a", transform=ax.transAxes, zorder=4)

        ax.text(x0 + w / 2, y0 + h * 0.50,
                self.project_info["specialty"],
                ha="center", va="center",
                fontproperties=get_arabic_font(8), color="#555",
                transform=ax.transAxes, zorder=4)

        ax.plot([x0 + 0.015, x0 + w - 0.015], [y0 + h * 0.42, y0 + h * 0.42],
                color="#aaa", lw=0.7, transform=ax.transAxes, zorder=3)

        ax.text(x0 + w / 2, y0 + h * 0.32,
                f"رقم الترخيص: {self.project_info['license']}",
                ha="center", va="center",
                fontproperties=get_arabic_font(7), color="#666",
                transform=ax.transAxes, zorder=4)

        ax.text(x0 + w / 2, y0 + h * 0.18,
                f"التاريخ: {self.project_info['date']}",
                ha="center", va="center",
                fontproperties=get_arabic_font(8), fontweight="bold",
                color="#1a1a1a", transform=ax.transAxes, zorder=4)

    def build_figure(self, fig, dpi=150):
        fig.patch.set_facecolor("white")
        gs = GridSpec(2, 2, figure=fig,
                      width_ratios=[1.55, 1.0],
                      height_ratios=[1.0, 0.30],
                      left=0.008, right=0.992,
                      top=0.992, bottom=0.008,
                      wspace=0.008, hspace=0.008)
        ax_map = fig.add_subplot(gs[0, 0])
        ax_side = fig.add_subplot(gs[0, 1])
        ax_bottom = fig.add_subplot(gs[1, :])

        self.draw_map(ax_map)
        self.draw_side_panel(ax_side)
        self.draw_bottom_panel(ax_bottom)


# ============================================================
# تصدير DXF
# ============================================================
def export_dxf(path, corners_utm, epsg, measurements, site_info,
                engineer, scale=1.0):
    try:
        import ezdxf
    except ImportError:
        raise ImportError("شغّل: pip install ezdxf")

    doc = ezdxf.new("R2010", setup=True)
    msp = doc.modelspace()

    doc.layers.add("BOUNDARY", color=1)
    doc.layers.add("DIMENSIONS", color=3)
    doc.layers.add("POINTS", color=5)
    doc.layers.add("TEXT", color=7)
    doc.layers.add("AXIS", color=8)

    if corners_utm:
        ox = corners_utm[0][0]
        oy = corners_utm[0][1]
    else:
        ox, oy = 0, 0

    local = [(x - ox, y - oy) for x, y in corners_utm]
    local_scaled = [(x * scale, y * scale) for x, y in local]

    pts = local_scaled + [local_scaled[0]]
    msp.add_lwpolyline(pts, dxfattribs={"layer": "BOUNDARY", "closed": True})

    for i, (x, y) in enumerate(local_scaled):
        msp.add_circle((x, y), radius=0.5, dxfattribs={"layer": "POINTS"})
        msp.add_text(f"P{i+1}",
                      dxfattribs={"layer": "TEXT", "height": 1.5}
                      ).set_placement((x + 1, y + 1))

    def dim(p1, p2, label):
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        msp.add_line(p1, p2, dxfattribs={"layer": "DIMENSIONS"})
        msp.add_text(label,
                      dxfattribs={"layer": "DIMENSIONS", "height": 1.2}
                      ).set_placement((mx, my + 1.5))

    if len(local_scaled) == 4:
        dim(local_scaled[0], local_scaled[1], f"{measurements['top']:.2f}m")
        dim(local_scaled[2], local_scaled[3], f"{measurements['bottom']:.2f}m")
        dim(local_scaled[0], local_scaled[3], f"{measurements['right']:.2f}m")
        dim(local_scaled[1], local_scaled[2], f"{measurements['left']:.2f}m")

    if local_scaled:
        cx = sum(p[0] for p in local_scaled) / 4
        cy = sum(p[1] for p in local_scaled) / 4
        xs = [p[0] for p in local_scaled]
        ys = [p[1] for p in local_scaled]
        msp.add_line((cx, min(ys) - 5), (cx, max(ys) + 5),
                      dxfattribs={"layer": "AXIS", "linetype": "DASHED"})
        msp.add_line((min(xs) - 5, cy), (max(xs) + 5, cy),
                      dxfattribs={"layer": "AXIS", "linetype": "DASHED"})
        msp.add_text(f"AREA = {measurements['area']:.2f} m2",
                      dxfattribs={"layer": "TEXT", "height": 2.0}
                      ).set_placement((cx - 5, cy))

    if local_scaled:
        info_y = min(ys) - 15
        info_lines = [
            f"PROJECT: {site_info.get('type', '')}",
            f"AREA: {measurements['area']:.2f} m2",
            f"PERIMETER: {measurements['perimeter']:.2f} m",
            f"CRS: EPSG:{epsg} (WGS84 / UTM)",
            f"ENGINEER: {engineer}",
            f"DATE: {datetime.now().strftime('%Y-%m-%d')}",
        ]
        for k, line in enumerate(info_lines):
            msp.add_text(line,
                          dxfattribs={"layer": "TEXT", "height": 1.5}
                          ).set_placement((min(xs), info_y - k * 3))

    doc.saveas(path)
    return path


# ============================================================
# ProgressWindow
# ============================================================
class ProgressWindow:
    def __init__(self, parent, title="⏳ جاري العمل", modal=True):
        self.parent = parent
        self.cancelled = False
        self.finished = False

        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.configure(bg="white")
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", self._on_cancel)
        if modal:
            self.win.transient(parent)

        w, h = 480, 220
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(self.win, text=title, font=("Segoe UI", 14, "bold"),
                 bg="white", fg="#1e3a5f").pack(pady=(18, 5))

        self.status_label = tk.Label(self.win, text="جارٍ التحضير...",
                                      font=("Segoe UI", 10),
                                      bg="white", fg="#333",
                                      wraplength=440, justify="center")
        self.status_label.pack(pady=(5, 10))

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#e0e6ed",
                        background="#1e88e5",
                        thickness=22,
                        borderwidth=0)

        self.progress = ttk.Progressbar(
            self.win, style="Custom.Horizontal.TProgressbar",
            orient="horizontal", length=420, mode="determinate",
            maximum=100)
        self.progress.pack(pady=5)

        self.percent_label = tk.Label(self.win, text="0%",
                                       font=("Segoe UI", 11, "bold"),
                                       bg="white", fg="#1e88e5")
        self.percent_label.pack(pady=(2, 10))

        self.cancel_btn = tk.Button(self.win, text="إلغاء",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="#e53935", fg="white",
                                     activebackground="#c62828",
                                     activeforeground="white",
                                     relief="flat", padx=25, pady=6,
                                     command=self._on_cancel)
        self.cancel_btn.pack(pady=(0, 15))

        self.win.update_idletasks()

    def update(self, percent, message=""):
        if self.finished:
            return
        try:
            p = max(0, min(100, int(percent)))
            self.progress["value"] = p
            self.percent_label.config(text=f"{p}%")
            if message:
                self.status_label.config(text=message)
            self.win.update_idletasks()
        except Exception:
            pass

    def _on_cancel(self):
        self.cancelled = True
        try:
            self.status_label.config(text="جارٍ الإلغاء...")
            self.cancel_btn.config(state="disabled")
        except Exception:
            pass

    def close(self):
        if self.finished:
            return
        self.finished = True
        try:
            self.win.destroy()
        except Exception:
            pass


# ============================================================
# StartupDialog
# ============================================================
class StartupDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🚀 بدء مشروع جديد")
        self.configure(bg="white")
        self.resizable(False, False)
        self.result = None

        w, h = 620, 580
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        header = tk.Frame(self, bg="#1e3a5f", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Croqui Pro Surveyor v9.3",
                 font=("Segoe UI", 18, "bold"),
                 bg="#1e3a5f", fg="white").pack(pady=10)
        tk.Label(header, text="ابدأ مشروعك باختيار طريقة إدخال الأركان",
                 font=("Segoe UI", 10),
                 bg="#1e3a5f", fg="#b8c5d6").pack()

        body = tk.Frame(self, bg="white", padx=30, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="اختر طريقة البدء:",
                 font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#333").pack(anchor="w", pady=(0, 15))

        card1 = tk.Frame(body, bg="#f0f4f8", relief="flat",
                          highlightbackground="#d6dde5", highlightthickness=2)
        card1.pack(fill="x", pady=5)
        inner1 = tk.Frame(card1, bg="#f0f4f8", padx=20, pady=15)
        inner1.pack(fill="x")
        tk.Label(inner1, text="📥 استيراد من ملف",
                 font=("Segoe UI", 13, "bold"),
                 bg="#f0f4f8", fg="#1e3a5f").pack(anchor="w")
        tk.Label(inner1,
                 text="استورد الإحداثيات من ملف CSV أو TXT",
                 font=("Segoe UI", 9), bg="#f0f4f8", fg="#555",
                 justify="right").pack(anchor="w", pady=(3, 8))
        tk.Button(inner1, text="📂 اختر ملف CSV",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1e88e5", fg="white",
                  activebackground="#1565c0", activeforeground="white",
                  relief="flat", padx=20, pady=6, cursor="hand2",
                  command=self._pick_csv).pack(anchor="w")

        sep = tk.Frame(body, bg="white", pady=10)
        sep.pack(fill="x")
        tk.Label(sep, text="— أو —", font=("Segoe UI", 10),
                 bg="white", fg="#999").pack()

        card2 = tk.Frame(body, bg="#fff8e1", relief="flat",
                          highlightbackground="#f6d860", highlightthickness=2)
        card2.pack(fill="x", pady=5)
        inner2 = tk.Frame(card2, bg="#fff8e1", padx=20, pady=15)
        inner2.pack(fill="x")
        tk.Label(inner2, text="✏️ إدخال يدوي",
                 font=("Segoe UI", 13, "bold"),
                 bg="#fff8e1", fg="#8a6d00").pack(anchor="w")
        tk.Label(inner2,
                 text="ابدأ بإحداثيات افتراضية وحدد الأركان بالسحب",
                 font=("Segoe UI", 9), bg="#fff8e1", fg="#555",
                 justify="right").pack(anchor="w", pady=(3, 8))
        tk.Button(inner2, text="✏️ بدء بالإحداثيات الافتراضية",
                  font=("Segoe UI", 10, "bold"),
                  bg="#f6a623", fg="white",
                  activebackground="#d4900e", activeforeground="white",
                  relief="flat", padx=20, pady=6, cursor="hand2",
                  command=self._pick_manual).pack(anchor="w")

        cache_size = get_cache_size()
        tk.Label(body,
                 text=f"💾 الكاش: {CACHE_DIR} ({cache_size:.2f} MB)",
                 font=("Segoe UI", 8),
                 bg="white", fg="#888", wraplength=540,
                 justify="right").pack(pady=(10, 3))

        cancel = tk.Button(body, text="❌ إلغاء",
                            font=("Segoe UI", 10),
                            bg="#e0e0e0", fg="#555",
                            activebackground="#c0c0c0",
                            relief="flat", padx=30, pady=8,
                            cursor="hand2",
                            command=self._on_cancel)
        cancel.pack(pady=(5, 0))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.after(50, self._bring_to_front)

    def _bring_to_front(self):
        try:
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _pick_csv(self):
        path = filedialog.askopenfilename(
            parent=self, title="اختر ملف CSV",
            filetypes=[("CSV/Text", "*.csv *.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            corners = read_corners_from_csv(path)
            self.result = {"mode": "csv", "corners": corners}
            self.destroy()
        except Exception as exc:
            messagebox.showerror("فشل الاستيراد", str(exc), parent=self)

    def _pick_manual(self):
        defaults = [
            (12.5929379, 53.83599347),
            (12.5929379, 53.83323253),
            (12.59022609, 53.83323255),
            (12.59022609, 53.83593335),
        ]
        self.result = {"mode": "manual", "corners": defaults}
        self.destroy()

    def _on_cancel(self):
        self.result = {"mode": "cancel", "corners": None}
        self.destroy()


# ============================================================
# DraggableMarker
# ============================================================
class DraggableMarker:
    def __init__(self, index, lat, lon, color, name_ar, name_en,
                 ax, editor):
        self.index = index
        self.lat = lat
        self.lon = lon
        self.color = color
        self.name_ar = name_ar
        self.name_en = name_en
        self.ax = ax
        self.editor = editor

        x, y = lonlat_to_webmercator(lon, lat)

        self.marker, = ax.plot(
            x, y, marker="o", markersize=22,
            markerfacecolor=color, markeredgecolor="white",
            markeredgewidth=2.5, zorder=30, picker=True, pickradius=15)

        label_text = f"{index + 1}\n{name_en}"
        self.label = ax.text(
            x, y, label_text, ha="center", va="center",
            fontsize=9, fontweight="bold", color="white",
            zorder=31, picker=False)

        self.ring, = ax.plot(
            x, y, marker="o", markersize=30,
            markerfacecolor="none", markeredgecolor=color,
            markeredgewidth=2, alpha=0.4, zorder=29, linestyle="none")

    def set_position(self, lat, lon):
        self.lat = lat
        self.lon = lon
        x, y = lonlat_to_webmercator(lon, lat)
        self.marker.set_data([x], [y])
        self.label.set_position((x, y))
        self.ring.set_data([x], [y])

    def set_highlight(self, on):
        try:
            if on:
                self.marker.set_markersize(28)
                self.ring.set_alpha(0.9)
                self.ring.set_markersize(38)
            else:
                self.marker.set_markersize(22)
                self.ring.set_alpha(0.4)
                self.ring.set_markersize(30)
        except Exception:
            pass


# ============================================================
# InteractiveMapEditor - v9.3 (كل ضلع مستقل + سحب البحر/الطريق)
# ============================================================
class InteractiveMapEditor(tk.Toplevel):
    def __init__(self, parent, initial_corners, designer_ref, on_confirm_cb,
                 initial_road=(False, "bottom", 0.12),
                 initial_sea=(False, "top", 0.12)):
        super().__init__(parent)
        self.title("📍 محرر الأركان التفاعلي — Croqui Pro v9.3")
        self.configure(bg="white")
        self.transient(parent)

        self.designer_ref = designer_ref
        self.on_confirm_cb = on_confirm_cb

        self.corners = [list(c) for c in initial_corners]
        self.markers = []
        self.active_marker = None
        self.last_update_time = 0
        self.update_throttle_ms = 100

        self.map_type = "satellite"
        self.zoom = 17
        self.basemap_img = None
        self.basemap_bounds = None
        self.sat_img = None
        self.sat_bounds = None

        # ✅ حالات الشارع والبحر مع الإزاحة
        self.has_road = tk.BooleanVar(value=initial_road[0])
        self.road_edge = tk.StringVar(value=initial_road[1])
        self.road_offset = initial_road[2] if len(initial_road) > 2 else 0.12

        self.has_sea = tk.BooleanVar(value=initial_sea[0])
        self.sea_edge = tk.StringVar(value=initial_sea[1])
        self.sea_offset = initial_sea[2] if len(initial_sea) > 2 else 0.12

        # ✅ متغيرات السحب
        self._dragging_feature = None  # "road" أو "sea" أو None
        self._drag_start_offset = 0
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._sea_poly_data = None
        self._road_poly_data = None

        self._updating_entries = False

        w = int(self.winfo_screenwidth() * 0.92)
        h = int(self.winfo_screenheight() * 0.92)
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1100, 700)

        self._build_ui()

        self.after(200, self._load_map_async)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        top = tk.Frame(self, bg="#1e3a5f", height=60)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="📍 محرر الأركان التفاعلي v9.3",
                 font=("Segoe UI", 14, "bold"),
                 bg="#1e3a5f", fg="white").pack(side="left", padx=20)

        btn_frame = tk.Frame(top, bg="#1e3a5f")
        btn_frame.pack(side="right", padx=15)

        self.map_toggle_btn = tk.Button(
            btn_frame, text="🗺️ تبديل للخريطة العادية",
            font=("Segoe UI", 9, "bold"),
            bg="#4a90d9", fg="white",
            activebackground="#2c5f9a", activeforeground="white",
            relief="flat", padx=12, pady=6, cursor="hand2",
            command=self._toggle_map_type)
        self.map_toggle_btn.pack(side="left", padx=3)

        tk.Button(btn_frame, text="🔄 إعادة تعيين",
                  font=("Segoe UI", 9, "bold"),
                  bg="#757575", fg="white",
                  activebackground="#424242", activeforeground="white",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._reset_corners).pack(side="left", padx=3)

        tk.Button(btn_frame, text="❌ إلغاء",
                  font=("Segoe UI", 9, "bold"),
                  bg="#e53935", fg="white",
                  activebackground="#c62828", activeforeground="white",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._on_cancel).pack(side="left", padx=3)

        tk.Button(btn_frame, text="✅ تأكيد الأركان",
                  font=("Segoe UI", 10, "bold"),
                  bg="#2d6a4f", fg="white",
                  activebackground="#1b4332", activeforeground="white",
                  relief="flat", padx=20, pady=6, cursor="hand2",
                  command=self._on_confirm).pack(side="left", padx=3)

        main = tk.Frame(self, bg="white")
        main.pack(fill="both", expand=True)

        self.map_frame = tk.Frame(main, bg="#f0f0f0")
        self.map_frame.pack(side="left", fill="both", expand=True)

        self.side_frame = tk.Frame(main, bg="#f8f9fa", width=390)
        self.side_frame.pack(side="right", fill="y")
        self.side_frame.pack_propagate(False)

        self._build_side_panel()

        self.fig = plt.Figure(figsize=(10, 8), dpi=80)
        self.fig.patch.set_facecolor("white")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xticks([]); self.ax.set_yticks([])

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.map_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)

        info = tk.Label(self.map_frame,
                         text="💡 اسحب الأركان | اسحب البحر أو الطريق لتحريكه | Scroll للزوم",
                         font=("Segoe UI", 9),
                         bg="#fff8e1", fg="#8a6d00", pady=6)
        info.pack(fill="x", side="bottom")

    def _build_side_panel(self):
        canvas = tk.Canvas(self.side_frame, bg="#f8f9fa",
                           highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.side_frame, orient="vertical",
                                   command=canvas.yview)
        inner = tk.Frame(canvas, bg="#f8f9fa")

        inner.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        title_frame = tk.Frame(inner, bg="#1e3a5f")
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="📊 معلومات لحظية",
                 font=("Segoe UI", 12, "bold"),
                 bg="#1e3a5f", fg="white", pady=12).pack()

        area_frame = tk.Frame(inner, bg="white",
                                highlightbackground="#e0e0e0",
                                highlightthickness=1)
        area_frame.pack(fill="x", padx=12, pady=(12, 8))

        tk.Label(area_frame, text="⚡ المساحة الفعلية",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#555").pack(pady=(10, 3))

        self.area_label = tk.Label(area_frame, text="0.00 م²",
                                     font=("Segoe UI", 22, "bold"),
                                     bg="white", fg="#e31e24")
        self.area_label.pack(pady=(0, 10))

        lengths_frame = tk.Frame(inner, bg="white",
                                   highlightbackground="#e0e0e0",
                                   highlightthickness=1)
        lengths_frame.pack(fill="x", padx=12, pady=8)

        tk.Label(lengths_frame, text="📏 أطوال الأضلاع (مستقلة)",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#555").pack(pady=(10, 5), anchor="w", padx=12)

        tk.Label(lengths_frame,
                 text="كل ضلع يتحكم بنقطة واحدة فقط — لا تعارض",
                 font=("Segoe UI", 8), bg="white", fg="#888",
                 justify="right").pack(anchor="w", padx=12, pady=(0, 5))

        self.length_entries = {}
        edges = [
            ("top", EDGE_LABELS_AR["top"], "#e31e24"),
            ("right", EDGE_LABELS_AR["right"], "#0066cc"),
            ("bottom", EDGE_LABELS_AR["bottom"], "#f6a623"),
            ("left", EDGE_LABELS_AR["left"], "#2d6a4f"),
        ]
        for key, label, color in edges:
            row = tk.Frame(lengths_frame, bg="white")
            row.pack(fill="x", padx=12, pady=4)

            color_bar = tk.Frame(row, bg=color, width=5, height=22)
            color_bar.pack(side="right", padx=(0, 6))
            color_bar.pack_propagate(False)

            tk.Label(row, text=label,
                     font=("Segoe UI", 9, "bold"),
                     bg="white", fg=color, width=14,
                     anchor="e").pack(side="right")

            var = tk.StringVar(value="0.00")
            entry = tk.Entry(row, textvariable=var, width=10,
                              font=("Consolas", 10, "bold"),
                              relief="solid", bd=1,
                              bg="#f8f9fa", fg=color,
                              justify="center")
            entry.pack(side="left", padx=3)
            tk.Label(row, text="م", font=("Segoe UI", 10),
                     bg="white", fg="#666").pack(side="left")

            var.trace_add("write",
                          lambda *a, k=key, v=var: self._on_length_change(k, v))

            self.length_entries[key] = (var, entry, color)

        tk.Frame(lengths_frame, bg="white", height=8).pack()

        # ===== الطريق العام =====
        road_frame = tk.Frame(inner, bg="#fff8e1",
                                highlightbackground="#f6d860",
                                highlightthickness=2)
        road_frame.pack(fill="x", padx=12, pady=8)

        tk.Checkbutton(road_frame, text="🛣️ يوجد طريق عام",
                       variable=self.has_road,
                       font=("Segoe UI", 10, "bold"),
                       bg="#fff8e1", fg="#8a6d00",
                       activebackground="#fff8e1",
                       selectcolor="#fff8e1",
                       command=self._redraw_map_only
                       ).pack(anchor="w", padx=10, pady=(8, 3))

        row = tk.Frame(road_frame, bg="#fff8e1")
        row.pack(fill="x", padx=10, pady=(0, 3))
        tk.Label(row, text="على الضلع:",
                 font=("Segoe UI", 9),
                 bg="#fff8e1", fg="#555").pack(side="right", padx=3)

        for edge_key in ["top", "right", "bottom", "left"]:
            tk.Radiobutton(row, text=EDGE_NAMES_AR[edge_key],
                            variable=self.road_edge, value=edge_key,
                            font=("Segoe UI", 9),
                            bg="#fff8e1", fg="#333",
                            activebackground="#fff8e1",
                            selectcolor="#fff8e1",
                            command=self._redraw_map_only
                            ).pack(side="right", padx=3)

        tk.Label(road_frame,
                 text="💡 يمكنك سحب الطريق على الخريطة لتغيير بعده",
                 font=("Segoe UI", 8), bg="#fff8e1", fg="#8a6d00",
                 justify="right").pack(anchor="w", padx=10, pady=(0, 8))

        # ===== البحر =====
        sea_frame = tk.Frame(inner, bg="#e3f2fd",
                                highlightbackground="#4a90d9",
                                highlightthickness=2)
        sea_frame.pack(fill="x", padx=12, pady=8)

        tk.Checkbutton(sea_frame, text="🌊 يوجد بحر",
                       variable=self.has_sea,
                       font=("Segoe UI", 10, "bold"),
                       bg="#e3f2fd", fg="#1e3a5f",
                       activebackground="#e3f2fd",
                       selectcolor="#e3f2fd",
                       command=self._redraw_map_only
                       ).pack(anchor="w", padx=10, pady=(8, 3))

        row = tk.Frame(sea_frame, bg="#e3f2fd")
        row.pack(fill="x", padx=10, pady=(0, 3))
        tk.Label(row, text="على الضلع:",
                 font=("Segoe UI", 9),
                 bg="#e3f2fd", fg="#555").pack(side="right", padx=3)

        for edge_key in ["top", "right", "bottom", "left"]:
            tk.Radiobutton(row, text=EDGE_NAMES_AR[edge_key],
                            variable=self.sea_edge, value=edge_key,
                            font=("Segoe UI", 9),
                            bg="#e3f2fd", fg="#333",
                            activebackground="#e3f2fd",
                            selectcolor="#e3f2fd",
                            command=self._redraw_map_only
                            ).pack(side="right", padx=3)

        tk.Label(sea_frame,
                 text="💡 يمكنك سحب البحر على الخريطة لتغيير بعده",
                 font=("Segoe UI", 8), bg="#e3f2fd", fg="#1e3a5f",
                 justify="right").pack(anchor="w", padx=10, pady=(0, 8))

        # ===== إحداثيات الأركان =====
        coords_frame = tk.Frame(inner, bg="white",
                                  highlightbackground="#e0e0e0",
                                  highlightthickness=1)
        coords_frame.pack(fill="x", padx=12, pady=8)

        tk.Label(coords_frame, text="📍 إحداثيات الأركان (WGS84)",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#555").pack(pady=(10, 5), anchor="w", padx=12)

        self.coord_entries = []
        for i in range(4):
            row = tk.Frame(coords_frame, bg="white")
            row.pack(fill="x", padx=12, pady=3)

            color_bar = tk.Frame(row, bg=PIN_COLORS[i], width=6, height=28)
            color_bar.pack(side="right", padx=(0, 6))
            color_bar.pack_propagate(False)

            tk.Label(row, text=f"{i+1}-{PIN_NAMES_EN[i]}",
                     font=("Segoe UI", 9, "bold"),
                     bg="white", fg=PIN_COLORS[i],
                     width=8, anchor="e").pack(side="right")

            lat_var = tk.StringVar(value=f"{self.corners[i][0]:.8f}")
            lon_var = tk.StringVar(value=f"{self.corners[i][1]:.8f}")

            lat_e = tk.Entry(row, textvariable=lat_var, width=13,
                              font=("Consolas", 8), relief="solid",
                              bd=1, bg="#f8f9fa")
            lat_e.pack(side="left", padx=2)
            tk.Label(row, text="Lat", font=("Segoe UI", 7),
                     bg="white", fg="#888").pack(side="left")

            lon_e = tk.Entry(row, textvariable=lon_var, width=13,
                              font=("Consolas", 8), relief="solid",
                              bd=1, bg="#f8f9fa")
            lon_e.pack(side="left", padx=2)
            tk.Label(row, text="Lon", font=("Segoe UI", 7),
                     bg="white", fg="#888").pack(side="left")

            lat_var.trace_add("write",
                              lambda *a, idx=i: self._on_manual_coord_change(idx))
            lon_var.trace_add("write",
                              lambda *a, idx=i: self._on_manual_coord_change(idx))

            self.coord_entries.append((lat_var, lon_var))

        tk.Frame(coords_frame, bg="white", height=10).pack()

    def _load_map_async(self):
        pw = ProgressWindow(self, "🗺️ تحميل الخريطة", modal=False)

        clat = sum(c[0] for c in self.corners) / 4
        clon = sum(c[1] for c in self.corners) / 4
        _, _, radius = compute_site_center_and_radius(self.corners, margin=2.2)

        q = queue.Queue()
        cancel = threading.Event()

        def worker():
            try:
                q.put((10, "تحميل OpenStreetMap..."))

                def p_osm(d, t, m):
                    pct = 10 + int(45 * d / max(1, t))
                    q.put((pct, f"OSM: {m}"))

                img, x0, y0, x1, y1 = fetch_osm(
                    clon, clat, radius, size_px=1600,
                    zoom=self.zoom, progress_cb=p_osm,
                    cancel_event=cancel)
                if cancel.is_set():
                    q.put(("cancelled", ""))
                    return
                if img:
                    self.basemap_img = img
                    self.basemap_bounds = (x0, y0, x1, y1)

                q.put((60, "تحميل الصورة الجوية..."))

                def p_sat(d, t, m):
                    pct = 60 + int(35 * d / max(1, t))
                    q.put((pct, f"قمر صناعي: {m}"))

                img2, x0b, y0b, x1b, y1b = fetch_satellite(
                    clon, clat, radius, size_px=1600,
                    zoom=self.zoom, progress_cb=p_sat,
                    cancel_event=cancel)
                if cancel.is_set():
                    q.put(("cancelled", ""))
                    return
                if img2:
                    self.sat_img = img2
                    self.sat_bounds = (x0b, y0b, x1b, y1b)

                q.put(("done", ""))

            except Exception as e:
                q.put(("error", str(e)))
                traceback.print_exc()

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                while True:
                    it = q.get_nowait()
                    if it[0] == "done":
                        pw.update(100, "اكتمل!")
                        self.after(150, lambda: self._finish_load(pw, True))
                        return
                    elif it[0] == "cancelled":
                        self.after(150, lambda: self._finish_load(pw, False))
                        return
                    elif it[0] == "error":
                        self.after(150,
                                    lambda msg=it[1]: self._finish_load(pw, False, msg))
                        return
                    else:
                        pw.update(it[0], it[1])
            except queue.Empty:
                pass
            if not pw.finished:
                self.after(80, poll)

        self.after(80, poll)

    def _finish_load(self, pw, success, msg=""):
        if pw.cancelled:
            pw.close()
            self._on_cancel()
            return
        pw.close()
        if not success and msg:
            messagebox.showerror("خطأ في التحميل", msg, parent=self)
        self._draw_map()
        self._refresh_measurements()
        self._create_markers()

    def _redraw_map_only(self):
        self._draw_map()
        self._create_markers()

    def _draw_map(self):
        self.ax.clear()
        self.ax.set_xticks([]); self.ax.set_yticks([])

        if self.map_type == "osm":
            img = self.basemap_img
            bounds = self.basemap_bounds
        else:
            img = self.sat_img
            bounds = self.sat_bounds

        if img is None or bounds is None:
            self.ax.set_facecolor("#f0f0f0")
            self.ax.text(0.5, 0.5, "لا توجد خريطة",
                          ha="center", va="center",
                          transform=self.ax.transAxes,
                          fontproperties=get_arabic_font(14),
                          color="#888")
        else:
            x0, y0, x1, y1 = bounds
            self.ax.imshow(img, extent=[x0, x1, y0, y1],
                            aspect="equal", interpolation="bilinear",
                            zorder=0)
            self.ax.set_xlim(x0, x1)
            self.ax.set_ylim(y0, y1)

        self._draw_polygon()
        self._draw_axes_lines()
        self._draw_road_sea()
        self.canvas.draw_idle()

    def _draw_polygon(self):
        if hasattr(self, "_polygon_line") and self._polygon_line:
            try:
                self._polygon_line.remove()
            except Exception:
                pass

        pts = []
        for lat, lon in self.corners:
            x, y = lonlat_to_webmercator(lon, lat)
            pts.append((x, y))
        pts.append(pts[0])

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        self._polygon_line, = self.ax.plot(
            xs, ys, color="#e31e24", lw=2.8, zorder=20,
            solid_capstyle="round")

    def _draw_axes_lines(self):
        if hasattr(self, "_axis_lines"):
            for ln in self._axis_lines:
                try:
                    ln.remove()
                except Exception:
                    pass
        self._axis_lines = []

        xs = [lonlat_to_webmercator(lon, lat)[0] for lat, lon in self.corners]
        ys = [lonlat_to_webmercator(lon, lat)[1] for lat, lon in self.corners]
        cx = sum(xs) / 4
        cy = sum(ys) / 4

        l1, = self.ax.plot([cx, cx], [min(ys), max(ys)],
                            color="white", lw=1.5,
                            ls=(0, (6, 4)), zorder=15, alpha=0.9)
        l2, = self.ax.plot([min(xs), max(xs)], [cy, cy],
                            color="white", lw=1.5,
                            ls=(0, (6, 4)), zorder=15, alpha=0.9)
        self._axis_lines = [l1, l2]

    def _draw_road_sea(self):
        if hasattr(self, "_road_sea_artists"):
            for art in self._road_sea_artists:
                try:
                    art.remove()
                except Exception:
                    pass
        self._road_sea_artists = []

        corner_merc = []
        for lat, lon in self.corners:
            corner_merc.append(lonlat_to_webmercator(lon, lat))

        # ✅ مسح بيانات السحب القديمة
        self._sea_poly_data = None
        self._road_poly_data = None

        if self.has_road.get():
            self._draw_feature(corner_merc, self.road_edge.get(),
                                "🛣️ الطريق العام", "#4a4a4a", is_sea=False,
                                offset_factor=self.road_offset)

        if self.has_sea.get():
            self._draw_feature(corner_merc, self.sea_edge.get(),
                                "🌊 البحر", "#1a4d6e", is_sea=True,
                                offset_factor=self.sea_offset)

    def _draw_feature(self, corner_merc, edge, label, color, is_sea=True,
                       offset_factor=0.12):
        idx_map = {
            "top": (0, 1),
            "right": (0, 3),
            "bottom": (3, 2),
            "left": (1, 2),
        }
        i1, i2 = idx_map[edge]
        p1 = corner_merc[i1]
        p2 = corner_merc[i2]

        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1:
            return

        nx = -dy / L
        ny = dx / L

        cx = sum(p[0] for p in corner_merc) / 4
        cy = sum(p[1] for p in corner_merc) / 4
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        vx = mx - cx
        vy = my - cy
        if nx * vx + ny * vy < 0:
            nx, ny = -nx, -ny

        width = L * offset_factor

        a1 = (p1[0] + nx * width, p1[1] + ny * width)
        a2 = (p2[0] + nx * width, p2[1] + ny * width)

        if is_sea:
            poly = plt.Polygon([p1, p2, a2, a1], closed=True,
                                facecolor=color, edgecolor="white",
                                linewidth=1.5, alpha=0.8, zorder=7)
        else:
            poly = plt.Polygon([p1, p2, a2, a1], closed=True,
                                facecolor=color, edgecolor="none",
                                alpha=0.85, zorder=7)

        self.ax.add_patch(poly)
        self._road_sea_artists.append(poly)

        # ✅ احفظ بيانات السحب
        if is_sea:
            self._sea_poly_data = (p1, p2, a1, a2, nx, ny, L, edge, corner_merc)
        else:
            self._road_poly_data = (p1, p2, a1, a2, nx, ny, L, edge, corner_merc)

        if not is_sea:
            mid1 = ((p1[0] + a1[0]) / 2, (p1[1] + a1[1]) / 2)
            mid2 = ((p2[0] + a2[0]) / 2, (p2[1] + a2[1]) / 2)
            line, = self.ax.plot([mid1[0], mid2[0]], [mid1[1], mid2[1]],
                                  color="white", lw=1.5,
                                  ls=(0, (12, 10)), zorder=8)
            self._road_sea_artists.append(line)

        mx_label = (p1[0] + p2[0] + a1[0] + a2[0]) / 4
        my_label = (p1[1] + p2[1] + a1[1] + a2[1]) / 4
        angle = math.degrees(math.atan2(dy, dx))
        if angle > 90 or angle < -90:
            angle += 180

        txt = self.ax.text(mx_label, my_label, label,
                            ha="center", va="center",
                            fontproperties=get_arabic_font(11),
                            fontweight="bold",
                            color="white", rotation=angle,
                            bbox=dict(boxstyle="round,pad=0.3",
                                      facecolor="#2c3e50",
                                      edgecolor="white", linewidth=1),
                            zorder=9)
        self._road_sea_artists.append(txt)

    def _create_markers(self):
        for m in self.markers:
            for obj in [m.marker, m.label, m.ring]:
                try:
                    obj.remove()
                except Exception:
                    pass
        self.markers = []

        for i, (lat, lon) in enumerate(self.corners):
            m = DraggableMarker(
                index=i, lat=lat, lon=lon,
                color=PIN_COLORS[i],
                name_ar=PIN_NAMES_AR[i],
                name_en=PIN_NAMES_EN[i],
                ax=self.ax, editor=self)
            self.markers.append(m)

        self.canvas.draw_idle()

    # ==================================================
    # ✅ on_press: نتحقق أولاً من البحر/الطريق للسحب
    # ==================================================
    def _on_press(self, event):
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        # ✅ أولاً: هل النقرة على البحر أو الطريق؟ (للسحب)
        from matplotlib.path import Path as MplPath
        for feature_name in ["sea", "road"]:
            poly_data = getattr(self, f"_{feature_name}_poly_data", None)
            if poly_data is None:
                continue
            enabled = (self.has_sea.get() if feature_name == "sea"
                        else self.has_road.get())
            if not enabled:
                continue
            p1, p2, a1, a2, nx, ny, L, edge, corner_merc = poly_data
            poly_path = MplPath([p1, p2, a2, a1])
            if poly_path.contains_point((event.xdata, event.ydata)):
                self._dragging_feature = feature_name
                self._drag_start_x = event.xdata
                self._drag_start_y = event.ydata
                if feature_name == "sea":
                    self._drag_start_offset = self.sea_offset
                else:
                    self._drag_start_offset = self.road_offset
                try:
                    self.canvas.get_tk_widget().config(cursor="sb_h_double_arrow")
                except Exception:
                    pass
                return

        # ✅ وإلا: جرّب تحريك الأركان
        closest = None
        min_dist = float("inf")
        for m in self.markers:
            x, y = lonlat_to_webmercator(m.lon, m.lat)
            d = math.hypot(event.xdata - x, event.ydata - y)
            bbox = self.ax.get_window_extent()
            xr = self.ax.get_xlim()[1] - self.ax.get_xlim()[0]
            px_per_data = bbox.width / xr
            d_px = d * px_per_data
            if d_px < 25 and d_px < min_dist:
                min_dist = d_px
                closest = m

        if closest:
            self.active_marker = closest
            closest.set_highlight(True)
            self.canvas.draw_idle()

    # ==================================================
    # ✅ on_motion: سحب البحر/الطريق أو الأركان
    # ==================================================
    def _on_motion(self, event):
        if event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        now = time.time() * 1000
        if now - self.last_update_time < self.update_throttle_ms:
            return
        self.last_update_time = now

        # ✅ سحب البحر/الطريق
        if self._dragging_feature is not None:
            poly_data = getattr(self, f"_{self._dragging_feature}_poly_data", None)
            if poly_data is None:
                return
            p1, p2, a1, a2, nx, ny, L, edge, corner_merc = poly_data

            dx = event.xdata - self._drag_start_x
            dy = event.ydata - self._drag_start_y
            delta_normal = dx * nx + dy * ny

            delta_offset = delta_normal / max(L, 1)
            new_offset = self._drag_start_offset + delta_offset
            new_offset = max(0.02, min(1.0, new_offset))

            if self._dragging_feature == "sea":
                self.sea_offset = new_offset
            else:
                self.road_offset = new_offset

            self._draw_road_sea()
            self.canvas.draw_idle()
            return

        # ✅ سحب الأركان
        if self.active_marker is None:
            return

        lon, lat = webmercator_to_lonlat(event.xdata, event.ydata)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return

        idx = self.active_marker.index
        self.corners[idx] = [lat, lon]
        self.active_marker.set_position(lat, lon)
        self._draw_polygon()
        self._draw_axes_lines()
        self._draw_road_sea()
        self._refresh_measurements()
        self._update_coord_entries()
        self.canvas.draw_idle()

    # ==================================================
    # ✅ on_release: إنهاء السحب
    # ==================================================
    def _on_release(self, event):
        if self._dragging_feature is not None:
            self._dragging_feature = None
            try:
                self.canvas.get_tk_widget().config(cursor="")
            except Exception:
                pass
            return

        if self.active_marker is not None:
            self.active_marker.set_highlight(False)
            self.active_marker = None
            self.canvas.draw_idle()

    def _on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        if event.button == "up":
            new_zoom = min(19, self.zoom + 1)
        elif event.button == "down":
            new_zoom = max(15, self.zoom - 1)
        else:
            return
        if new_zoom == self.zoom:
            return
        self.zoom = new_zoom
        self._reload_map()

    def _reload_map(self):
        clat = sum(c[0] for c in self.corners) / 4
        clon = sum(c[1] for c in self.corners) / 4
        _, _, radius = compute_site_center_and_radius(self.corners, margin=2.2)

        pw = ProgressWindow(self, f"🗺️ تحميل (Zoom {self.zoom})", modal=False)

        q = queue.Queue()
        cancel = threading.Event()

        def worker():
            try:
                q.put((10, "OSM..."))

                def p_osm(d, t, m):
                    pct = 10 + int(45 * d / max(1, t))
                    q.put((pct, f"OSM: {m}"))

                img, x0, y0, x1, y1 = fetch_osm(
                    clon, clat, radius, size_px=1600,
                    zoom=self.zoom, progress_cb=p_osm,
                    cancel_event=cancel)
                if cancel.is_set():
                    q.put(("cancelled", ""))
                    return
                if img:
                    self.basemap_img = img
                    self.basemap_bounds = (x0, y0, x1, y1)

                q.put((55, "قمر صناعي..."))

                def p_sat(d, t, m):
                    pct = 55 + int(40 * d / max(1, t))
                    q.put((pct, f"قمر صناعي: {m}"))

                img2, x0b, y0b, x1b, y1b = fetch_satellite(
                    clon, clat, radius, size_px=1600,
                    zoom=self.zoom, progress_cb=p_sat,
                    cancel_event=cancel)
                if cancel.is_set():
                    q.put(("cancelled", ""))
                    return
                if img2:
                    self.sat_img = img2
                    self.sat_bounds = (x0b, y0b, x1b, y1b)

                q.put(("done", ""))

            except Exception as e:
                q.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                while True:
                    it = q.get_nowait()
                    if it[0] == "done":
                        pw.update(100, "اكتمل")
                        self.after(150, lambda: self._finish_reload(pw))
                        return
                    elif it[0] == "cancelled":
                        self.after(150, pw.close)
                        return
                    elif it[0] == "error":
                        self.after(150, pw.close)
                        return
                    else:
                        pw.update(it[0], it[1])
            except queue.Empty:
                pass
            if not pw.finished:
                self.after(80, poll)

        self.after(80, poll)

    def _finish_reload(self, pw):
        pw.close()
        self._draw_map()
        self._create_markers()
        self._refresh_measurements()

    def _refresh_measurements(self):
        try:
            m = precise_measurements([tuple(c) for c in self.corners])
            self.area_label.config(text=f"{m['area']:,.2f} م²")

            self._updating_entries = True
            for key in ["top", "right", "bottom", "left"]:
                var, entry, color = self.length_entries[key]
                var.set(f"{m[key]:.2f}")
            self._updating_entries = False

        except Exception as e:
            print(f"[Measure] {e}")

    def _update_coord_entries(self):
        self._updating_entries = True
        for i, (lat_var, lon_var) in enumerate(self.coord_entries):
            lat, lon = self.corners[i]
            lat_var.set(f"{lat:.8f}")
            lon_var.set(f"{lon:.8f}")
        self._updating_entries = False

    # ==================================================
    # ✅ _on_length_change: كل ضلع مستقل تماماً
    # ==================================================
    def _on_length_change(self, key, var):
        """كل ضلع يعدل نقطة واحدة فقط — لا تعارض مع أي ضلع آخر"""
        if self._updating_entries:
            return
        try:
            new_length = clean_number(var.get())
            if new_length <= 0 or new_length > 100000:
                return
        except Exception:
            return

        # ✅ خريطة الأضلاع المستقلة:
        #   top    (P1↔P2): P1 ثابت → P2 يتحرك  (idx=1)
        #   right  (P1↔P4): P1 ثابت → P4 يتحرك  (idx=3)
        #   bottom (P3↔P4): P3 ثابت → P4 يتحرك  (idx=3)  ← لكن يتقاسم مع right
        #   left   (P2↔P3): P2 ثابت → P3 يتحرك  (idx=2)
        #
        # ✅ لتفادي التعارض بين bottom و right:
        #   bottom يستخدم anchor = P4, mover = P3
        #   right  يستخدم anchor = P1, mover = P4
        #   → كل واحد يحرك نقطة مختلفة (P3 و P4 على التوالي)
        edge_map = {
            "top":    {"anchor": 0, "mover": 1},  # P1 → P2
            "right":  {"anchor": 0, "mover": 3},  # P1 → P4
            "bottom": {"anchor": 3, "mover": 2},  # P4 → P3
            "left":   {"anchor": 1, "mover": 2},  # P2 → P3
        }
        edge = edge_map[key]
        anchor_idx = edge["anchor"]
        mover_idx = edge["mover"]

        anchor = tuple(self.corners[anchor_idx])
        mover = tuple(self.corners[mover_idx])

        new_pos = move_point_along_line(anchor, mover, new_length)
        self.corners[mover_idx] = [new_pos[0], new_pos[1]]

        if mover_idx < len(self.markers):
            self.markers[mover_idx].set_position(new_pos[0], new_pos[1])

        self._draw_polygon()
        self._draw_axes_lines()
        self._draw_road_sea()
        self._refresh_measurements()
        self._update_coord_entries()
        self.canvas.draw_idle()

    def _on_manual_coord_change(self, idx):
        if self._updating_entries:
            return
        try:
            lat = clean_number(self.coord_entries[idx][0].get())
            lon = clean_number(self.coord_entries[idx][1].get())
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return
            self.corners[idx] = [lat, lon]
            if idx < len(self.markers):
                self.markers[idx].set_position(lat, lon)
            self._draw_polygon()
            self._draw_axes_lines()
            self._draw_road_sea()
            self._refresh_measurements()
            self.canvas.draw_idle()
        except Exception:
            pass

    def _toggle_map_type(self):
        self.map_type = "satellite" if self.map_type == "osm" else "osm"
        if self.map_type == "satellite":
            self.map_toggle_btn.config(text="🗺️ تبديل للخريطة العادية")
        else:
            self.map_toggle_btn.config(text="🛰️ تبديل للقمر الصناعي")
        self._draw_map()
        self._create_markers()
        self._refresh_measurements()

    def _reset_corners(self):
        if not messagebox.askyesno(
            "تأكيد",
            "إعادة تعيين جميع الأركان؟",
            parent=self):
            return
        defaults = [
            (12.5929379, 53.83599347),
            (12.5929379, 53.83323253),
            (12.59022609, 53.83323255),
            (12.59022609, 53.83593335),
        ]
        self.corners = [list(c) for c in defaults]
        for i, (lat, lon) in enumerate(defaults):
            if i < len(self.markers):
                self.markers[i].set_position(lat, lon)
        self._draw_polygon()
        self._draw_axes_lines()
        self._draw_road_sea()
        self._refresh_measurements()
        self._update_coord_entries()
        self.canvas.draw_idle()

    def _on_confirm(self):
        try:
            corners = [tuple(c) for c in self.corners]
            road = (self.has_road.get(), self.road_edge.get(), self.road_offset)
            sea = (self.has_sea.get(), self.sea_edge.get(), self.sea_offset)
            self.on_confirm_cb(corners, road, sea)
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ عند التأكيد: {e}", parent=self)
            return
        self.destroy()

    def _on_cancel(self):
        self.destroy()


# ============================================================
# CroquiApp
# ============================================================
class CroquiApp(tk.Tk):
    def __init__(self, initial_corners=None):
        super().__init__()
        self.title("Croqui Pro Surveyor v9.3 — محرر تفاعلي متقدم")
        self.geometry("1500x950")
        self.minsize(1200, 800)

        self.designer = CroquiDesigner()
        self.corner_vars = []
        self.initial_corners = initial_corners or [
            (12.5929379, 53.83599347),
            (12.5929379, 53.83323253),
            (12.59022609, 53.83323255),
            (12.59022609, 53.83593335),
        ]

        self.has_road = False
        self.road_edge = "bottom"
        self.road_offset = 0.12
        self.has_sea = False
        self.sea_edge = "top"
        self.sea_offset = 0.12

        self.pin_lat_var = tk.StringVar(value="—")
        self.pin_lon_var = tk.StringVar(value="—")
        self.pin_radius_var = tk.StringVar(value="—")

        self.project_vars = {
            "type": tk.StringVar(value="أرض مخصصة لمجمع سياحي"),
            "north_facing": tk.StringVar(value=""),
            "south_facing": tk.StringVar(value=""),
            "east_facing": tk.StringVar(value=""),
            "west_facing": tk.StringVar(value=""),
            "engineer": tk.StringVar(value="م. وائل عبدالله"),
            "specialty": tk.StringVar(value="مهندس مدني - مساح"),
            "license": tk.StringVar(value="هيئة المهندسين"),
        }
        self.status_var = tk.StringVar(value="جاهز")

        self.font_var = tk.StringVar()
        self.header_color_var = tk.StringVar(value=TABLE_HEADER_COLOR)
        self.cell_color_var = tk.StringVar(value=TABLE_CELL_COLOR)
        self.logo_path_var = tk.StringVar(value="لم يتم رفع شعار")

        self._build_ui()
        self._load_initial_corners()
        self._auto_compute_pin()

        self.status_var.set(
            "✓ جاهز! اضغط '🔄 تحديث المعاينة' أو '🎯 إعادة تحديد الأركان'"
        )

    def _load_initial_corners(self):
        if not self.initial_corners:
            return
        for i, (lat, lon) in enumerate(self.initial_corners):
            if i < len(self.corner_vars):
                self.corner_vars[i][0].set(f"{lat:.8f}")
                self.corner_vars[i][1].set(f"{lon:.8f}")

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Croqui Pro Surveyor",
                  font=("Segoe UI", 16, "bold")).pack(side="left", padx=5)
        ttk.Label(top, text="v9.3",
                  font=("Segoe UI", 10)).pack(side="left", padx=10)

        ttk.Button(top, text="📐 تصدير DXF",
                   command=self.export_dxf_file).pack(side="right", padx=3)
        ttk.Button(top, text="📄 تصدير PDF",
                   command=lambda: self.export("pdf")).pack(side="right", padx=3)
        ttk.Button(top, text="🖼️ تصدير PNG",
                   command=lambda: self.export("png")).pack(side="right", padx=3)

        tk.Button(top, text="🔄 تحديث المعاينة",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1e88e5", fg="white",
                  activebackground="#1565c0", activeforeground="white",
                  relief="flat", padx=15, pady=6, cursor="hand2",
                  command=self.generate_preview).pack(side="right", padx=3)

        self.reset_btn = tk.Button(top,
                                     text="🎯 إعادة تحديد الأركان",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="#2d6a4f", fg="white",
                                     activebackground="#1b4332",
                                     activeforeground="white",
                                     relief="flat", padx=15, pady=6,
                                     cursor="hand2",
                                     command=self.open_interactive_editor)
        self.reset_btn.pack(side="right", padx=10)

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = ttk.Frame(main, padding=5, width=470)
        right = ttk.Frame(main)
        main.add(left, weight=0)
        main.add(right, weight=1)

        self._build_inputs(left)
        self._build_preview(right)

    def _build_inputs(self, parent):
        canvas = tk.Canvas(parent, width=460, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)

        frame.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        editor_box = ttk.LabelFrame(frame, text="🎯 المحرر التفاعلي",
                                      padding=10)
        editor_box.pack(fill="x", pady=5)

        tk.Label(editor_box,
                 text="اسحب الأركان | اسحب البحر والطريق | كل ضلع مستقل",
                 font=("Segoe UI", 9), fg="#555",
                 bg="#f8f9fa", wraplength=400,
                 justify="right").pack(anchor="w", pady=(0, 8))

        tk.Button(editor_box,
                  text="🗺️ فتح المحرر التفاعلي",
                  font=("Segoe UI", 11, "bold"),
                  bg="#e31e24", fg="white",
                  activebackground="#c62828", activeforeground="white",
                  relief="flat", padx=15, pady=10, cursor="hand2",
                  command=self.open_interactive_editor).pack(fill="x")

        cache_box = ttk.LabelFrame(frame, text="💾 إدارة الكاش", padding=8)
        cache_box.pack(fill="x", pady=5)

        self.cache_label = tk.Label(cache_box,
                                      text=f"حجم الكاش: {get_cache_size():.2f} MB",
                                      font=("Segoe UI", 9),
                                      fg="#555", bg="#f8f9fa",
                                      wraplength=420, justify="right")
        self.cache_label.pack(anchor="w", pady=(0, 5))
        tk.Label(cache_box, text=f"المسار: {CACHE_DIR}",
                 font=("Segoe UI", 7),
                 fg="#999", bg="#f8f9fa", wraplength=420,
                 justify="right").pack(anchor="w", pady=(0, 5))

        tk.Button(cache_box, text="🗑️ حذف الكاش",
                  font=("Segoe UI", 9),
                  bg="#e53935", fg="white",
                  activebackground="#c62828", activeforeground="white",
                  relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._clear_cache).pack(fill="x")
        tk.Button(cache_box, text="🔄 تحديث الحجم",
                  font=("Segoe UI", 9),
                  bg="#757575", fg="white",
                  activebackground="#424242", activeforeground="white",
                  relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._update_cache_label
                  ).pack(fill="x", pady=(3, 0))

        style_box = ttk.LabelFrame(frame, text="🎨 الخط والألوان", padding=8)
        style_box.pack(fill="x", pady=5)

        row = ttk.Frame(style_box)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="الخط:", width=13).pack(side="left")
        self.font_combo = ttk.Combobox(row, textvariable=self.font_var,
                                        state="readonly",
                                        values=list(_arabic_fonts.keys()))
        self.font_combo.pack(side="left", fill="x", expand=True)
        if _arabic_fonts:
            self.font_var.set(list(_arabic_fonts.keys())[0])
        self.font_combo.bind("<<ComboboxSelected>>", self._on_font_change)

        row = ttk.Frame(style_box)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="لون الهيدر:", width=13).pack(side="left")
        self.header_color_btn = tk.Button(row, text="  ",
                                           bg=self.header_color_var.get(),
                                           width=6,
                                           command=self._pick_header_color)
        self.header_color_btn.pack(side="left", padx=3)

        row = ttk.Frame(style_box)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="لون الخلية:", width=13).pack(side="left")
        self.cell_color_btn = tk.Button(row, text="  ",
                                         bg=self.cell_color_var.get(),
                                         width=6,
                                         command=self._pick_cell_color)
        self.cell_color_btn.pack(side="left", padx=3)

        logo_box = ttk.LabelFrame(frame, text="🖼️ شعار المكتب", padding=8)
        logo_box.pack(fill="x", pady=5)
        ttk.Label(logo_box, textvariable=self.logo_path_var,
                  foreground="#666", wraplength=420).pack(anchor="w", pady=2)
        row = ttk.Frame(logo_box)
        row.pack(fill="x", pady=2)
        ttk.Button(row, text="📤 رفع شعار",
                   command=self.upload_logo).pack(side="left", fill="x",
                                                    expand=True, padx=2)
        ttk.Button(row, text="🗑️ إزالة",
                   command=self.remove_logo).pack(side="left", padx=2)

        csv_box = ttk.LabelFrame(frame, text="📂 استيراد CSV", padding=8)
        csv_box.pack(fill="x", pady=5)
        ttk.Button(csv_box, text="📥 استيراد ملف CSV",
                   command=self.import_csv).pack(fill="x", pady=3)
        ttk.Button(csv_box, text="📤 تصدير الإحداثيات",
                   command=self.export_csv).pack(fill="x", pady=3)

        pin_box = ttk.LabelFrame(frame, text="📍 مركز الخريطة", padding=8)
        pin_box.pack(fill="x", pady=5)
        for label, var in [("Latitude:", self.pin_lat_var),
                            ("Longitude:", self.pin_lon_var),
                            ("نصف القطر (م):", self.pin_radius_var)]:
            row = ttk.Frame(pin_box)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=15).pack(side="left")
            e = ttk.Entry(row, textvariable=var, state="readonly",
                          foreground="#0066cc")
            e.pack(side="left", fill="x", expand=True)

        corners_box = ttk.LabelFrame(frame, text="📐 إحداثيات الزوايا",
                                     padding=8)
        corners_box.pack(fill="x", pady=5)
        for name in ["1 NE", "2 NW", "3 SW", "4 SE"]:
            row = ttk.Frame(corners_box)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=name, width=8).pack(side="left")
            lat_var = tk.StringVar()
            lon_var = tk.StringVar()
            ttk.Label(row, text="Lat:").pack(side="left")
            ttk.Entry(row, textvariable=lat_var, width=13).pack(side="left", padx=2)
            ttk.Label(row, text="Lon:").pack(side="left")
            ttk.Entry(row, textvariable=lon_var, width=13).pack(side="left", padx=2)
            self.corner_vars.append((lat_var, lon_var))
            lat_var.trace_add("write", lambda *a: self._auto_compute_pin())
            lon_var.trace_add("write", lambda *a: self._auto_compute_pin())

        project_box = ttk.LabelFrame(frame, text="📋 بيانات المشروع", padding=8)
        project_box.pack(fill="x", pady=5)
        for key, label in [
            ("type", "نوع المخطط:"),
            ("engineer", "اسم المهندس:"),
            ("specialty", "التخصص:"),
            ("license", "رقم الترخيص:"),
        ]:
            row = ttk.Frame(project_box)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=15).pack(side="left")
            ttk.Entry(row, textvariable=self.project_vars[key]).pack(
                side="left", fill="x", expand=True)

        faces_box = ttk.LabelFrame(frame, text="🧭 الواجهات (اختياري)",
                                     padding=8)
        faces_box.pack(fill="x", pady=5)
        for key, label in [
            ("north_facing", "الواجهة الشمالية:"),
            ("south_facing", "الواجهة الجنوبية:"),
            ("east_facing", "الواجهة الشرقية:"),
            ("west_facing", "الواجهة الغربية:"),
        ]:
            row = ttk.Frame(faces_box)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=15).pack(side="left")
            ttk.Entry(row, textvariable=self.project_vars[key]).pack(
                side="left", fill="x", expand=True)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=10)
        ttk.Button(buttons, text="🔄 تحديث المعاينة",
                   command=self.generate_preview).pack(fill="x", pady=3)
        ttk.Button(buttons, text="💾 حفظ المشروع",
                   command=self.save_project).pack(fill="x", pady=3)
        ttk.Button(buttons, text="📂 فتح المشروع",
                   command=self.load_project).pack(fill="x", pady=3)

        ttk.Label(frame, textvariable=self.status_var,
                  foreground="#0066cc", wraplength=440,
                  justify="right").pack(fill="x", pady=5)

    def _build_preview(self, parent):
        self.fig = plt.Figure(figsize=(11, 8), dpi=80)
        self.fig.patch.set_facecolor("white")
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def _update_cache_label(self):
        self.cache_label.config(text=f"حجم الكاش: {get_cache_size():.2f} MB")

    def _clear_cache(self):
        if not messagebox.askyesno("تأكيد",
                                     f"حذف كل ملفات الكاش في:\n{CACHE_DIR}؟"):
            return
        if clear_cache():
            self._update_cache_label()
            messagebox.showinfo("تم", "تم حذف الكاش")

    def open_interactive_editor(self):
        corners = self._read_corners()
        if not corners:
            messagebox.showerror("خطأ", "الإحداثيات غير صالحة")
            return

        def on_confirm(new_corners, road, sea):
            for i, (lat, lon) in enumerate(new_corners):
                if i < len(self.corner_vars):
                    self.corner_vars[i][0].set(f"{lat:.8f}")
                    self.corner_vars[i][1].set(f"{lon:.8f}")
            self.has_road = road[0]
            self.road_edge = road[1]
            self.road_offset = road[2] if len(road) > 2 else 0.12
            self.has_sea = sea[0]
            self.sea_edge = sea[1]
            self.sea_offset = sea[2] if len(sea) > 2 else 0.12
            self._auto_compute_pin()
            self.status_var.set("✓ تم تحديث الأركان والشارع/البحر")
            self.generate_preview()

        InteractiveMapEditor(
            self, corners, self.designer, on_confirm,
            initial_road=(self.has_road, self.road_edge, self.road_offset),
            initial_sea=(self.has_sea, self.sea_edge, self.sea_offset))

    def _auto_compute_pin(self):
        try:
            corners = []
            for lat_v, lon_v in self.corner_vars:
                lat_s = lat_v.get().strip()
                lon_s = lon_v.get().strip()
                if not lat_s or not lon_s:
                    return
                lat = clean_number(lat_s)
                lon = clean_number(lon_s)
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    return
                corners.append((lat, lon))
            if len(corners) != 4:
                return
            clat, clon, radius = compute_site_center_and_radius(corners, 1.15)
            self.pin_lat_var.set(f"{clat:.8f}")
            self.pin_lon_var.set(f"{clon:.8f}")
            self.pin_radius_var.set(f"{radius:.1f}")
        except Exception:
            pass

    def _on_font_change(self, event=None):
        name = self.font_var.get()
        path = _arabic_fonts.get(name)
        if path and set_current_font(name, path):
            self.status_var.set(f"✓ تم تغيير الخط إلى: {name}")

    def _pick_header_color(self):
        color = colorchooser.askcolor(color=self.header_color_var.get(),
                                       title="اختر لون الهيدر")[1]
        if color:
            self.header_color_var.set(color)
            self.header_color_btn.configure(bg=color)

    def _pick_cell_color(self):
        color = colorchooser.askcolor(color=self.cell_color_var.get(),
                                       title="اختر لون الخلية")[1]
        if color:
            self.cell_color_var.set(color)
            self.cell_color_btn.configure(bg=color)

    def upload_logo(self):
        path = filedialog.askopenfilename(
            title="اختر صورة الشعار",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif"),
                       ("All", "*.*")])
        if not path:
            return
        self.logo_path_var.set(os.path.basename(path))
        self.designer.set_custom_logo(path)
        self.status_var.set(f"✓ تم رفع الشعار")

    def remove_logo(self):
        self.logo_path_var.set("لم يتم رفع شعار")
        self.designer.set_custom_logo(None)

    def _read_corners(self):
        try:
            out = []
            for lat_v, lon_v in self.corner_vars:
                lat = clean_number(lat_v.get())
                lon = clean_number(lon_v.get())
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValueError(f"قيم غير صالحة")
                out.append((lat, lon))
            return out
        except Exception as exc:
            messagebox.showerror("خطأ في الزوايا", str(exc))
            return None

    def import_csv(self):
        path = filedialog.askopenfilename(
            title="اختر ملف CSV",
            filetypes=[("CSV/Text", "*.csv *.txt"), ("All", "*.*")])
        if not path:
            return
        try:
            corners = read_corners_from_csv(path)
            for i, (lat, lon) in enumerate(corners):
                self.corner_vars[i][0].set(f"{lat:.8f}")
                self.corner_vars[i][1].set(f"{lon:.8f}")
            self._auto_compute_pin()
            self.status_var.set(f"✓ تم استيراد 4 زوايا")
            self.generate_preview()
        except Exception as exc:
            messagebox.showerror("فشل الاستيراد", str(exc))

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="corners.csv")
        if not path:
            return
        try:
            corners = self._read_corners()
            if not corners:
                return
            names = ["شمال شرق", "شمال غرب", "جنوب غرب", "جنوب شرق"]
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.writer(f)
                w.writerow(["name", "latitude", "longitude"])
                for i, (lat, lon) in enumerate(corners):
                    w.writerow([names[i], f"{lat:.8f}", f"{lon:.8f}"])
            self.status_var.set(f"✓ تم التصدير: {path}")
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def generate_preview(self):
        corners = self._read_corners()
        if not corners:
            return

        self._auto_compute_pin()
        try:
            pin_lat = clean_number(self.pin_lat_var.get())
            pin_lon = clean_number(self.pin_lon_var.get())
            pin_radius = clean_number(self.pin_radius_var.get())
        except Exception:
            messagebox.showerror("خطأ", "تعذر حساب مركز الخريطة.")
            return

        self._on_font_change()
        self.designer.set_table_colors(self.header_color_var.get(),
                                        self.cell_color_var.get())
        self.designer.set_road_sea(self.has_road, self.road_edge,
                                    self.has_sea, self.sea_edge,
                                    self.road_offset, self.sea_offset)

        faces_auto = {
            "north_facing": "",
            "south_facing": "",
            "east_facing": "",
            "west_facing": "",
        }
        if self.has_road:
            faces_auto[f"{self.road_edge}_facing"] = "الطريق العام (RR01)"
        if self.has_sea:
            faces_auto[f"{self.sea_edge}_facing"] = "البحر"

        for key in faces_auto:
            manual = self.project_vars.get(key)
            if manual and manual.get().strip():
                self.designer.site_info[key] = manual.get().strip()
            else:
                self.designer.site_info[key] = faces_auto[key]

        for k, v in self.project_vars.items():
            if k in self.designer.site_info:
                if hasattr(v, "get"):
                    val = v.get()
                    if val.strip() or k not in ["north_facing", "south_facing",
                                                  "east_facing", "west_facing"]:
                        self.designer.site_info[k] = val
            if k in self.designer.project_info:
                self.designer.project_info[k] = v.get()

        self.designer.set_corners(corners)
        self.designer.set_pin(pin_lat, pin_lon, pin_radius)

        pw = ProgressWindow(self, "⏳ جاري تحديث المعاينة")
        pw.update(0, "بدء العملية...")

        q = queue.Queue()
        cancel_event = threading.Event()

        def worker():
            try:
                q.put((10, "جاري تحميل OpenStreetMap..."))

                def osm_progress(done, total, msg):
                    percent = 10 + int(40 * done / max(1, total))
                    q.put((percent, f"OpenStreetMap: {msg}"))

                ok1 = self.designer.load_basemap(
                    progress_cb=osm_progress,
                    cancel_event=cancel_event)

                if cancel_event.is_set():
                    q.put(("cancelled", "تم الإلغاء"))
                    return

                q.put((55, "جاري تحميل الصورة الجوية..."))

                def sat_progress(done, total, msg):
                    percent = 55 + int(35 * done / max(1, total))
                    q.put((percent, f"صورة جوية: {msg}"))

                ok2 = self.designer.load_satellite(
                    progress_cb=sat_progress,
                    cancel_event=cancel_event)

                if cancel_event.is_set():
                    q.put(("cancelled", "تم الإلغاء"))
                    return

                q.put((92, "جاري رسم المخطط..."))
                q.put(("done", "اكتمل!"))

            except Exception as e:
                q.put(("error", f"خطأ: {e}"))
                traceback.print_exc()

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                while True:
                    item = q.get_nowait()
                    if item[0] == "done":
                        _finish_preview(pw, success=True)
                        return
                    elif item[0] == "cancelled":
                        _finish_preview(pw, success=False, msg="تم الإلغاء")
                        return
                    elif item[0] == "error":
                        _finish_preview(pw, success=False, msg=item[1])
                        return
                    else:
                        percent, msg = item
                        pw.update(percent, msg)
            except queue.Empty:
                pass
            if not pw.finished:
                self.after(80, poll)

        def _finish_preview(pw, success=True, msg=""):
            if pw.cancelled:
                pw.close()
                self.status_var.set("✗ تم إلغاء العملية")
                return
            if not success:
                pw.close()
                if msg:
                    self.status_var.set(f"✗ {msg}")
                return
            try:
                self.fig.clear()
                self.designer.build_figure(self.fig)
                self.canvas.draw()
                m = self.designer.measurements
                self.status_var.set(
                    f"✓ المساحة: {m['area']:,.2f} م²  |  "
                    f"الطول: {max(m['top'], m['bottom']):.2f}  |  "
                    f"العرض: {max(m['left'], m['right']):.2f}")
            except Exception as e:
                self.status_var.set(f"✗ خطأ: {e}")
                traceback.print_exc()
            pw.update(100, "اكتمل!")
            self.after(200, pw.close)

        self.after(80, poll)

    def export(self, fmt):
        corners = self._read_corners()
        if not corners:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()}", f"*.{fmt}")],
            initialfile=f"croqui.{fmt}")
        if not path:
            return
        try:
            self._on_font_change()
            self.designer.set_table_colors(self.header_color_var.get(),
                                            self.cell_color_var.get())
            self.designer.set_road_sea(self.has_road, self.road_edge,
                                        self.has_sea, self.sea_edge,
                                        self.road_offset, self.sea_offset)
            fig = plt.figure(figsize=(16, 10.5), dpi=300)
            self.designer.build_figure(fig, dpi=300)
            if fmt == "pdf":
                with PdfPages(path) as pdf:
                    pdf.savefig(fig, facecolor="white",
                                bbox_inches="tight", pad_inches=0.1)
            else:
                fig.savefig(path, dpi=300, facecolor="white",
                            bbox_inches="tight", pad_inches=0.1)
            plt.close(fig)
            self.status_var.set(f"✓ تم: {path}")
            messagebox.showinfo("نجاح", f"تم:\n{path}")
        except Exception as exc:
            self.status_var.set(f"✗ {exc}")
            messagebox.showerror("خطأ", str(exc))

    def export_dxf_file(self):
        corners = self._read_corners()
        if not corners:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".dxf",
            filetypes=[("DXF (AutoCAD)", "*.dxf")],
            initialfile="croqui.dxf")
        if not path:
            return
        try:
            m = precise_measurements(corners)
            utm, epsg = to_utm(corners)
            export_dxf(path, utm, epsg, m,
                        self.designer.site_info,
                        self.project_vars["engineer"].get())
            self.status_var.set(f"✓ DXF: {path}")
            messagebox.showinfo("نجاح", f"تم:\n{path}")
        except ImportError as e:
            messagebox.showerror("مكتبة ناقصة", f"{e}\n\npip install ezdxf")
        except Exception as exc:
            messagebox.showerror("خطأ", str(exc))

    def save_project(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".croqui.json",
            filetypes=[("Croqui", "*.croqui.json")])
        if not path:
            return
        data = {
            "corners": [(v[0].get(), v[1].get()) for v in self.corner_vars],
            "project": {k: v.get() for k, v in self.project_vars.items()},
            "road": {"has": self.has_road, "edge": self.road_edge,
                     "offset": self.road_offset},
            "sea": {"has": self.has_sea, "edge": self.sea_edge,
                    "offset": self.sea_offset},
            "style": {
                "font": self.font_var.get(),
                "header_color": self.header_color_var.get(),
                "cell_color": self.cell_color_var.get(),
                "logo_path": self.designer.custom_logo_path or "",
            }
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.status_var.set(f"✓ تم الحفظ: {path}")

    def load_project(self):
        path = filedialog.askopenfilename(
            filetypes=[("Croqui", "*.croqui.json")])
        if not path:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for i, (lat, lon) in enumerate(data.get("corners", [])):
            if i < len(self.corner_vars):
                self.corner_vars[i][0].set(lat)
                self.corner_vars[i][1].set(lon)
        for k, v in data.get("project", {}).items():
            if k in self.project_vars:
                self.project_vars[k].set(v)
        road = data.get("road", {})
        sea = data.get("sea", {})
        self.has_road = road.get("has", False)
        self.road_edge = road.get("edge", "bottom")
        self.road_offset = road.get("offset", 0.12)
        self.has_sea = sea.get("has", False)
        self.sea_edge = sea.get("edge", "top")
        self.sea_offset = sea.get("offset", 0.12)

        style = data.get("style", {})
        if style.get("font") and style["font"] in _arabic_fonts:
            self.font_var.set(style["font"])
            self._on_font_change()
        if style.get("header_color"):
            self.header_color_var.set(style["header_color"])
            self.header_color_btn.configure(bg=style["header_color"])
        if style.get("cell_color"):
            self.cell_color_var.set(style["cell_color"])
            self.cell_color_btn.configure(bg=style["cell_color"])
        if style.get("logo_path") and os.path.exists(style["logo_path"]):
            self.logo_path_var.set(os.path.basename(style["logo_path"]))
            self.designer.set_custom_logo(style["logo_path"])
        self._auto_compute_pin()
        self.status_var.set(f"✓ تم التحميل: {path}")
        self.generate_preview()


# ============================================================
# نقطة الدخول
# ============================================================
def main():
    print("=" * 60)
    print("Croqui Pro Surveyor v9.3")
    print(f"مجلد الكاش: {CACHE_DIR}")
    print(f"حجم الكاش الحالي: {get_cache_size():.2f} MB")
    print("=" * 60)

    root = tk.Tk()
    root.withdraw()

    dlg = StartupDialog(root)
    root.wait_window(dlg)

    if dlg.result is None or dlg.result.get("mode") == "cancel":
        try:
            root.destroy()
        except Exception:
            pass
        return

    initial_corners = dlg.result["corners"]
    try:
        root.destroy()
    except Exception:
        pass

    app = CroquiApp(initial_corners=initial_corners)
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n!!! خطأ فادح: {e}")
        traceback.print_exc()
        input("\nاضغط Enter للإغلاق...")