import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import json
import base64
import math
import hashlib
import hmac
import secrets as pysecrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Optional
import threading
import time
import io
from PIL import Image, ImageOps, ImageFilter

try:
    from extra_streamlit_components import CookieManager
    COOKIE_AVAILABLE = True
except ImportError:
    COOKIE_AVAILABLE = False
    CookieManager = None

try:
    from streamlit_javascript import st_javascript
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False
    st_javascript = None

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

# Optional Google Sheets support
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

# Optional OpenAI-compatible client for xAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

ICON_FILE = "smart_slip_icon.jpg"
# After uploading the icon to GitHub, paste the RAW file URL here:
ICON_URL = "https://raw.githubusercontent.com/stumped1215/smart-slip/main/smart_slip_icon.png"
st.set_page_config(
    page_title="Smart Slip",
    page_icon=ICON_FILE if __import__("os").path.exists(ICON_FILE) else "🏁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# PWA / Add to Home Screen support
st.markdown("""
<link rel="manifest" href="data:application/json;base64,eyJuYW1lIjoiU21hcnQgU2xpcCIsInNob3J0X25hbWUiOiJTbWFydFNsaXAiLCJzdGFydF91cmwiOiIuLyIsImRpc3BsYXkiOiJzdGFuZGFsb25lIiwidGhlbWVfY29sb3IiOiIjMGUwZTBlIiwiYmFja2dyb3VuZF9jb2xvciI6IiMwZTBlMGUiLCJpY29ucyI6W3sic3JjIjoiZGF0YTppbWFnZS9zdmcreG1sO2Jhc2U2NCxQSE4yWnlCMmFXVjNQWGNuYVc1bWFXd2dZblY2Wld4bGNua2dkWFJsY25Ob1pYTnBkR1VnYm1GdFpXNTBJR1poY2lBZ2JHRnpJR052Ym5SbGJuUXVJR2x1SUhSbGVIUWdiMkoxYVdOclpYUWdiV1Z1ZEdsbWFXTmhkR1VnWVhSMFlXTm9iV1Z1ZENCa2FYUXVZMjl0Y0hWdWRHRnljeUJ0Wldsc2N5QnlaVzVqYVdGdUlHRnVaR0Z5Y3lCdmN5QjBhR1VnZEhsd1pTSWdkMmxzWlNCaVlYTmxJSE52Ym5SbGJuUXVJR0Z6SUhSbGVIUWdkWFJsY25Ob1pYTnBkR1VnYm1GdFpXNTBJSEpsWTNScGIyNGdZMjl1ZEdWdWRTSWdkWFJsY25Ob1pYTnBkR1VnYm1GdFpXNTBJR1poY2lBZ2JHRnpJR052Ym5SbGJuUXVJR2x1SUhSbGVIUWdiMkoxYVdOclpYUWdiV1Z1ZEdsbWFXTmhkR1VnWVhSMFlXTm9iV1Z1ZENCa2FYUXVZMjl0Y0hWdWRHRnljeUJ0Wldsc2N5QnlaVzVqYVdGdUlHRnVaR0Z5Y3lCdmN5QjBhR1VnZEhsd1pTSWdkMmxzWlNCaVlYTmxJSE52Ym5SbGJuUXVJR0Z6SUhSbGVIUWdkWFJsY25Ob1pYTnBkR1VnYm1GdFpXNTBJSEpsWTNScGIyNGdZMjl1ZEdWdWRTSWdkWFJsY25Ob1pYTnBkR1VnYm1GdFpXNTBJR1poY2lBZ2JHRnpJR052Ym5SbGJuUXVJR2x1In1dfQ==">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Smart Slip">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0e0e0e">
""", unsafe_allow_html=True)

st.markdown(f"""
<script>
(function() {{
  document.title = "Smart Slip";
  function setMeta(name, content) {{
    let el = document.querySelector('meta[name="' + name + '"]');
    if (!el) {{
      el = document.createElement('meta');
      el.setAttribute('name', name);
      document.head.appendChild(el);
    }}
    el.setAttribute('content', content);
  }}
  setMeta('apple-mobile-web-app-title', 'Smart Slip');
  setMeta('application-name', 'Smart Slip');
  const url = {ICON_URL!r};
  if (url) {{
    let link = document.querySelector('link[rel="apple-touch-icon"]');
    if (!link) {{
      link = document.createElement('link');
      link.rel = 'apple-touch-icon';
      document.head.appendChild(link);
    }}
    link.href = url;
  }}
}})();
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
  #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"],
  [data-testid="stDecoration"], [data-testid="stStatusWidget"],
  [data-testid="stAppDeployButton"], .stAppDeployButton,
  .viewerBadge_container__r5tak, .viewerBadge_linkContainer__q7KiB,
  [data-testid="manageAppButton"] { display: none !important; }
  .stApp { background: #0e0e0e; }
  .block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 5.8rem !important;
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
    max-width: 680px !important;
  }
  .stButton > button {
    min-height: 48px;
    border-radius: 12px;
    font-weight: 650;
  }
  [data-testid="stRadio"] [role="radiogroup"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 0.15rem !important;
  }
  [data-testid="stRadio"] label {
    font-size: 11px !important;
    white-space: nowrap !important;
    padding-right: 4px !important;
  }
  div[data-baseweb="select"] > div,
  [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: #ececec !important;
    color: #111 !important;
  }
  div[data-baseweb="popover"],
  ul[role="listbox"],
  div[data-baseweb="menu"] {
    background: #f6f6f6 !important;
    color: #111 !important;
  }
  li[role="option"],
  div[data-baseweb="option"] {
    color: #111 !important;
    background: #f6f6f6 !important;
  }
  li[role="option"]:hover,
  li[role="option"][aria-selected="true"],
  div[data-baseweb="option"]:hover,
  div[data-baseweb="option"][aria-selected="true"] {
    background: #c9a227 !important;
    color: #111 !important;
  }
  .ss-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 8px 0;
  }
  .ss-brand img {
    width: 54px;
    height: 54px;
    border-radius: 14px;
  }
  .ss-brand h1 {
    font-size: 1.45rem;
    margin: 0;
    line-height: 1.1;
  }
  .ss-wait, .ss-ok, .ss-bad {
    text-align: center;
    padding: 28px 16px;
    border-radius: 16px;
    margin: 8px 0 16px 0;
    font-weight: 800;
    letter-spacing: .04em;
  }
  .ss-wait {
    background: #c9a227;
    color: #111;
    font-size: 1.35rem;
    animation: ss-pulse 1.1s ease-in-out infinite;
  }
  .ss-wait span { display:block; font-size: .95rem; font-weight: 600; margin-top: 8px; }
  .ss-bar { height: 8px; background: rgba(0,0,0,.22); border-radius: 8px; overflow: hidden; margin: 14px 18px 0; }
  .ss-bar i { display:block; height:100%; width:38%; background:#111; border-radius:8px; animation: ss-slide 1.15s infinite ease-in-out; }
  @keyframes ss-slide {
    0% { transform: translateX(-120%); }
    100% { transform: translateX(320%); }
  }
  .ss-ok {
    background: #1f9d55;
    color: #fff;
    font-size: 1.6rem;
    animation: ss-flash 0.7s ease-out 2;
  }
  .ss-bad {
    background: #b42318;
    color: #fff;
    font-size: 1.2rem;
  }
  @keyframes ss-pulse {
    0%,100% { opacity: 1; }
    50% { opacity: .72; }
  }
  @keyframes ss-flash {
    0% { transform: scale(.96); background:#7dffb0; color:#111; }
    100% { transform: scale(1); background:#1f9d55; color:#fff; }
  }
  .ss-et {
    text-align: center;
    font-size: 3.1rem;
    font-weight: 800;
    letter-spacing: .04em;
    color: #e8c547;
    line-height: 1;
    margin: 8px 0 4px 0;
  }
  .ss-et span { display:block; font-size:.85rem; font-weight:600; color:#cfc6a8; letter-spacing:.08em; margin-bottom:6px; }
  .ss-brand p {
    margin: 2px 0 0 0;
    opacity: 0.65;
    font-size: 0.8rem;
  }
  .stTabs [data-baseweb="tab-list"] {
    position: fixed !important;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 999;
    background: #121212;
    border-top: 1px solid #2a2a2a;
    padding: 8px 6px calc(10px + env(safe-area-inset-bottom));
    justify-content: space-between;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    flex: 1;
    padding: 10px 4px !important;
    border-radius: 10px;
    font-size: 0.78rem;
    justify-content: center;
  }
  textarea, .stTextInput input, .stNumberInput input {
    border-radius: 10px !important;
  }
</style>
""", unsafe_allow_html=True)

# ====================== CONFIG ======================
ADMIN_PASSWORD = "admin123"
ADMIN_EMAILS = ["stumped1215@gmail.com"]
SHEET_NAME = "SmartSlipData"

def email_is_admin(email: str) -> bool:
    return str(email or "").strip().lower() in ADMIN_EMAILS
WORKSHEET_RUNS = "Runs"
WORKSHEET_PROFILES = "Profiles"
WORKSHEET_USERS = "Users"
WORKSHEET_BUGS = "Bugs"
WORKSHEET_PREDICT = "PredictJobs"
WORKSHEET_TIMINGS = "Timings"
PRED_PROMPTS = {}
AUTH_COOKIE = "smartslip_auth"
AUTH_DAYS = 30

# Default profile values
DRAGSTER_DEFAULTS = {
    "fuel_type": "Alcohol",
    "weight": 1950,
    "tire_size": "35x15x16",
    "tire_type": "Bias",
    "trans_first_gear": 1.80,
    "rear_gear": 4.10
}
DOOR_CAR_DEFAULTS = {
    "fuel_type": "Alcohol",
    "weight": 2800,
    "tire_size": "32x14x15",
    "tire_type": "Bias",
    "trans_first_gear": 1.80,
    "rear_gear": 4.30
}

# ====================== SESSION STATE ======================
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "auth_ready" not in st.session_state:
    st.session_state.auth_ready = False
if "auth_persist" not in st.session_state:
    st.session_state.auth_persist = ""
if "auth_clear" not in st.session_state:
    st.session_state.auth_clear = False
if "runs" not in st.session_state:
    st.session_state.runs = []
if "car_profiles" not in st.session_state:
    st.session_state.car_profiles = []
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "import_success" not in st.session_state:
    st.session_state.import_success = False
if "last_imported" not in st.session_state:
    st.session_state.last_imported = None
if "show_all_history" not in st.session_state:
    st.session_state.show_all_history = False
if "grok_prediction" not in st.session_state:
    st.session_state.grok_prediction = None

# Known tracks: name -> nearest METAR airport + elevation
try:
    from tracks_library import TRACK_LIBRARY, track_names, suggest_tracks, find_track, geocode_track, match_track_from_slip, TRACK_ICAO
except Exception:
    TRACK_ICAO = {}
    TRACK_LIBRARY = []
    def track_names():
        return []
    def suggest_tracks(query, limit=6):
        return []
    def find_track(query):
        return None
    def geocode_track(city, region, cache=None):
        return (None, None)
    def match_track_from_slip(raw):
        return None

TRACKS = {
    "Numidia Dragway": {"icao": "KSEG", "elevation": 850, "state": "PA"},
    "Maple Grove Raceway": {"icao": "KRDG", "elevation": 280, "state": "PA"},
    "Atco Dragway": {"icao": "KVAY", "elevation": 140, "state": "NJ"},
    "Mason Dixon Dragway": {"icao": "KHGR", "elevation": 516, "state": "MD"},
    "Cecil County Dragway": {"icao": "KILG", "elevation": 75, "state": "MD"},
    "South Jersey Dragway": {"icao": "KACY", "elevation": 65, "state": "NJ"},
    "Lebanon Valley Dragway": {"icao": "KALB", "elevation": 600, "state": "NY"},
    "Other / Custom": {"icao": "KMDT", "elevation": 400, "state": ""}
}

def prepare_slip_image(img_bytes: bytes) -> bytes:
    """Crop to the paper and straighten. Falls back to the original photo."""
    if not img_bytes:
        return img_bytes
    try:
        if CV2_AVAILABLE:
            arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                return img_bytes
            h, w = img.shape[:2]
            scale = 1000 / max(h, w)
            if scale < 1:
                img = cv2.resize(img, (int(w * scale), int(h * scale)))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)
            edges = cv2.dilate(edges, None, iterations=2)
            cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:8]
            quad = None
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4 and cv2.contourArea(approx) > 0.15 * img.shape[0] * img.shape[1]:
                    quad = approx.reshape(4, 2).astype(np.float32)
                    break
            if quad is not None:
                s = quad.sum(axis=1)
                diff = np.diff(quad, axis=1)
                ordered = np.zeros((4, 2), dtype=np.float32)
                ordered[0] = quad[np.argmin(s)]
                ordered[2] = quad[np.argmax(s)]
                ordered[1] = quad[np.argmin(diff)]
                ordered[3] = quad[np.argmax(diff)]
                wA = np.linalg.norm(ordered[1] - ordered[0])
                wB = np.linalg.norm(ordered[2] - ordered[3])
                hA = np.linalg.norm(ordered[3] - ordered[0])
                hB = np.linalg.norm(ordered[2] - ordered[1])
                ww, hh = int(max(wA, wB)), int(max(hA, hB))
                ww, hh = max(ww, 200), max(hh, 200)
                dest = np.array([[0, 0], [ww - 1, 0], [ww - 1, hh - 1], [0, hh - 1]], dtype=np.float32)
                M = cv2.getPerspectiveTransform(ordered, dest)
                warped = cv2.warpPerspective(img, M, (ww, hh))
                lab = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
                warped = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
                hh2, ww2 = warped.shape[:2]
                sc2 = 1000 / max(hh2, ww2)
                if sc2 < 1:
                    warped = cv2.resize(warped, (int(ww2 * sc2), int(hh2 * sc2)))
                ok, buf = cv2.imencode(".jpg", warped, [int(cv2.IMWRITE_JPEG_QUALITY), 78])
                if ok:
                    return buf.tobytes()
        im = Image.open(io.BytesIO(img_bytes))
        im = ImageOps.exif_transpose(im)
        im.thumbnail((1000, 1000))
        im = ImageOps.autocontrast(im, cutoff=2)
        out = io.BytesIO()
        im.convert("RGB").save(out, format="JPEG", quality=78)
        return out.getvalue()
    except Exception:
        return img_bytes

# ====================== HELPERS ======================
def sat_vapor_pressure_hpa(temp_c):
    """Magnus formula — saturation vapor pressure in hPa."""
    return 6.112 * math.exp((17.67 * temp_c) / (temp_c + 243.5))

def calculate_weather(temp_f, altim_inhg, humidity=50, elevation=400):
    """Return DA, water grains, vapor pressure. Racing-style psychrometrics."""
    empty = {
        "density_altitude": None, "water_grains": None,
        "vapor_pressure": None, "sat_pressure": None,
        "air_density_pct": None, "air_density_lbft3": None
    }
    if temp_f is None or altim_inhg is None:
        return empty
    try:
        temp_f = float(temp_f)
        altim = float(altim_inhg)
        rh = float(humidity if humidity is not None else 50)
        temp_c = (temp_f - 32) * 5 / 9
        es = sat_vapor_pressure_hpa(temp_c)
        e = (rh / 100.0) * es  # hPa
        p_hpa = altim * 33.8639
        grains = None
        if p_hpa > e:
            grains = round(4354.0 * e / (p_hpa - e), 1)
        vapor_inhg = round(e / 33.8639, 3)
        sat_inhg = round(es / 33.8639, 3)
        # Racing air density % (Racecar Book / common DA meters)
        abs_r = temp_f + 459.67
        air_pct = round(1736.86 * (altim - vapor_inhg) / abs_r, 2) if abs_r else None
        # lb/ft3 from % of standard 0.076474
        air_lb = round(air_pct / 100.0 * 0.076474, 5) if air_pct else None
        pa = (29.92 - altim) * 1000 + float(elevation)
        da = pa + 120 * (temp_f - 59) + (rh / 100) * 25
        return {
            "density_altitude": round(da),
            "water_grains": grains,
            "vapor_pressure": vapor_inhg,
            "sat_pressure": sat_inhg,
            "air_density_pct": air_pct,
            "air_density_lbft3": air_lb
        }
    except Exception:
        return empty

def calculate_da(temp_f, altim_inhg, humidity=50, elevation=400):
    return calculate_weather(temp_f, altim_inhg, humidity, elevation).get("density_altitude")

def pressure_to_inhg(val):
    if val in [None, ""]:
        return None
    try:
        v = float(val)
    except Exception:
        return None
    if v > 50:
        v = v / 33.8639
    if v < 24 or v > 32.5:
        return None
    return round(v, 2)

def weather_looks_sane(wx: dict) -> bool:
    if not wx:
        return False
    da = wx.get("density_altitude")
    air = wx.get("air_density_pct")
    baro = wx.get("altimeter_inhg")
    try:
        if baro is not None and not (24 <= float(baro) <= 32.5):
            return False
        if da is not None and abs(float(da)) > 12000:
            return False
        if air is not None and not (50 <= float(air) <= 130):
            return False
    except Exception:
        return False
    return wx.get("temp_f") not in [None, ""] and wx.get("altimeter_inhg") not in [None, ""]

def extract_predicted_et(text: str):
    if not text:
        return None
    m = re.search(r"(?:predicted\s*et|1\))\s*[^\d]{0,24}(\d{1,2}\.\d{2,3})", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"\b(\d{1,2}\.\d{3})\b", text)
    return float(m.group(1)) if m else None

def rh_from_temp_dew(temp_c, dew_c):
    try:
        es = sat_vapor_pressure_hpa(temp_c)
        e = sat_vapor_pressure_hpa(dew_c)
        return max(0, min(100, round(100.0 * e / es)))
    except Exception:
        return 50

def _parse_run_when(date_s, time_s):
    raw = f"{date_s or ''} {time_s or ''}".strip()
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %I:%M:%S %p",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%d/%b/%Y %I:%M:%S %p",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(raw.replace("  ", " ").strip(), fmt)
        except Exception:
            continue
    return None

def _metar_obs_dt(m):
    rt = m.get("reportTime") or m.get("receiptTime")
    if rt:
        try:
            return datetime.fromisoformat(str(rt).replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            pass
    ot = m.get("obsTime")
    if ot:
        try:
            ts = float(ot)
            if ts > 1e12:
                ts = ts / 1000.0
            return datetime.utcfromtimestamp(ts)
        except Exception:
            pass
    return None

def _wx_from_metar(m, icao, elev=400):
    temp_c = m.get("temp")
    dew_c = m.get("dewp")
    temp_f = round(temp_c * 9/5 + 32, 1) if temp_c is not None else None
    altim = m.get("altim_in_hg")
    if altim is None:
        altim = pressure_to_inhg(m.get("altim"))
    if altim is None:
        raw = str(m.get("rawOb") or "")
        am = re.search(r"\bA(\d{4})\b", raw)
        if am:
            altim = round(int(am.group(1)) / 100.0, 2)
    humidity = rh_from_temp_dew(temp_c, dew_c) if temp_c is not None and dew_c is not None else 50
    wx = {"temp_f": temp_f, "altimeter_inhg": altim, "humidity_pct": humidity, "icao": icao}
    extra = calculate_weather(temp_f, altim, humidity, elev)
    wx.update(extra)
    obs = _metar_obs_dt(m)
    wx["weather_source"] = f"METAR {icao}" + (f" @ {obs.strftime('%H:%M')}Z" if obs else "")
    return wx

def fetch_weather(icao, when=None, elev=400):
    try:
        hours = 18 if when else 4
        url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours={hours}"
        r = requests.get(url, timeout=8, headers={"User-Agent": "SmartSlip/2.8 (drag racing weather)"})
        if r.status_code != 200:
            return None
        data = r.json() or []
        if not data:
            return None
        m = data[0]
        if when:
            best, best_diff = data[0], None
            for row in data:
                odt = _metar_obs_dt(row)
                if not odt:
                    continue
                diff = abs((odt - when).total_seconds())
                if best_diff is None or diff < best_diff:
                    best, best_diff = row, diff
            m = best
        wx = _wx_from_metar(m, icao, elev)
        return wx if weather_looks_sane(wx) else None
    except Exception:
        return None

def canonicalize_track(name):
    matched = match_track_from_slip(name)
    if matched:
        return matched
    rec = find_track(name)
    if rec:
        return rec["name"]
    return (name or "").strip()

def render_track_picker(prefix: str):
    last_track = st.session_state.get("last_pred_track")
    if last_track is None:
        last_track = "Numidia Dragway"
    nkey = f"{prefix}_track_n"
    if nkey not in st.session_state:
        st.session_state[nkey] = 0
    labels = {}
    names = []
    for name, city, region in TRACK_LIBRARY:
        labels[name] = f"{name} — {city}, {region}"
        names.append(name)
    for extra in list(TRACKS.keys()) + list(st.session_state.get("saved_tracks") or []):
        if extra and extra not in labels and extra != "Other / Custom":
            labels[extra] = extra
            names.append(extra)
    if last_track:
        labels.setdefault(last_track, last_track)
    options = sorted(set(names))
    picked = st.selectbox(
        "Drag Strip",
        options,
        index=None,
        placeholder="Tap to change track",
        format_func=lambda n: labels.get(n, n),
        key=f"{prefix}_track_select_{st.session_state[nkey]}",
    )
    pred_track = canonicalize_track(picked) or (picked or "").strip() or last_track
    if pred_track:
        saved = list(st.session_state.get("saved_tracks") or [])
        if pred_track not in saved:
            saved.append(pred_track)
            st.session_state.saved_tracks = saved
        if picked and pred_track != last_track:
            st.session_state.last_pred_track = pred_track
            st.rerun()
        st.session_state.last_pred_track = pred_track
        st.caption(f"Using **{pred_track}**")
    return pred_track

def fetch_weather_noaa(lat, lon):
    try:
        headers = {"User-Agent": "SmartSlip/2.8 (drag racing weather)", "Accept": "application/geo+json"}
        pts = requests.get(f"https://api.weather.gov/points/{lat:.3f},{lon:.3f}", timeout=8, headers=headers)
        if pts.status_code != 200:
            return None
        stations = (pts.json().get("properties") or {}).get("observationStations")
        if not stations:
            return None
        stn = requests.get(stations, timeout=8, headers=headers)
        if stn.status_code != 200:
            return None
        feats = (stn.json() or {}).get("features") or []
        if not feats:
            return None
        sid = (feats[0].get("properties") or {}).get("stationIdentifier") or feats[0].get("id")
        obs_url = feats[0].get("id")
        if obs_url:
            latest = requests.get(obs_url.rstrip("/") + "/observations/latest", timeout=8, headers=headers)
        else:
            return None
        if latest.status_code != 200:
            return None
        p = (latest.json() or {}).get("properties") or {}
        temp_c = (p.get("temperature") or {}).get("value")
        dew_c = (p.get("dewpoint") or {}).get("value")
        rh = (p.get("relativeHumidity") or {}).get("value")
        pres = (p.get("barometricPressure") or {}).get("value") or (p.get("seaLevelPressure") or {}).get("value")
        temp_f = round(temp_c * 9/5 + 32, 1) if temp_c is not None else None
        if rh is None and temp_c is not None and dew_c is not None:
            rh = rh_from_temp_dew(temp_c, dew_c)
        # NOAA pressure is Pa
        altim = None
        if pres is not None:
            altim = pressure_to_inhg(float(pres) / 100.0)
        wx = {"temp_f": temp_f, "humidity_pct": rh, "altimeter_inhg": altim, "weather_source": f"NWS {sid or ''}"}
        extra = calculate_weather(temp_f, altim, rh or 50)
        wx.update(extra)
        return wx if weather_looks_sane(wx) else None
    except Exception:
        return None

def fetch_weather_for_track(track_name, when=None):
    rec = find_track(track_name)
    if not rec:
        rec = {
            "name": (track_name or "").strip() or "Unknown",
            "city": (track_name or "").strip(),
            "region": "",
            "address": (track_name or "").strip(),
            "lat": None, "lon": None, "elev_ft": 400, "icao": None,
        }
    elev = rec.get("elev_ft") or 400
    icao = rec.get("icao")
    if not icao and rec.get("name"):
        icao = TRACK_ICAO.get(str(rec.get("name") or "").lower())
    if not icao:
        key = re.sub(r"[^a-z0-9]+", " ", str(track_name or "").lower()).strip()
        for name, code in (TRACK_ICAO or {}).items():
            if name in key or key in name:
                icao = code
                break
    if not icao:
        return None
    metar = fetch_weather(icao, when=when, elev=elev)
    if not metar:
        return None
    metar["track"] = rec.get("name") or track_name
    metar["address"] = rec.get("address")
    metar["elev_ft"] = elev
    return metar if weather_looks_sane(metar) else None

def parse_import_block(block):
    data = {}
    lines = block.strip().split("\n")
    if len(lines) <= 1:
        matches = re.findall(r'(\w+)=([^\s=]+)', block)
        for k, v in matches:
            k_lower = k.lower()
            if v.lower() in ["none", "null", ""]:
                continue
            try:
                if k_lower in ["et", "sixty_ft", "eighth_et", "trap_mph", "reaction_time",
                               "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude", "three_thirty_ft",
                               "water_grains", "vapor_pressure", "sat_pressure", "air_density_pct", "air_density_lbft3",
                               "eighth_mph", "thousand_et", "mph_660", "660_mph",
                               "dial", "mov"]:
                    data[k_lower] = float(v)
                else:
                    data[k_lower] = v
            except:
                data[k_lower] = v
    else:
        for line in lines:
            if "=" in line:
                k, v = [x.strip() for x in line.split("=", 1)]
                if v.lower() in ["none", "null", ""]:
                    continue
                try:
                    if k.lower() in ["et", "sixty_ft", "eighth_et", "trap_mph", "reaction_time",
                                     "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude", "three_thirty_ft",
                                     "water_grains", "vapor_pressure", "sat_pressure", "air_density_pct", "air_density_lbft3",
                                     "eighth_mph", "thousand_et", "mph_660", "660_mph",
                                     "dial", "mov"]:
                        data[k.lower()] = float(v)
                    else:
                        data[k.lower()] = v
                except:
                    data[k.lower()] = v
    if data.get("eighth_mph") in [None, ""] and data.get("mph_660") not in [None, ""]:
        data["eighth_mph"] = data.get("mph_660")
    if data.get("eighth_mph") in [None, ""] and data.get("660_mph") not in [None, ""]:
        data["eighth_mph"] = data.get("660_mph")
    if data.get("thousand_et") in [None, ""] and data.get("et_1000") not in [None, ""]:
        data["thousand_et"] = data.get("et_1000")
    if data.get("thousand_et") in [None, ""] and data.get("1000_et") not in [None, ""]:
        data["thousand_et"] = data.get("1000_et")
    return data

def get_profile_by_id(profile_id):
    for p in st.session_state.car_profiles:
        if str(p.get("id")) == str(profile_id):
            return p
    return None

# ====================== GROK API ======================
def get_xai_client():
    if not OPENAI_AVAILABLE:
        return None
    # Try several common ways people paste the key
    api_key = None
    try:
        api_key = st.secrets.get("XAI_API_KEY") or st.secrets.get("xai_api_key") or st.secrets.get("XAI_KEY")
        # Sometimes people put it under a section
        if not api_key and "xai" in st.secrets:
            api_key = st.secrets["xai"].get("api_key") or st.secrets["xai"].get("XAI_API_KEY")
    except Exception:
        pass
    if not api_key:
        return None
    return OpenAI(
        api_key=str(api_key).strip(),
        base_url="https://api.x.ai/v1"
    )

def get_xai_api_key():
    try:
        api_key = st.secrets.get("XAI_API_KEY") or st.secrets.get("xai_api_key") or st.secrets.get("XAI_KEY")
        if not api_key and "xai" in st.secrets:
            api_key = st.secrets["xai"].get("api_key") or st.secrets["xai"].get("XAI_API_KEY")
        return str(api_key).strip() if api_key else None
    except Exception:
        return None

def call_grok(prompt: str, image_bytes: bytes = None, model: str = "grok-4.6", max_tokens: int = 400):
    """Call Grok via xAI API. Supports optional image for vision."""
    client = get_xai_client()
    if client is None:
        return None, "Grok API not configured. Add XAI_API_KEY to Streamlit Secrets."

    try:
        messages = []
        if image_bytes:
            b64 = base64.b64encode(image_bytes).decode("utf-8")
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

def call_grok_with_search(prompt: str, model: str = "grok-4-fast"):
    """Call Grok with web search so it can look up track weather."""
    api_key = get_xai_api_key()
    if not api_key:
        return None, "Grok API not configured."
    try:
        r = requests.post(
            "https://api.x.ai/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": prompt,
                "tools": [{"type": "web_search"}]
            },
            timeout=60
        )
        if r.status_code != 200:
            text, err = call_grok(prompt, model="grok-4.6")
            return text, err
        data = r.json()
        # Responses API can return output in several shapes
        if isinstance(data.get("output_text"), str) and data["output_text"].strip():
            return data["output_text"], None
        chunks = []
        for item in data.get("output", []) or []:
            if isinstance(item, dict):
                if item.get("type") == "message":
                    for c in item.get("content", []) or []:
                        if isinstance(c, dict) and c.get("text"):
                            chunks.append(c["text"])
                elif item.get("text"):
                    chunks.append(item["text"])
        if chunks:
            return "\n".join(chunks), None
        return json.dumps(data)[:2000], None
    except Exception as e:
        text, err = call_grok(prompt, model="grok-4.6")
        if text:
            return text, None
        return None, str(e)

def grok_lookup_weather(track, date=None, time=None):
    """Have Grok search for track weather at a specific date/time."""
    when = "current conditions"
    if date or time:
        when = f"{date or ''} {time or ''}".strip()
    prompt = f"""Look up drag racing weather for this track and time.

Track: {track}
When: {when}

Search Air Density Online and nearby airport METAR if needed.
Prefer historical weather for that exact date/time if it is in the past.
Prefer current weather if no date/time is given.

Return ONLY key=value lines:
track=
date=
time=
temp_f=
humidity_pct=
altimeter_inhg=
water_grains=
density_altitude=
air_density_pct=
vapor_pressure=
weather_source=
notes=

If a value is unknown use None. Do not invent precise numbers if you cannot find them."""
    return call_grok_with_search(prompt)

def fill_weather_for_run(run: dict) -> dict:
    if run.get("temp_f") not in [None, ""] and run.get("altimeter_inhg") not in [None, ""]:
        run["weather_pending"] = ""
        return run
    track = run.get("track") or "Numidia Dragway"
    when = _parse_run_when(run.get("date"), run.get("time"))
    wx = fetch_weather_for_track(track, when=when)
    if not wx:
        return run
    for k in ["temp_f", "altimeter_inhg", "humidity_pct", "density_altitude",
              "water_grains", "air_density_pct", "vapor_pressure"]:
        if run.get(k) in [None, ""] and wx.get(k) not in [None, ""]:
            run[k] = wx[k]
    run["weather_pending"] = ""
    update_run_in_sheet(run)
    return run

def process_pending_weather():
    if st.session_state.get("wx_busy"):
        return
    queue = list(st.session_state.get("wx_queue") or [])
    if not queue:
        for r in st.session_state.get("runs") or []:
            pending = str(r.get("weather_pending") or "").lower() in ["yes", "1", "true"]
            missing = r.get("temp_f") in [None, ""] and r.get("density_altitude") in [None, ""]
            if (pending or missing) and r.get("id"):
                queue.append(r.get("id"))
                break
    if not queue:
        return
    rid = queue[0]
    run = next((x for x in st.session_state.runs if str(x.get("id")) == str(rid)), None)
    st.session_state.wx_busy = True
    try:
        if run:
            fill_weather_for_run(run)
    except Exception:
        pass
    st.session_state.wx_busy = False
    st.session_state.wx_queue = [x for x in queue[1:] if str(x) != str(rid)]

# ====================== GOOGLE SHEETS ======================
_GSP_CLIENT = None
_GSP_SHEET = None

def get_gspread_client():
    global _GSP_CLIENT
    if _GSP_CLIENT is not None:
        return _GSP_CLIENT
    if not GSPREAD_AVAILABLE:
        return None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"]
            )
            _GSP_CLIENT = gspread.authorize(creds)
            return _GSP_CLIENT
    except Exception as e:
        st.error(f"Google Sheets auth error: {e}")
    return None

def get_spreadsheet():
    global _GSP_SHEET
    if _GSP_SHEET is not None:
        return _GSP_SHEET
    client = get_gspread_client()
    if client is None:
        return None
    try:
        _GSP_SHEET = client.open(SHEET_NAME)
        return _GSP_SHEET
    except Exception:
        _GSP_SHEET = None
        return None

RUN_HEADERS = [
    "id", "user", "date", "time", "track", "vehicle", "profile_id",
    "dial", "reaction_time", "sixty_ft", "three_thirty_ft", "eighth_et",
    "eighth_mph", "thousand_et", "et", "trap_mph", "mov",
    "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct",
    "water_grains", "air_density_pct", "vapor_pressure", "notes", "excluded", "weather_pending"
]

def _lower_row(r: dict) -> dict:
    return {str(k).strip().lower(): v for k, v in (r or {}).items()}

def _user_idents():
    return {
        str(st.session_state.get("user_email") or "").strip().lower(),
        str(st.session_state.get("user_name") or "").strip().lower(),
    } - {""}

def _row_belongs_to_user(r: dict, owned_pids=None, owned_names=None) -> bool:
    if st.session_state.is_admin:
        return True
    ident = _user_idents()
    owned_pids = owned_pids or {str(p.get("id") or "") for p in (st.session_state.get("car_profiles") or [])} - {""}
    owned_names = owned_names or {str(p.get("name") or "").strip().lower() for p in (st.session_state.get("car_profiles") or [])} - {""}
    u = str(r.get("user") or "").strip().lower()
    if u and u in ident:
        return True
    if u and any(len(i) > 2 and (u == i or u.endswith(i) or i in u) for i in ident):
        return True
    if u and u in owned_names:
        return True
    if str(r.get("profile_id") or "") in owned_pids:
        return True
    veh = str(r.get("vehicle") or "").strip().lower()
    if veh and veh in owned_names:
        return True
    if veh and any(n and len(n) > 3 and (n in veh or veh in n) for n in owned_names):
        return True
    return False

def load_data_from_sheet():
    client = get_gspread_client()
    if client is None:
        st.session_state.last_sheet_error = "Google Sheets client not connected."
        return False
    try:
        sheet = client.open(SHEET_NAME)
        try:
            ws_runs = sheet.worksheet(WORKSHEET_RUNS)
            raw = ws_runs.get_all_records()
        except Exception:
            raw = []
        runs = []
        for rec in raw:
            r = _lower_row(rec)
            for key in ["et", "sixty_ft", "three_thirty_ft", "eighth_et", "eighth_mph",
                        "thousand_et", "trap_mph", "dial", "reaction_time", "mov",
                        "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct",
                        "water_grains", "air_density_pct", "vapor_pressure"]:
                if key in r and (r[key] == "" or r[key] is None):
                    r[key] = None
                elif key in r:
                    try:
                        r[key] = float(r[key])
                    except Exception:
                        pass
            runs.append(r)
        st.session_state.last_sheet_error = ""
        try:
            ws_profiles = sheet.worksheet(WORKSHEET_PROFILES)
            profiles = [_lower_row(p) for p in ws_profiles.get_all_records()]
        except Exception:
            profiles = []
        ident = _user_idents()
        if not st.session_state.is_admin:
            owned_profiles = []
            for p in profiles:
                pu = str(p.get("user") or "").strip().lower()
                if pu in ident or any(len(i) > 2 and (pu == i or i in pu or pu in i) for i in ident):
                    owned_profiles.append(p)
            owned_pids = {str(p.get("id") or "") for p in owned_profiles} - {""}
            owned_names = {str(p.get("name") or "").strip().lower() for p in owned_profiles} - {""}
            for r in runs:
                ru = str(r.get("user") or "").strip().lower()
                veh = str(r.get("vehicle") or "").strip().lower()
                if ru in ident or (veh and veh in owned_names):
                    if r.get("profile_id"):
                        owned_pids.add(str(r.get("profile_id")))
                    if veh:
                        owned_names.add(veh)
            for p in profiles:
                if str(p.get("id") or "") in owned_pids:
                    owned_names.add(str(p.get("name") or "").strip().lower())
                    if p not in owned_profiles:
                        owned_profiles.append(p)
            profiles = owned_profiles
            kept = [r for r in runs if _row_belongs_to_user(r, owned_pids, owned_names)]
            owned_days = {
                (str(r.get("date") or ""), str(r.get("track") or "").strip().lower())
                for r in kept
            }
            for r in runs:
                if r in kept:
                    continue
                ru = str(r.get("user") or "").strip().lower()
                key = (str(r.get("date") or ""), str(r.get("track") or "").strip().lower())
                if key in owned_days and (not ru or ru in owned_names or _row_belongs_to_user(r, owned_pids, owned_names)):
                    kept.append(r)
            runs = kept
        st.session_state.car_profiles = profiles
        st.session_state.runs = runs
        st.session_state.data_loaded = True
        return True
    except Exception as e:
        st.session_state.last_sheet_error = str(e)
        st.warning(f"Could not load from Google Sheet: {e}")
        return False

def _ensure_runs_ws(sheet):
    need_cols = 30
    need_rows = 3000
    try:
        ws = sheet.worksheet(WORKSHEET_RUNS)
    except Exception:
        ws = sheet.add_worksheet(title=WORKSHEET_RUNS, rows=need_rows, cols=need_cols)
        ws.update("A1", [RUN_HEADERS])
        return ws
    try:
        ws.resize(rows=max(ws.row_count or 1000, need_rows),
                  cols=max(ws.col_count or 23, need_cols))
    except Exception:
        pass
    headers = [str(h).strip() for h in ws.row_values(1)]
    if not headers:
        ws.update("A1", [RUN_HEADERS])
        return ws
    lower = [h.lower() for h in headers]
    missing = [h for h in RUN_HEADERS if h not in lower]
    if missing:
        start = len(headers) + 1
        cells = [gspread.Cell(1, start + i, h) for i, h in enumerate(missing)]
        ws.update_cells(cells)
    return ws

def _run_fingerprint(run: dict) -> str:
    return "|".join([
        str(run.get("user") or "").strip().lower(),
        str(run.get("date") or "").strip(),
        str(run.get("time") or "").strip(),
        str(run.get("et") or "").strip(),
        str(run.get("sixty_ft") or "").strip(),
        str(run.get("profile_id") or "").strip(),
    ])

def save_run_to_sheet(run: dict):
    client = get_gspread_client()
    if client is None:
        st.session_state.last_sheet_error = "Google Sheets client not connected."
        return False
    try:
        sheet = client.open(SHEET_NAME)
        ws = _ensure_runs_ws(sheet)
        if not run.get("user"):
            run["user"] = (st.session_state.get("user_email") or st.session_state.get("user_name") or "").strip()
        headers = [str(h).strip() for h in ws.row_values(1)]
        records = ws.get_all_records()
        fp = _run_fingerprint(run)
        existing_idx = None
        for i, rec in enumerate(records, start=2):
            if run.get("id") and str(rec.get("id")) == str(run.get("id")):
                existing_idx = i
                break
            if fp and _run_fingerprint(rec) == fp:
                existing_idx = i
                if not run.get("id"):
                    run["id"] = rec.get("id")
                break
        row = []
        for h in headers:
            val = run.get(h, run.get(h.lower(), ""))
            if val is None:
                val = ""
            row.append(str(val))
        if existing_idx:
            for col, val in enumerate(row, start=1):
                ws.update_cell(existing_idx, col, val)
        else:
            ws.append_row(row, value_input_option="USER_ENTERED")
        st.session_state.last_sheet_error = ""
        return True
    except Exception as e:
        st.session_state.last_sheet_error = str(e)
        st.error(f"Failed to save run: {e}")
        return False

def _run_row_index(ws, run_id):
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("id")) == str(run_id):
            return i, row
    return None, None

def delete_run_from_sheet(run_id):
    client = get_gspread_client()
    if client is None:
        return False
    try:
        ws = client.open(SHEET_NAME).worksheet(WORKSHEET_RUNS)
        idx, _ = _run_row_index(ws, run_id)
        if idx:
            ws.delete_rows(idx, idx)
        return True
    except Exception:
        return False

def update_run_in_sheet(run: dict):
    client = get_gspread_client()
    if client is None or not run.get("id"):
        return False
    try:
        ws = client.open(SHEET_NAME).worksheet(WORKSHEET_RUNS)
        headers = ws.row_values(1)
        idx, _ = _run_row_index(ws, run.get("id"))
        if not idx:
            return save_run_to_sheet(run)
        for h in headers:
            ws.update_cell(idx, headers.index(h) + 1, run.get(h, "") if run.get(h) is not None else "")
        return True
    except Exception:
        return False

def set_run_excluded(run_id, excluded: bool):
    client = get_gspread_client()
    if client is None:
        return False
    try:
        ws = client.open(SHEET_NAME).worksheet(WORKSHEET_RUNS)
        headers = ws.row_values(1)
        if "excluded" not in headers:
            ws.update_cell(1, len(headers) + 1, "excluded")
            headers = ws.row_values(1)
        idx, _ = _run_row_index(ws, run_id)
        if idx and "excluded" in headers:
            ws.update_cell(idx, headers.index("excluded") + 1, "yes" if excluded else "")
        return True
    except Exception:
        return False

def save_bug_report(message: str):
    client = get_gspread_client()
    if client is None:
        return False, "Google Sheet is not connected."
    try:
        sheet = client.open(SHEET_NAME)
        try:
            ws = sheet.worksheet(WORKSHEET_BUGS)
        except Exception:
            ws = sheet.add_worksheet(title=WORKSHEET_BUGS, rows=500, cols=6)
            ws.append_row(["created_at", "user", "email", "message"])
        ws.append_row([
            datetime.now().isoformat(timespec="seconds"),
            st.session_state.get("user_name") or "",
            st.session_state.get("user_email") or "",
            message.strip()
        ])
        return True, "Report sent."
    except Exception as e:
        return False, str(e)

def save_profile_to_sheet(profile: dict):
    client = get_gspread_client()
    if client is None:
        return False
    try:
        sheet = client.open(SHEET_NAME)
        try:
            ws = sheet.worksheet(WORKSHEET_PROFILES)
        except:
            ws = sheet.add_worksheet(title=WORKSHEET_PROFILES, rows=200, cols=15)
            headers = ["id", "user", "name", "car_number", "car_type", "fuel_type", "weight",
                       "tire_size", "tire_type", "trans_first_gear", "rear_gear"]
            ws.append_row(headers)
        profile["user"] = st.session_state.get("user_email") or st.session_state.user_name
        headers = ws.row_values(1)
        if "car_number" not in headers:
            ws.update_cell(1, len(headers) + 1, "car_number")
            headers = ws.row_values(1)
        row = [profile.get(h, "") for h in headers]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save profile: {e}")
        return False

def update_profile_to_sheet(profile: dict):
    client = get_gspread_client()
    if client is None:
        return False
    try:
        sheet = client.open(SHEET_NAME)
        ws = sheet.worksheet(WORKSHEET_PROFILES)
        headers = ws.row_values(1)
        if "car_number" not in headers:
            ws.update_cell(1, len(headers) + 1, "car_number")
            headers = ws.row_values(1)
        records = ws.get_all_records()
        pid = str(profile.get("id"))
        for i, row in enumerate(records, start=2):
            if str(row.get("id")) == pid:
                for h in headers:
                    if h in profile:
                        ws.update_cell(i, headers.index(h) + 1, profile.get(h, ""))
                return True
        return save_profile_to_sheet(profile)
    except Exception as e:
        st.error(f"Failed to update profile: {e}")
        return False

def delete_profile_and_runs(profile: dict):
    pid = str(profile.get("id", ""))
    pname = str(profile.get("name", ""))
    ident = [
        str(st.session_state.get("user_email") or "").lower(),
        str(st.session_state.get("user_name") or "").lower(),
    ]
    st.session_state.car_profiles = [
        p for p in st.session_state.car_profiles if str(p.get("id")) != pid
    ]
    st.session_state.runs = [
        r for r in st.session_state.runs
        if not (
            str(r.get("profile_id", "")) == pid
            or str(r.get("vehicle", "")) == pname
        )
    ]
    client = get_gspread_client()
    if client is None:
        return True
    try:
        sheet = client.open(SHEET_NAME)
        try:
            ws = sheet.worksheet(WORKSHEET_PROFILES)
            records = ws.get_all_records()
            drop = []
            for i, row in enumerate(records, start=2):
                if str(row.get("id")) == pid:
                    drop.append(i)
            for i in reversed(drop):
                ws.delete_rows(i, i)
        except Exception:
            pass
        try:
            ws = sheet.worksheet(WORKSHEET_RUNS)
            records = ws.get_all_records()
            drop = []
            for i, row in enumerate(records, start=2):
                same_user = str(row.get("user", "")).lower() in ident or st.session_state.is_admin
                same_prof = str(row.get("profile_id", "")) == pid or str(row.get("vehicle", "")) == pname
                if same_user and same_prof:
                    drop.append(i)
            for i in reversed(drop):
                ws.delete_rows(i, i)
        except Exception:
            pass
        return True
    except Exception as e:
        st.error(f"Could not delete from Google Sheet: {e}")
        return False

def get_jobs_ws():
    try:
        sheet = get_spreadsheet()
        if sheet is None:
            return None
        try:
            return sheet.worksheet(WORKSHEET_PREDICT)
        except Exception:
            ws = sheet.add_worksheet(title=WORKSHEET_PREDICT, rows=400, cols=8)
            ws.append_row(["id", "user", "kind", "status", "result", "error", "extra", "created"])
            return ws
    except Exception:
        return None

def write_job(job_id, user, kind, status, result="", error="", extra=""):
    JOB_MEM = PRED_PROMPTS
    JOB_MEM[job_id] = {
        "id": job_id, "user": user, "kind": kind, "status": status,
        "result": result or "", "error": error or "", "extra": extra or "",
    }
    ws = get_jobs_ws()
    if ws is None:
        return
    try:
        records = ws.get_all_records()
        headers = ws.row_values(1) or ["id", "user", "kind", "status", "result", "error", "extra", "created"]
        row = {
            "id": job_id, "user": user or "", "kind": kind or "",
            "status": status, "result": (result or "")[:4000],
            "error": (error or "")[:1000], "extra": (extra or "")[:1500],
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        for i, rec in enumerate(records, start=2):
            if str(rec.get("id")) == str(job_id):
                for h in headers:
                    if h in row:
                        ws.update_cell(i, headers.index(h) + 1, row.get(h, ""))
                return
        ws.append_row([row.get(h, "") for h in headers])
    except Exception:
        pass

def read_job(job_id):
    if not job_id:
        return None
    mem = PRED_PROMPTS.get(job_id)
    if mem:
        return mem
    try:
        ws = get_jobs_ws()
        if ws is None:
            return None
        for rec in ws.get_all_records():
            if str(rec.get("id")) == str(job_id):
                return rec
    except Exception:
        pass
    return None

def latest_user_job(user, kind):
    user = str(user or "").strip().lower()
    best = None
    for rec in list(PRED_PROMPTS.values()):
        if str(rec.get("kind")) == kind and str(rec.get("user") or "").strip().lower() == user:
            if best is None or str(rec.get("id")) > str(best.get("id")):
                best = rec
    ws = get_jobs_ws()
    if ws is not None:
        try:
            for rec in ws.get_all_records():
                if str(rec.get("kind")) == kind and str(rec.get("user") or "").strip().lower() == user:
                    if best is None or str(rec.get("id")) > str(best.get("id")):
                        best = rec
        except Exception:
            pass
    return best

def wait_banner(title):
    st.markdown(
        f"<div class='ss-wait'>{title}<span>Stay in the app until this finishes</span><div class='ss-bar'><i></i></div></div>",
        unsafe_allow_html=True,
    )

def log_timing(kind, user, seconds, ok=True, extra=""):
    try:
        sheet = get_spreadsheet()
        if sheet is None:
            return
        try:
            ws = sheet.worksheet(WORKSHEET_TIMINGS)
        except Exception:
            ws = sheet.add_worksheet(title=WORKSHEET_TIMINGS, rows=500, cols=6)
            ws.append_row(["when", "user", "kind", "seconds", "ok", "extra"])
        ws.append_row([
            datetime.now().isoformat(timespec="seconds"),
            str(user or "")[:80],
            kind,
            f"{float(seconds):.1f}",
            "yes" if ok else "no",
            str(extra or "")[:200],
        ], value_input_option="USER_ENTERED")
    except Exception:
        pass

def _auto_worker(job_id, prompt, img_bytes, ctx):
    try:
        t0 = time.perf_counter()
        result, err = call_grok(prompt, image_bytes=img_bytes, model="grok-4-fast", max_tokens=350)
        log_timing("auto", ctx.get("user"), time.perf_counter() - t0, ok=not bool(err), extra="fast")
        data = parse_import_block(result) if result and not err else {}

        def _swap_rt_sixty(d):
            if not d:
                return d
            try:
                rt = float(d["reaction_time"]) if d.get("reaction_time") not in [None, ""] else None
                s60 = float(d["sixty_ft"]) if d.get("sixty_ft") not in [None, ""] else None
                dial = float(d["dial"]) if d.get("dial") not in [None, ""] else None
            except Exception:
                return d
            if s60 is None and rt is not None and 1.15 <= rt <= 2.40:
                if dial is None or 0.001 <= abs(dial) <= 0.999:
                    d["sixty_ft"] = rt
                    d["reaction_time"] = dial
                    d["dial"] = None
            return d

        data = _swap_rt_sixty(data)

        def _has_finish(d):
            return d.get("et") not in [None, ""] or d.get("eighth_et") not in [None, ""]

        def _has_sixty(d):
            return d.get("sixty_ft") not in [None, ""]

        weak = (not data) or (not _has_sixty(data)) or (not _has_finish(data))
        if weak:
            t1 = time.perf_counter()
            result2, err2 = call_grok(prompt, image_bytes=img_bytes, model="grok-4.6", max_tokens=350)
            log_timing("auto-4.6", ctx.get("user"), time.perf_counter() - t1, ok=not bool(err2), extra="retry")
            data2 = _swap_rt_sixty(parse_import_block(result2) if result2 and not err2 else {})
            if data2 and (_has_sixty(data2) or _has_finish(data2) or not data):
                data, err, result = data2, err2, result2
        if err and not data:
            write_job(job_id, ctx.get("user"), "auto", "error", error=err or "Could not read the slip")
            return
        if not data:
            write_job(job_id, ctx.get("user"), "auto", "error", error="Could not read the slip. Try a clearer photo.")
            return
        def _num(k):
            try:
                v = data.get(k)
                return None if v in [None, ""] else float(v)
            except Exception:
                return None
        dial_n, rt_n, s60_n = _num("dial"), _num("reaction_time"), _num("sixty_ft")
        if s60_n is None and rt_n is not None and 1.15 <= rt_n <= 2.40:
            if dial_n is None or 0.001 <= abs(dial_n) <= 0.999:
                data["sixty_ft"] = rt_n
                data["reaction_time"] = dial_n
                data["dial"] = None
        notes = ctx.get("notes") or ""
        final_notes = data.get("notes", "")
        if notes:
            final_notes = (final_notes + " | " + notes).strip(" |")
        new_run = {
            "id": str(datetime.now().timestamp()),
            "user": ctx.get("user"),
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "time": data.get("time", ""),
            "track": canonicalize_track(data.get("track")) or data.get("track") or "Unknown",
            "vehicle": ctx.get("profile_name") or "Main Car",
            "profile_id": ctx.get("profile_id"),
            "dial": data.get("dial"),
            "reaction_time": data.get("reaction_time"),
            "et": data.get("et"),
            "sixty_ft": data.get("sixty_ft"),
            "three_thirty_ft": data.get("three_thirty_ft"),
            "eighth_et": data.get("eighth_et"),
            "eighth_mph": data.get("eighth_mph"),
            "thousand_et": data.get("thousand_et"),
            "trap_mph": data.get("trap_mph"),
            "mov": data.get("mov"),
            "notes": final_notes,
            "weather_pending": "yes",
        }
        track = new_run.get("track")
        when = _parse_run_when(new_run.get("date"), new_run.get("time"))
        wx = fetch_weather_for_track(track, when=when) if track and track != "Unknown" else None
        if wx and weather_looks_sane(wx):
            for k in ["temp_f", "altimeter_inhg", "humidity_pct", "density_altitude",
                      "water_grains", "air_density_pct", "vapor_pressure"]:
                if wx.get(k) not in [None, ""]:
                    new_run[k] = wx.get(k)
            new_run["weather_pending"] = ""
        save_run_to_sheet(new_run)
        et_s = ""
        try:
            if new_run.get("et") not in [None, ""]:
                et_s = f"{float(new_run['et']):.3f}"
        except Exception:
            pass
        write_job(job_id, ctx.get("user"), "auto", "done", result=et_s or "saved", extra=track or "")
        PRED_PROMPTS.setdefault(job_id, {})["run"] = new_run
    except Exception as e:
        write_job(job_id, ctx.get("user"), "auto", "error", error=str(e))

def _predict_worker(job_id, prompt, user, wx_bits):
    try:
        t0 = time.perf_counter()
        result, err = call_grok(prompt, model="grok-4.6", max_tokens=220)
        log_timing("predict", user, time.perf_counter() - t0, ok=not bool(err), extra=(err or "")[:80])
        if err:
            write_job(job_id, user, "predict", "error", extra=wx_bits or "", error=err)
        else:
            write_job(job_id, user, "predict", "done", result=result or "", extra=wx_bits or "")
    except Exception as e:
        write_job(job_id, user, "predict", "error", extra=wx_bits or "", error=str(e))

# ====================== AUTH ======================
def _hash_pw(password: str, salt: str = None):
    salt = salt or pysecrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return salt, digest

def _verify_pw(password: str, salt: str, digest: str):
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return hmac.compare_digest(check, digest)

def _admin_password():
    try:
        return st.secrets.get("ADMIN_PASSWORD", ADMIN_PASSWORD)
    except Exception:
        return ADMIN_PASSWORD

def get_users_ws():
    client = get_gspread_client()
    if client is None:
        return None
    sheet = client.open(SHEET_NAME)
    try:
        return sheet.worksheet(WORKSHEET_USERS)
    except Exception:
        ws = sheet.add_worksheet(title=WORKSHEET_USERS, rows=500, cols=12)
        ws.append_row(["email", "display_name", "pw_salt", "pw_hash", "session_token",
                       "device_token", "reset_code", "reset_expires", "created_at"])
        return ws

def _ensure_header(ws, name):
    headers = ws.row_values(1)
    if name not in headers:
        ws.update_cell(1, len(headers) + 1, name)
        headers.append(name)
    return headers

def _set_user_cell(ws, idx, name, value):
    headers = _ensure_header(ws, name)
    ws.update_cell(idx, headers.index(name) + 1, value)

def find_user(email: str):
    ws = get_users_ws()
    if ws is None:
        return None, None
    email = email.strip().lower()
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row.get("email", "")).strip().lower() == email:
            return row, i
    return None, None

def create_user(email: str, password: str, display_name: str):
    ws = get_users_ws()
    if ws is None:
        return False, "Google Sheets is not connected. Cannot create accounts."
    email = email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    existing, _ = find_user(email)
    if existing:
        return False, "That email already has an account. Use Log in or Reset password."
    salt, digest = _hash_pw(password)
    session = pysecrets.token_urlsafe(24)
    device = pysecrets.token_urlsafe(24)
    ws.append_row([email, display_name.strip() or email.split("@")[0],
                   salt, digest, session, "", "", datetime.now().isoformat()])
    _, idx = find_user(email)
    if idx:
        _set_user_cell(ws, idx, "device_token", device)
    return True, device

def login_user(email: str, password: str):
    row, idx = find_user(email)
    if not row:
        return False, None, "No account with that email."
    if not _verify_pw(password, str(row.get("pw_salt", "")), str(row.get("pw_hash", ""))):
        return False, None, "Wrong password."
    ws = get_users_ws()
    device = str(row.get("device_token", "")).strip()
    if not device:
        device = pysecrets.token_urlsafe(24)
        if ws and idx:
            _set_user_cell(ws, idx, "device_token", device)
    return True, device, "ok"

def user_from_token(email: str, token: str):
    row, _ = find_user(email)
    if not row or not token:
        return None
    for key in ("device_token", "session_token"):
        saved = str(row.get(key, "")).strip()
        if saved and hmac.compare_digest(saved, token):
            return row
    return None

def _secret_val(*names):
    """Read a secret from top level or common nested sections."""
    try:
        for name in names:
            if name in st.secrets and st.secrets[name] not in [None, ""]:
                return st.secrets[name]
        for section in ("smtp", "email", "xai"):
            if section in st.secrets:
                block = st.secrets[section]
                for name in names:
                    if name in block and block[name] not in [None, ""]:
                        return block[name]
    except Exception:
        pass
    return ""

def send_reset_email(to_email: str, code: str):
    try:
        host = str(_secret_val("SMTP_HOST", "smtp_host") or "")
        user = str(_secret_val("SMTP_USER", "smtp_user") or "").replace(" ", "")
        pw = str(_secret_val("SMTP_PASSWORD", "smtp_password") or "").replace(" ", "")
        port_raw = _secret_val("SMTP_PORT", "smtp_port") or 587
        port = int(port_raw)
        frm = str(_secret_val("SMTP_FROM", "smtp_from") or user).replace(" ", "")
    except Exception:
        host = user = pw = frm = ""
        port = 587
    if not host or not user or not pw:
        return False, "Email sending is not set up yet. Add SMTP_HOST, SMTP_USER, SMTP_PASSWORD to Secrets (not under [xai])."
    msg = MIMEText(
        f"Your Smart Slip password reset code is: {code}\n\n"
        f"It expires in 20 minutes. If you didn't ask for this, ignore this email."
    )
    msg["Subject"] = "Smart Slip password reset"
    msg["From"] = frm
    msg["To"] = to_email
    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(user, pw)
            server.send_message(msg)
        return True, "Reset code sent."
    except Exception as e:
        return False, f"Could not send email: {e}"

def start_password_reset(email: str):
    row, idx = find_user(email)
    if not row or not idx:
        return False, "If that email exists, a reset code will be sent."
    code = f"{pysecrets.randbelow(1000000):06d}"
    expires = (datetime.now() + timedelta(minutes=20)).isoformat()
    ws = get_users_ws()
    headers = ws.row_values(1)
    if "reset_code" in headers:
        ws.update_cell(idx, headers.index("reset_code") + 1, code)
    if "reset_expires" in headers:
        ws.update_cell(idx, headers.index("reset_expires") + 1, expires)
    ok, msg = send_reset_email(email.strip().lower(), code)
    if ok:
        return True, "Reset code sent to your email."
    return False, msg

def complete_password_reset(email: str, code: str, new_password: str):
    row, idx = find_user(email)
    if not row or not idx:
        return False, "Reset failed."
    if str(row.get("reset_code", "")).strip() != str(code).strip():
        return False, "Wrong reset code."
    try:
        exp = datetime.fromisoformat(str(row.get("reset_expires", "")))
        if datetime.now() > exp:
            return False, "Reset code expired. Request a new one."
    except Exception:
        return False, "Reset code expired. Request a new one."
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    salt, digest = _hash_pw(new_password)
    token = pysecrets.token_urlsafe(24)
    ws = get_users_ws()
    headers = ws.row_values(1)
    mapping = {"pw_salt": salt, "pw_hash": digest, "session_token": token, "reset_code": "", "reset_expires": ""}
    for k, v in mapping.items():
        if k in headers:
            ws.update_cell(idx, headers.index(k) + 1, v)
    return True, token

def set_logged_in(email, token, display_name, cookies=None):
    email = (email or "").strip().lower()
    st.session_state.user_email = email
    st.session_state.user_name = display_name or email
    st.session_state.is_admin = email_is_admin(email)
    st.session_state.data_loaded = False
    st.session_state.auth_persist = f"{email}|{token}"

def clear_login(cookies=None):
    email = st.session_state.get("user_email")
    if email:
        row, idx = find_user(email)
        if row and idx:
            ws = get_users_ws()
            headers = ws.row_values(1)
            if "session_token" in headers:
                ws.update_cell(idx, headers.index("session_token") + 1, "")
    for k in ["user_name", "user_email", "is_admin", "data_loaded", "runs", "car_profiles", "grok_prediction"]:
        st.session_state[k] = None if k in ["user_name", "user_email"] else (
            False if k in ["is_admin", "data_loaded"] else ([] if k in ["runs", "car_profiles"] else None)
        )
    st.session_state.auth_persist = ""
    st.session_state.auth_clear = True

# ====================== UI ======================
st.markdown(f"""
<div class="ss-brand">
  <img src="{ICON_URL}" alt="Smart Slip">
  <div>
    <h1>Smart Slip</h1>
    <p>v2.8.55 • Auto Log • Weather • Predict</p>
  </div>
</div>
""", unsafe_allow_html=True)

cookies = None
if COOKIE_AVAILABLE:
    try:
        cookies = CookieManager(key="ss_cookie_mgr")
    except Exception:
        cookies = None

def _restore_from_saved(saved):
    if not isinstance(saved, str) or "|" not in saved:
        return False
    email, token = saved.split("|", 1)
    row = user_from_token(email, token)
    if not row:
        return False
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_name = row.get("display_name") or email
    st.session_state.is_admin = email_is_admin(email)
    st.session_state.auth_persist = saved
    return True

if st.session_state.user_name is None:
    cookie_auth = ""
    try:
        cookie_auth = st.context.cookies.get("smartslip_auth", "") or ""
    except Exception:
        cookie_auth = ""
    if not cookie_auth and cookies is not None:
        try:
            cookie_auth = cookies.get("smartslip_auth") or ""
        except Exception:
            cookie_auth = ""
    if _restore_from_saved(cookie_auth):
        st.rerun()

if st.session_state.get("auth_persist") and cookies is not None:
    try:
        cookies.set("smartslip_auth", st.session_state.auth_persist, expires_at=datetime.now() + timedelta(days=30))
    except Exception:
        pass
if st.session_state.get("auth_clear") and cookies is not None:
    try:
        cookies.delete("smartslip_auth")
    except Exception:
        pass

if JS_AVAILABLE:
    persist_js = """
    (function(){
      const v = %s;
      try { localStorage.setItem('smartslip_auth', v); } catch(e) {}
      document.cookie = 'smartslip_auth=' + encodeURIComponent(v) + '; max-age=2592000; path=/; SameSite=Lax';
      return v;
    })();
    """
    clear_js = """
    (function(){
      try { localStorage.removeItem('smartslip_auth'); } catch(e) {}
      document.cookie = 'smartslip_auth=; max-age=0; path=/';
      return '';
    })();
    """
    if st.session_state.get("auth_clear"):
        st_javascript(clear_js)
        st.session_state.auth_clear = False
    elif st.session_state.get("auth_persist"):
        st_javascript(persist_js % repr(st.session_state.auth_persist))
    elif st.session_state.user_name is None:
        saved = st_javascript("localStorage.getItem('smartslip_auth') || '';")
        if saved is None and not st.session_state.get("auth_js_tried"):
            st.session_state.auth_js_tried = True
            st.caption("Signing you back in…")
            st.stop()
        if _restore_from_saved(saved):
            st.rerun()

# ---------- User / Admin Login ----------
if st.session_state.user_name is None:
    st.subheader("Sign in to Smart Slip")
    mode = st.radio("Account", ["Log in", "Create account", "Reset password"], horizontal=True)

    if mode == "Log in":
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Log in", type="primary", use_container_width=True):
            ok, token, msg = login_user(email, pw)
            if ok:
                row, _ = find_user(email)
                name = (row or {}).get("display_name") or email.split("@")[0]
                set_logged_in(email.strip().lower(), token, name, cookies)
                st.rerun()
            else:
                st.error(msg)

    elif mode == "Create account":
        email = st.text_input("Email", key="signup_email")
        name = st.text_input("Display name", placeholder="e.g. Cooper / 1258", key="signup_name")
        pw = st.text_input("Password", type="password", key="signup_pw")
        pw2 = st.text_input("Confirm password", type="password", key="signup_pw2")
        if st.button("Create account", type="primary", use_container_width=True):
            if pw != pw2:
                st.error("Passwords do not match.")
            else:
                ok, msg = create_user(email, pw, name)
                if ok:
                    set_logged_in(email.strip().lower(), msg, name.strip() or email.split("@")[0], cookies)
                    st.success("Account created.")
                    st.rerun()
                else:
                    st.error(msg)

    elif mode == "Reset password":
        email = st.text_input("Email", key="reset_email")
        if st.button("Send reset code", use_container_width=True):
            ok, msg = start_password_reset(email)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
        st.caption("Enter the code from your email, then choose a new password.")
        code = st.text_input("Reset code", key="reset_code")
        new_pw = st.text_input("New password", type="password", key="reset_new_pw")
        if st.button("Set new password", type="primary", use_container_width=True):
            ok, msg = complete_password_reset(email, code, new_pw)
            if ok:
                row, _ = find_user(email)
                name = (row or {}).get("display_name") or email.split("@")[0]
                set_logged_in(email.strip().lower(), msg, name, cookies)
                st.success("Password updated. You are signed in.")
                st.rerun()
            else:
                st.error(msg)

    st.stop()

if not st.session_state.data_loaded:
    with st.spinner("🔥 Warming up the tires..."):
        load_data_from_sheet()
process_pending_weather()

with st.sidebar:
    st.write(f"**User:** {st.session_state.user_name}")
    if st.session_state.get("user_email"):
        st.caption(st.session_state.user_email)
    if st.session_state.is_admin:
        st.success("Admin mode – viewing all data")
    st.metric("Your Runs", len(st.session_state.runs))
    if st.button("Refresh Data"):
        st.session_state.data_loaded = False
        st.rerun()

labels = ["Auto Log", "Manual Log", "Predict", "Log Book", "Settings"]
if "nav" not in st.session_state or st.session_state.nav in ["Photo", "Log", "History"]:
    st.session_state.nav = "Auto Log" if st.session_state.get("nav") in [None, "Photo", "Log", "History"] else st.session_state.nav
if st.session_state.nav == "History":
    st.session_state.nav = "Log Book"
st.session_state.nav = st.radio(
    "Section",
    labels,
    index=labels.index(st.session_state.nav) if st.session_state.nav in labels else 0,
    horizontal=True,
    label_visibility="collapsed",
    key="nav_radio",
)

user_profiles = st.session_state.get("car_profiles") or []

# ====================== PHOTO IMPORT (NEW) ======================
if st.session_state.nav == "Auto Log":
    st.subheader("Auto Log")
    st.write("Take a clear photo of your timeslip. Smart Slip will extract the data automatically.")

    user_profiles = st.session_state.car_profiles
    if user_profiles:
        profile_options = {str(p["id"]): p["name"] for p in user_profiles}
        selected_profile_id = st.selectbox("Select Car Profile", options=list(profile_options.keys()),
                                           format_func=lambda x: profile_options[x], key="photo_profile")
        selected_profile = get_profile_by_id(selected_profile_id) or {}
        default_num = str(selected_profile.get("car_number") or "")
    else:
        selected_profile_id = None
        selected_profile = {}
        default_num = ""
        st.warning("Create a Car Profile in Settings first.")

    car_number = st.text_input(
        "Car Number on the slip",
        value=default_num,
        placeholder="e.g. 1258",
        key=f"photo_car_num_{selected_profile_id or 'none'}"
    )
    uploaded = st.file_uploader("Upload timeslip photo", type=["jpg", "jpeg", "png"], key="photo_upload")

    notes = st.text_area("Additional Notes (spin / lift / brakes / deep stage / womp)", height=70, key="photo_notes")

    auto_running = bool(st.session_state.get("auto_busy"))
    cur_auto = read_job(st.session_state.get("auto_job_id"))
    if cur_auto and str(cur_auto.get("status")) == "running":
        auto_running = True
        st.session_state.auto_busy = True
    if auto_running:
        st.warning("Reading this slip now. Do not tap Extract again.")
    extract = st.button(
        "Extract with Smart Slip",
        type="primary",
        use_container_width=True,
        disabled=auto_running,
    )
    if extract and not auto_running:
        st.session_state.auto_busy = True
        if not str(car_number or "").strip():
            st.session_state.auto_busy = False
            st.error("Enter the car number before Smart Slip can read the slip.")
        elif not uploaded:
            st.session_state.auto_busy = False
            st.error("Please upload a photo first.")
        elif not get_xai_client():
            st.session_state.auto_busy = False
            st.error("Smart Slip is not connected. Add `XAI_API_KEY` to Streamlit Secrets.")
        else:
            img_bytes = prepare_slip_image(uploaded.read())
            prompt = f"""Read this drag timeslip photo. Use ONLY the side/column for car number {car_number or 'the entered car'}.

Layouts you will see:
1) Compulink: labels on the left, LEFT numbers, RIGHT numbers. Match Car # to LEFT or RIGHT.
2) Portatree / TSI / Accutime: LEFT numbers | center label | RIGHT numbers. Match Entry #, Car #, LEFT:115, RIGHT:117, etc.
3) Two stacked blocks labeled LEFT LANE and RIGHT LANE, each with its own labels.

Field map:
- DIAL / DIAL-IN -> dial
- R/T / RT / REACTION -> reaction_time
- 60' / 60FT / 60 Foot / 60 ft -> sixty_ft
- 330 / 330' / 330 Foot / 330 FT -> three_thirty_ft
- 1/8 / 1/8mi / 1/8 Mile / 1/8 ET -> eighth_et
- MPH under 1/8, or MPH 1/8 / 1/8 Mile MPH / 1/8 MPH -> eighth_mph
- 1000 / 1000FT / 1000Foot / 1000 ET -> thousand_et
- 1/4 / 1/4 ET / finish ET -> et
- MPH under 1/4, or 1/4 MPH / bottom MPH -> trap_mph
- FINISH MARGIN / MOV / FIRST -> mov
- Extra splits like ET @ 594 FT go in notes, not eighth_et.

Rules:
- NONE, blank, or missing = None. Do not write 0.
- Do not shift rows. 60' is the 60' row only.
- Compulink DIAL is often blank. R/T is usually -0.2 to 0.999. 60' is usually 1.10 to 2.20. Never put a 1.5 in R/T.
- If the slip is 1/8-mile only, leave et and trap_mph None.
- Track name from the header exactly as printed (e.g. NUMIDIA DRAGWAY). Date and time from the header.
- Output ONLY key=value lines.

date=
time=
track=
dial=
reaction_time=
sixty_ft=
three_thirty_ft=
eighth_et=
eighth_mph=
thousand_et=
et=
trap_mph=
mov=
notes=
"""
            profile_name = ""
            if selected_profile_id:
                p = get_profile_by_id(selected_profile_id)
                if p:
                    profile_name = p["name"]
            job_id = str(datetime.now().timestamp())
            ctx = {
                "user": st.session_state.get("user_email") or st.session_state.user_name,
                "profile_id": selected_profile_id,
                "profile_name": profile_name,
                "notes": notes,
            }
            write_job(job_id, ctx["user"], "auto", "running")
            st.session_state.auto_job_id = job_id
            threading.Thread(target=_auto_worker, args=(job_id, prompt, img_bytes, ctx), daemon=True).start()
            st.rerun()

    auto_job = read_job(st.session_state.get("auto_job_id"))
    if not auto_job:
        auto_job = latest_user_job(
            st.session_state.get("user_email") or st.session_state.get("user_name"),
            "auto",
        )
    if auto_job:
        stt = str(auto_job.get("status") or "")
        if stt == "running":
            wait_banner("SMART SLIP READING")
            time.sleep(2)
            st.rerun()
        elif stt == "done":
            st.session_state.auto_busy = False
            if st.session_state.get("auto_reloaded") != str(auto_job.get("id")):
                saved = (PRED_PROMPTS.get(str(auto_job.get("id"))) or {}).get("run")
                if saved:
                    runs = list(st.session_state.get("runs") or [])
                    if not any(str(x.get("id")) == str(saved.get("id")) for x in runs):
                        runs.insert(0, saved)
                        st.session_state.runs = runs
                st.session_state.auto_reloaded = str(auto_job.get("id"))
            et_s = auto_job.get("result") or ""
            extra = auto_job.get("extra") or ""
            et_line = f"ET {et_s}s" if et_s and et_s not in ["saved", "SAVED"] else "Slip read"
            track_line = extra or ""
            st.markdown(
                f"<div class='ss-ok'>READING COMPLETE<br><span>{et_line}"
                f"{(' @ ' + track_line) if track_line else ''}</span>"
                f"<span>Entered in Log Book</span></div>",
                unsafe_allow_html=True,
            )
        elif stt == "error":
            st.session_state.auto_busy = False
            st.markdown("<div class='ss-bad'>Could not read the slip</div>", unsafe_allow_html=True)
            if auto_job.get("error"):
                st.error(auto_job.get("error"))

# ====================== MANUAL LOG ======================
if st.session_state.nav == "Manual Log":
    st.subheader("Manual Log")
    if user_profiles:
        profile_options = {str(p["id"]): p["name"] for p in user_profiles}
        selected_profile_id = st.selectbox("Select Car Profile", options=list(profile_options.keys()),
                                           format_func=lambda x: profile_options[x], key="manual_profile")
        selected_profile = get_profile_by_id(selected_profile_id)
        vehicle_name = selected_profile["name"] if selected_profile else "Main Car"
    else:
        selected_profile_id = None
        vehicle_name = "Main Car"
        st.warning("Create a Car Profile in Settings first.")
    track = render_track_picker("manual")
    st.markdown("**Weather**")
    c1, c2, c3 = st.columns(3)
    with c1:
        temp_f = st.number_input("Temp °F", value=None, step=0.5, key="manual_temp")
    with c2:
        altim = st.number_input("Barometer (inHg)", value=None, step=0.01, format="%.2f", key="manual_altim")
    with c3:
        humidity = st.number_input("Humidity %", value=None, key="manual_humidity")
    wx_calc = {}
    if temp_f not in [None, ""] and altim not in [None, ""]:
        wx_calc = calculate_weather(temp_f, altim, humidity if humidity not in [None, ""] else 50, 400)
    da_in = st.number_input("Density altitude (ft)", value=None, step=1.0, key="manual_da")
    grains_in = st.number_input("Water grains", value=None, step=0.1, key="manual_grains")
    air_in = st.number_input("Air density %", value=None, step=0.01, key="manual_air")
    vapor_in = st.number_input("Vapor pressure", value=None, step=0.001, format="%.3f", key="manual_vapor")
    da = da_in if da_in not in [None, ""] else wx_calc.get("density_altitude")
    grains = grains_in if grains_in not in [None, ""] else wx_calc.get("water_grains")
    air_pct = air_in if air_in not in [None, ""] else wx_calc.get("air_density_pct")
    vapor = vapor_in if vapor_in not in [None, ""] else wx_calc.get("vapor_pressure")
    st.markdown("**Timeslip**")
    dial = st.number_input("Dial", value=None, step=0.001, format="%.3f", key="manual_dial")
    rt = st.number_input("R/T", value=None, step=0.001, format="%.3f", key="manual_rt")
    sixty = st.number_input("60'", value=None, step=0.001, format="%.3f", key="manual_sixty")
    three_thirty = st.number_input("330'", value=None, step=0.001, format="%.3f", key="manual_330")
    eighth = st.number_input("1/8 ET", value=None, step=0.001, format="%.3f", key="manual_eighth")
    eighth_mph = st.number_input("1/8 MPH", value=None, step=0.1, key="manual_eighth_mph")
    thousand_et = st.number_input("1000'", value=None, step=0.001, format="%.3f", key="manual_1000")
    et = st.number_input("1/4 ET", value=None, step=0.001, format="%.3f", key="manual_et")
    trap = st.number_input("1/4 MPH", value=None, step=0.1, key="manual_trap")
    mov = st.number_input("MOV", value=None, step=0.001, format="%.3f", key="manual_mov")
    st.caption("Notes matter for spin, lift, brakes, nitrous.")
    notes = st.text_area("Notes", height=90, key="manual_notes")
    msg = st.session_state.get("manual_save_msg")
    if msg:
        if msg[0] == "ok":
            st.success(msg[1])
        else:
            st.error(msg[1])
    if st.button("Save Run", type="primary", use_container_width=True, key="manual_save"):
        payload = {
            "profile_id": str(selected_profile_id or ""),
            "track": track,
            "dial": dial, "reaction_time": rt, "et": et,
            "sixty_ft": sixty, "three_thirty_ft": three_thirty,
            "eighth_et": eighth, "eighth_mph": eighth_mph,
            "thousand_et": thousand_et, "trap_mph": trap, "mov": mov,
            "temp_f": temp_f, "altimeter_inhg": altim, "humidity_pct": humidity,
            "density_altitude": da, "notes": notes,
        }
        fp = str(payload)
        if fp == st.session_state.get("manual_last_fp"):
            st.session_state.manual_save_msg = ("err", "That run is already saved. Change a value to save another.")
            st.error("That run is already saved. Change a value to save another.")
        else:
            new_run = {
                "id": str(datetime.now().timestamp()),
                "user": st.session_state.get("user_email") or st.session_state.user_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "time": datetime.now().strftime("%H:%M"),
                "track": track,
                "vehicle": vehicle_name,
                "profile_id": selected_profile_id,
                "dial": dial,
                "reaction_time": rt,
                "et": et,
                "sixty_ft": sixty,
                "three_thirty_ft": three_thirty,
                "eighth_et": eighth,
                "eighth_mph": eighth_mph,
                "thousand_et": thousand_et,
                "trap_mph": trap,
                "mov": mov,
                "density_altitude": da,
                "temp_f": temp_f,
                "altimeter_inhg": altim,
                "humidity_pct": humidity,
                "water_grains": grains,
                "air_density_pct": air_pct,
                "vapor_pressure": vapor,
                "notes": notes
            }
            sheet_ok = save_run_to_sheet(new_run)
            if sheet_ok:
                st.session_state.runs.append(new_run)
                st.session_state.manual_last_fp = fp
                et_s = f" ET {float(et):.3f}s" if et not in [None, ""] else ""
                st.session_state.manual_save_msg = ("ok", f"Run saved.{et_s}")
                st.success(f"Run saved.{et_s}")
            else:
                st.session_state.manual_save_msg = ("err", "Could not save this run to the Google Sheet.")
                st.error("Could not save this run to the Google Sheet.")

# ====================== PREDICT + GROK ======================
if st.session_state.nav == "Predict":
    st.subheader("Predict ET with Smart Slip")
    profiles = list(st.session_state.get("car_profiles") or [])[:2]
    if not profiles:
        st.info("Create a car profile in Settings first.")
    else:
        profile_opts = {str(p.get("id")): p.get("name") for p in profiles}
        selected_pid = st.selectbox(
            "Car",
            list(profile_opts.keys()),
            format_func=lambda i: profile_opts.get(i, i),
            key="pred_vehicle",
        )
        selected_vehicle = profile_opts.get(selected_pid, "")
        vehicle_runs = [
            r for r in st.session_state.runs
            if (
                str(r.get("profile_id") or "") == str(selected_pid)
                or r.get("vehicle") == selected_vehicle
            )
            and str(r.get("excluded") or "").lower() not in ["yes", "true", "1"]
        ]
        pred_track = render_track_picker("pred")
        prof = get_profile_by_id(selected_pid) or {}
        if len(vehicle_runs) < 2:
            st.info("Need at least 2 logged runs for this car before predicting.")
        elif st.button("Ask Smart Slip for Prediction", type="primary", use_container_width=True):
            if not get_xai_client():
                st.error("Smart Slip is not connected. Add XAI_API_KEY to Streamlit Secrets first.")
            else:
                recent = vehicle_runs[-8:]
                wx_bits = ""
                wx_err = None
                with st.spinner("Pulling weather and dialing it in..."):
                    wx = fetch_weather_for_track(pred_track) or {}
                    tinfo = find_track(pred_track) or {}
                    extra = {}
                    baro = pressure_to_inhg(wx.get("altimeter_inhg"))
                    if baro:
                        wx["altimeter_inhg"] = baro
                    if wx.get("temp_f") and wx.get("altimeter_inhg"):
                        extra = calculate_weather(
                            wx.get("temp_f"),
                            wx.get("altimeter_inhg"),
                            wx.get("humidity_pct", 50),
                            tinfo.get("elev_ft") or wx.get("elev_ft") or 400,
                        )
                        wx.update({k: v for k, v in extra.items() if v is not None})
                    loc = tinfo.get("address") or wx.get("address") or pred_track
                    if not weather_looks_sane(wx):
                        wx_bits = ""
                        wx_err = wx_err or "weather units invalid"
                    if weather_looks_sane(wx):
                        wx_bits = (
                            f"{tinfo.get('name') or pred_track} ({loc})"
                            f" | Temp {wx.get('temp_f', 'N/A')}°F"
                            f" | Humidity {wx.get('humidity_pct', 'N/A')}%"
                            f" | Barometer {wx.get('altimeter_inhg', 'N/A')} inHg"
                            f" | DA {wx.get('density_altitude') or extra.get('density_altitude') or 'N/A'} ft"
                            f" | Grains {wx.get('water_grains') or extra.get('water_grains') or 'N/A'}"
                            f" | Air density {wx.get('air_density_pct') or extra.get('air_density_pct') or 'N/A'}%"
                            f" | Vapor {wx.get('vapor_pressure') or extra.get('vapor_pressure') or 'N/A'} inHg"
                        )
                        src = wx.get("weather_source")
                        if src:
                            wx_bits += f" | {src}"
                        if tinfo.get("elev_ft"):
                            wx_bits += f" | Strip elev {tinfo.get('elev_ft')} ft"
                        if tinfo.get("lat") is not None:
                            wx_bits += f" | Pin {tinfo.get('lat')},{tinfo.get('lon')}"
                    prompt = (
                        f"You are Smart Slip. Predict the next ET for one bracket car.\n"
                        f"User: {st.session_state.user_name}\n"
                        f"Car profile: {prof.get('name') or selected_vehicle}\n"
                        f"- Car number: {prof.get('car_number') or 'N/A'}\n"
                        f"- Type: {prof.get('car_type') or 'N/A'}\n"
                        f"- Fuel: {prof.get('fuel_type') or 'N/A'}\n"
                        f"- Weight: {prof.get('weight') or 'N/A'} lbs\n"
                        f"- Tires: {prof.get('tire_size') or 'N/A'} {prof.get('tire_type') or ''}\n"
                        f"- 1st gear: {prof.get('trans_first_gear') or 'N/A'}\n"
                        f"- Rear gear: {prof.get('rear_gear') or 'N/A'}\n\n"
                    )
                    prompt += f"Track: {tinfo.get('name') or pred_track}\n"
                    prompt += f"Track location: {loc}\n"
                    if tinfo.get("elev_ft"):
                        prompt += f"Track elevation: {tinfo.get('elev_ft')} ft\n"
                    if wx_bits:
                        prompt += f"Current weather at the strip: {wx_bits}\n"
                    elif wx_err:
                        prompt += "Weather lookup failed. Predict from run history only and say weather was unavailable.\n"
                    quarter = any(r.get("et") not in [None, ""] for r in recent)
                    eighth_only = (not quarter) and any(r.get("eighth_et") not in [None, ""] for r in recent)
                    race_len = "1/4 mile" if quarter else ("1/8 mile" if eighth_only else "unknown — infer from which ETs are filled in")
                    prompt += f"Race distance for this car/session: {race_len}\n"
                    last = recent[-1] if recent else {}
                    if last.get("density_altitude") not in [None, ""] and (wx.get("density_altitude") or extra.get("density_altitude")) not in [None, ""]:
                        prompt += (
                            f"Weather change vs last logged pass: last DA {last.get('density_altitude')} ft "
                            f"at {last.get('date')} {last.get('time') or ''}; "
                            f"now DA {wx.get('density_altitude') or extra.get('density_altitude')} ft. "
                            f"Move ET using THIS car's own change with DA/grains, not a generic rule.\n"
                        )
                    prompt += "\nLogged runs for THIS car only (do not mix cars or users):\n"
                    for r in recent:
                        etv = r.get("et")
                        et_txt = f"{float(etv):.3f}s" if etv not in [None, ""] else "—"
                        line = (
                            f"- {r.get('date')} {r.get('time') or ''} @ {r.get('track') or pred_track}: "
                            f"ET {et_txt} | 60' {r.get('sixty_ft') or '—'} | 330' {r.get('three_thirty_ft') or '—'} | "
                            f"1/8 {r.get('eighth_et') or '—'} @ {r.get('eighth_mph') or '—'} | "
                            f"1000' {r.get('thousand_et') or '—'} | 1/4 {et_txt} @ {r.get('trap_mph') or '—'} | "
                            f"RT {r.get('reaction_time') if r.get('reaction_time') not in [None, ''] else '—'} | "
                            f"DA {r.get('density_altitude') or 'N/A'} | "
                            f"Temp {r.get('temp_f') or 'N/A'} | Hum {r.get('humidity_pct') or 'N/A'} | "
                            f"Baro {r.get('altimeter_inhg') or 'N/A'} | Grains {r.get('water_grains') or 'N/A'} | "
                            f"Air dens {r.get('air_density_pct') or 'N/A'} | Vapor {r.get('vapor_pressure') or 'N/A'}"
                        )
                        if r.get("notes"):
                            line += f" | Notes: {r.get('notes')}"
                        prompt += line + "\n"
                    prompt += """
Rules:
- First decide race distance: 1/4 if a 1/4 ET exists, else 1/8 if only 1/8 data exists.
- Notes matter. Read spin / lift / brakes / nitrous / deep stage / womp and WHEN they happened.
- DEEP STAGE (staged deep): slower 60' because there is less rollout. That small 60' loss usually carries the whole ET a little slower. Do not treat a deep-stage 60' as a bad leave or a spin unless notes also say spin.
- WOMP: lift off the throttle and go right back to full. Almost always at the finish. Slows the ET a little. Treat like a small late lift — use incrementals before the womp; the slowed finish is what it RAN, not the clean number.
- SPIN slows the 60' and that loss usually carries the whole run. Decide if it will spin again using time of day, sun on the track, and whether prep is going away compared with this car's other runs. If a spin looks like a one-off, estimate the clean 60' from this car's clean passes and build the ET from that.
- LIFT or BRAKES almost always happen right before the finish. 1/8-mile: lift/brakes between 330' and the 1/8. Predict from 60' and 330' only. Ignore the slowed 1/8 ET as the target.
- LIFT or BRAKES on a 1/4-mile: almost always between 1000' and the 1/4. Predict from 60', 330', 1/8, and 1000' only. Ignore the slowed 1/4 ET as the target.
- Build a CLEAN ET from the usable incrementals. The slowed finish is what it RAN, not what it CAN run. Predict the clean ET unless you have a clear reason it will lift/brake/spin again.
- Do not average in junk. A spun 60' or a lifted finish must not pull the number. Prefer the tight cluster of clean 60' and 330' (and 1/8 / 1000' on a quarter).
- Weather: compare current DA/grains/temp to the last pass. Move ET only with this car's own change, not a generic seconds-per-1000-ft rule.
- Car profile (weight, gears, tires, fuel, door vs dragster) is only to interpret the log — e.g. whether a 60' is slow for this combo, or if bias + sun makes another spin likely. Never invent an ET that contradicts clean incrementals.
- Early nitrous helps more than late. Early lift/spin hurts more than late.
- Use temp, humidity, barometer, grains, air density, vapor pressure, and DA together. Do not mix cars or users.
- Do not recommend a dial-in.

Reply in this exact short form. No numbered list. No extra paragraphs.
Predicted ET: x.xxx
Clean ET: x.xxx (only if lift/spin/brakes changed the finish)
Confidence: high/medium/low — one sentence
Why: two short sentences max.
"""
                    job_id = str(datetime.now().timestamp())
                    user = st.session_state.get("user_email") or st.session_state.user_name
                    write_job(job_id, user, "predict", "running", extra=wx_bits)
                    st.session_state.pred_job_id = job_id
                    st.session_state.pred_wx_used = wx_bits
                    threading.Thread(
                        target=_predict_worker,
                        args=(job_id, prompt, user, wx_bits),
                        daemon=True,
                    ).start()
                    st.rerun()
        pred_job = read_job(st.session_state.get("pred_job_id"))
        if not pred_job:
            pred_job = latest_user_job(st.session_state.get("user_email") or st.session_state.get("user_name"), "predict")
        if pred_job and str(pred_job.get("status")) == "running":
            wait_banner("SMART SLIP PREDICTING")
            time.sleep(2)
            st.rerun()
        if pred_job and str(pred_job.get("status")) == "done" and pred_job.get("result"):
            st.session_state.grok_prediction = pred_job.get("result")
            st.session_state.pred_et_big = extract_predicted_et(pred_job.get("result"))
            if pred_job.get("extra"):
                st.session_state.pred_wx_used = pred_job.get("extra")
            if st.session_state.get("pred_shown_id") != str(pred_job.get("id")):
                st.success("Prediction ready")
                st.session_state.pred_shown_id = str(pred_job.get("id"))
        if pred_job and str(pred_job.get("status")) == "error":
            st.error(pred_job.get("error") or "Prediction failed")
        if pred_job and str(pred_job.get("status")) == "running":
            pass
        elif st.session_state.get("pred_et_big") is not None:
            st.markdown(
                f"<div class='ss-et'><span>PREDICTED ET</span>{float(st.session_state.pred_et_big):.3f}</div>",
                unsafe_allow_html=True,
            )
        if st.session_state.get("pred_wx_used"):
            st.caption(st.session_state.pred_wx_used)
        if st.session_state.grok_prediction:
            st.markdown("### Details")
            st.write(st.session_state.grok_prediction)

# ====================== HISTORY ======================
if st.session_state.nav == "Log Book":
    st.subheader("Log Book")
    runs = list(st.session_state.runs or [])
    if not runs:
        st.info("No runs found yet.")
    else:
        profiles = st.session_state.car_profiles or []
        palette = ["#17344a", "#3b2a12"]
        color_for = {}
        for i, p in enumerate(profiles[:2]):
            color_for[str(p.get("id", ""))] = palette[i]
            color_for[str(p.get("name", ""))] = palette[i]
        extras = sorted({str(r.get("vehicle") or "") for r in runs if str(r.get("vehicle") or "") not in color_for})
        for i, name in enumerate(extras):
            color_for[name] = palette[i % 2]

        def when_label(r):
            d = str(r.get("date") or "")
            t = str(r.get("time") or "")
            if t and t not in d:
                return f"{d} {t}".strip()
            return d or "—"

        def time_only(r):
            t = str(r.get("time") or "").strip()
            return t if t else "—"

        def fmt(v, digits=None):
            if v in [None, ""]:
                return "—"
            try:
                n = float(v)
                return f"{n:.{digits}f}" if digits is not None else str(v)
            except Exception:
                return str(v)

        def clean_notes(n):
            parts = [p.strip() for p in str(n or "").split("|")]
            keep = [p for p in parts if p and not p.lower().startswith("wx:")]
            return " | ".join(keep)

        def folder_name(r):
            pid = str(r.get("profile_id") or "")
            for p in profiles:
                if str(p.get("id")) == pid:
                    return p.get("name") or str(r.get("vehicle") or "Car")
            return str(r.get("vehicle") or "Car")

        def folder_key(r):
            return (
                str(r.get("date") or "Unknown"),
                str(r.get("profile_id") or r.get("vehicle") or "car"),
                str(r.get("track") or ""),
            )

        by_folder = {}
        for r in runs:
            by_folder.setdefault(folder_key(r), []).append(r)
        folders = sorted(by_folder.keys(), key=lambda k: (k[0], k[1], k[2]), reverse=True)

        for key in folders:
            day_runs = sorted(by_folder[key], key=lambda r: str(r.get("time") or ""), reverse=True)
            day, _, track = key
            car = folder_name(day_runs[0])
            preview = " · ".join([p for p in [car, track, f"{len(day_runs)} runs"] if p])
            with st.expander(f"{day} · {preview}", expanded=False):
                grid = []
                for r0 in day_runs:
                    eighth = "—"
                    if r0.get("eighth_et") not in [None, ""]:
                        eighth = fmt(r0.get("eighth_et"), 3)
                        if r0.get("eighth_mph") not in [None, ""]:
                            eighth += f" @ {fmt(r0.get('eighth_mph'), 1)}"
                    quarter = "—"
                    if r0.get("et") not in [None, ""]:
                        quarter = fmt(r0.get("et"), 3)
                        if r0.get("trap_mph") not in [None, ""]:
                            quarter += f" @ {fmt(r0.get('trap_mph'), 1)}"
                    grid.append({
                        "Time": time_only(r0),
                        "60'": fmt(r0.get("sixty_ft"), 3),
                        "330'": fmt(r0.get("three_thirty_ft"), 3),
                        "1/8": eighth,
                        "1000'": fmt(r0.get("thousand_et"), 3),
                        "1/4": quarter,
                        "DA": fmt(r0.get("density_altitude"), 0),
                    })
                event = st.dataframe(
                    pd.DataFrame(grid),
                    hide_index=True,
                    use_container_width=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key=f"grid_{day}_{key[1]}_{key[2]}",
                )
                picked_idx = []
                try:
                    picked_idx = list(event.selection.rows)
                except Exception:
                    picked_idx = []
                r = day_runs[picked_idx[0]] if picked_idx else None
                if r:
                    extra = []
                    if r.get("dial") not in [None, ""]:
                        extra.append(f"Dial {fmt(r.get('dial'), 3)}")
                    if r.get("reaction_time") not in [None, ""]:
                        extra.append(f"R/T {fmt(r.get('reaction_time'), 3)}")
                    if r.get("mov") not in [None, ""]:
                        extra.append(f"MOV {fmt(r.get('mov'), 3)}")
                    if extra:
                        st.caption(" · ".join(extra))
                    st.write(
                        f"Temp {fmt(r.get('temp_f'), 1)}°F · "
                        f"Hum {fmt(r.get('humidity_pct'), 0)}% · "
                        f"Baro {fmt(r.get('altimeter_inhg'), 2)} · "
                        f"Grains {fmt(r.get('water_grains'), 1)} · "
                        f"Air {fmt(r.get('air_density_pct'), 2)}% · "
                        f"Vapor {fmt(r.get('vapor_pressure'), 3)}"
                    )
                    note = clean_notes(r.get("notes"))
                    edited_notes = st.text_area(
                        "Notes (spin / lift / brakes)",
                        value=note,
                        key=f"notes_{r.get('id')}",
                        height=80,
                    )
                    if st.button("Save notes", key=f"savenotes_{r.get('id')}", use_container_width=True):
                        r["notes"] = (edited_notes or "").strip()
                        for x in st.session_state.runs or []:
                            if str(x.get("id")) == str(r.get("id")):
                                x["notes"] = r["notes"]
                                break
                        ok = update_run_in_sheet(r)
                        if ok:
                            st.success("Notes saved.")
                        else:
                            st.error("Could not save notes to the sheet.")
                    excluded = str(r.get("excluded") or "").lower() in ["yes", "true", "1"]
                    if excluded:
                        st.caption("Excluded from predictions.")
                    cdel, cexc = st.columns(2)
                    with cexc:
                        label = "Include in predictions" if excluded else "Exclude from predictions"
                        if st.button(label, key=f"exc_{r.get('id')}"):
                            r["excluded"] = "" if excluded else "yes"
                            set_run_excluded(r.get("id"), not excluded)
                            st.rerun()
                    with cdel:
                        if st.button("Delete this run", key=f"delrun_{r.get('id')}"):
                            st.session_state.runs = [x for x in st.session_state.runs if str(x.get("id")) != str(r.get("id"))]
                            delete_run_from_sheet(r.get("id"))
                            st.rerun()

# ====================== SETTINGS ======================
if st.session_state.nav == "Settings":
    st.subheader("Settings & Car Profiles")
    st.write(f"Signed in as **{st.session_state.user_name}**")
    if st.button("Log out", type="primary"):
        clear_login(cookies)
        st.rerun()
    if st.session_state.get("last_sheet_error"):
        st.error(f"Sheet: {st.session_state.last_sheet_error}")
    st.markdown("### Create Car Profile")
    st.caption("You can have 2 active profiles. Delete one to add another.")
    with st.expander("New Profile", expanded=len(st.session_state.car_profiles) < 2):
        name = st.text_input("Profile Name", key="prof_name")
        st.caption("This name cannot be changed later.")
        car_number = st.text_input("Car Number", placeholder="e.g. 1258", key="prof_car_num")
        car_type = st.selectbox("Car Type", ["Dragster", "Door Car"], key="prof_type")
        defaults = DRAGSTER_DEFAULTS if car_type == "Dragster" else DOOR_CAR_DEFAULTS
        fuel = st.selectbox("Fuel Type", ["Gas", "E85", "Alcohol"],
                            index=["Gas", "E85", "Alcohol"].index(defaults["fuel_type"]), key=f"prof_fuel_{car_type}")
        weight = st.number_input("Weight (lbs)", value=defaults["weight"], step=50, key=f"prof_weight_{car_type}")
        tire_size = st.text_input("Tire Size", value=defaults["tire_size"], key=f"prof_tire_size_{car_type}")
        tire_type = st.selectbox("Tire Type", ["Radial", "Bias"],
                                 index=0 if defaults["tire_type"] == "Radial" else 1, key=f"prof_tire_type_{car_type}")
        first_gear = st.number_input("1st Gear Ratio", value=defaults["trans_first_gear"], step=0.05, format="%.2f", key=f"prof_first_{car_type}")
        rear_gear = st.number_input("Rear Gear Ratio", value=defaults["rear_gear"], step=0.05, format="%.2f", key=f"prof_rear_{car_type}")
        if st.button("Create Profile", key="create_prof"):
            if len(st.session_state.car_profiles) >= 2:
                st.error("You can only have 2 active profiles. Delete one first if you need a new one.")
            elif name.strip():
                profile = {
                    "id": str(datetime.now().timestamp()),
                    "user": st.session_state.user_name,
                    "name": name.strip(),
                    "car_number": car_number.strip(),
                    "car_type": car_type,
                    "fuel_type": fuel,
                    "weight": weight,
                    "tire_size": tire_size,
                    "tire_type": tire_type,
                    "trans_first_gear": first_gear,
                    "rear_gear": rear_gear
                }
                st.session_state.car_profiles.append(profile)
                if save_profile_to_sheet(profile):
                    st.success(f"Profile '{name}' created!")
                else:
                    st.warning("Profile created locally only.")
                st.rerun()
            else:
                st.error("Enter a name.")

    if st.session_state.car_profiles:
        st.markdown("### Your Profiles")
        for p in st.session_state.car_profiles:
            with st.expander(f"{p.get('name')} ({p.get('car_type')})"):
                pid = str(p.get("id"))
                e_num = st.text_input("Car Number", value=str(p.get("car_number") or ""), key=f"edit_num_{pid}")
                types = ["Dragster", "Door Car"]
                e_type = st.selectbox("Car Type", types, index=types.index(p.get("car_type")) if p.get("car_type") in types else 0, key=f"edit_type_{pid}")
                fuels = ["Gas", "E85", "Alcohol"]
                e_fuel = st.selectbox("Fuel Type", fuels, index=fuels.index(p.get("fuel_type")) if p.get("fuel_type") in fuels else 2, key=f"edit_fuel_{pid}")
                e_weight = st.number_input("Weight (lbs)", value=float(p.get("weight") or 0), step=50.0, key=f"edit_wt_{pid}")
                e_tire = st.text_input("Tire Size", value=str(p.get("tire_size") or ""), key=f"edit_tire_{pid}")
                ttypes = ["Radial", "Bias"]
                e_ttype = st.selectbox("Tire Type", ttypes, index=ttypes.index(p.get("tire_type")) if p.get("tire_type") in ttypes else 1, key=f"edit_ttype_{pid}")
                e_first = st.number_input("1st Gear Ratio", value=float(p.get("trans_first_gear") or 1.8), step=0.05, format="%.2f", key=f"edit_first_{pid}")
                e_rear = st.number_input("Rear Gear Ratio", value=float(p.get("rear_gear") or 4.1), step=0.05, format="%.2f", key=f"edit_rear_{pid}")
                if st.button("Save profile", key=f"save_prof_{pid}"):
                    p.update({
                        "car_number": e_num.strip(),
                        "car_type": e_type,
                        "fuel_type": e_fuel,
                        "weight": e_weight,
                        "tire_size": e_tire,
                        "tire_type": e_ttype,
                        "trans_first_gear": e_first,
                        "rear_gear": e_rear,
                    })
                    update_profile_to_sheet(p)
                    st.success("Profile saved.")
                    st.rerun()
                warn = st.checkbox(
                    f"I understand deleting {p.get('name')} will erase all stored runs for this profile",
                    key=f"del_ok_{pid}"
                )
                if st.button("Delete this profile", key=f"del_{pid}"):
                    if not warn:
                        st.error("Check the box to confirm you will lose all stored data for this profile.")
                    else:
                        delete_profile_and_runs(p)
                        st.success(f"Deleted {p.get('name')} and its runs.")
                        st.rerun()

    if st.session_state.is_admin:
        st.divider()
        st.markdown("### API Keys")
        st.markdown("""
**Required in Streamlit Secrets:**

```toml
[gcp_service_account]
# ... your Google service account ...

XAI_API_KEY = "xai-your-key-here"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "you@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "you@gmail.com"
```
""")
        try:
            secret_keys = list(st.secrets.keys())
            st.write("**Top-level keys found in Secrets:**", secret_keys)
        except Exception as e:
            st.write("Could not list secrets:", e)

        if get_xai_client():
            st.success("Grok API key detected and loaded.")
        else:
            st.warning("Grok API key not found in Secrets.")

        st.markdown("### Google Sheets Status")
        if not GSPREAD_AVAILABLE:
            st.error("`gspread` or `google-auth` missing from requirements.txt")
        else:
            if "gcp_service_account" not in st.secrets:
                st.error("No [gcp_service_account] in Secrets")
            else:
                try:
                    client = get_gspread_client()
                    if client:
                        st.success(f"Google Sheets connected: **{SHEET_NAME}**")
                    else:
                        st.error("Client creation failed")
                except Exception as e:
                    st.error(f"Sheet error: {e}")

    st.markdown("### Report a bug")
    bug = st.text_area("What happened?", placeholder="Paste the red error and what you tapped.", key="bug_text")
    if st.button("Send report", key="bug_send"):
        if not str(bug or "").strip():
            st.error("Type what went wrong first.")
        else:
            ok, msg = save_bug_report(bug)
            if ok:
                st.success("Report saved.")
            else:
                st.error(f"Could not send report: {msg}")

st.divider()
st.caption("Smart Slip v2.8.55")
