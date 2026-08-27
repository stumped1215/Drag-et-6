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

def rh_from_temp_dew(temp_c, dew_c):
    try:
        es = sat_vapor_pressure_hpa(temp_c)
        e = sat_vapor_pressure_hpa(dew_c)
        return max(0, min(100, round(100.0 * e / es)))
    except Exception:
        return 50

def fetch_weather(icao):
    try:
        url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                m = data[0]
                temp_c = m.get("temp")
                dew_c = m.get("dewp")
                temp_f = round(temp_c * 9/5 + 32, 1) if temp_c is not None else None
                altim = round(m["altim_in_hg"], 2) if m.get("altim_in_hg") is not None else None
                humidity = rh_from_temp_dew(temp_c, dew_c) if temp_c is not None and dew_c is not None else 50
                wx = {"temp_f": temp_f, "altimeter_inhg": altim, "humidity_pct": humidity, "icao": icao}
                extra = calculate_weather(temp_f, altim, humidity)
                wx.update(extra)
                return wx
    except Exception:
        pass
    return None

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

def call_grok(prompt: str, image_bytes: bytes = None, model: str = "grok-4"):
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
            temperature=0.3
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

def call_grok_with_search(prompt: str, model: str = "grok-4"):
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
            # Fallback: chat completions without tools
            text, err = call_grok(prompt, model=model)
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
        text, err = call_grok(prompt, model=model)
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

# ====================== GOOGLE SHEETS ======================
def get_gspread_client():
    if not GSPREAD_AVAILABLE:
        return None
    try:
        if "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"]
            )
            return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets auth error: {e}")
    return None

RUN_HEADERS = [
    "id", "user", "date", "time", "track", "vehicle", "profile_id",
    "dial", "reaction_time", "sixty_ft", "three_thirty_ft", "eighth_et",
    "eighth_mph", "thousand_et", "et", "trap_mph", "mov",
    "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct",
    "water_grains", "air_density_pct", "vapor_pressure", "notes", "excluded"
]

def _lower_row(r: dict) -> dict:
    return {str(k).strip().lower(): v for k, v in (r or {}).items()}

def _user_idents():
    return {
        str(st.session_state.get("user_email") or "").strip().lower(),
        str(st.session_state.get("user_name") or "").strip().lower(),
    } - {""}

def _row_belongs_to_user(r: dict) -> bool:
    if st.session_state.is_admin:
        return True
    ident = _user_idents()
    u = str(r.get("user") or "").strip().lower()
    if u and u in ident:
        return True
    if u and any(u == i or u.endswith(i) or i in u for i in ident):
        return True
    pid = str(r.get("profile_id") or "")
    if pid:
        for p in st.session_state.get("car_profiles") or []:
            if str(p.get("id")) == pid:
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
        if not st.session_state.is_admin:
            ident = _user_idents()
            profiles = [p for p in profiles if str(p.get("user") or "").strip().lower() in ident]
        st.session_state.car_profiles = profiles
        if not st.session_state.is_admin:
            runs = [r for r in runs if _row_belongs_to_user(r)]
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

def save_run_to_sheet(run: dict):
    client = get_gspread_client()
    if client is None:
        st.session_state.last_sheet_error = "Google Sheets client not connected."
        return False
    try:
        sheet = client.open(SHEET_NAME)
        ws = _ensure_runs_ws(sheet)
        run["user"] = (st.session_state.get("user_email") or st.session_state.get("user_name") or "").strip()
        headers = [str(h).strip() for h in ws.row_values(1)]
        row = []
        for h in headers:
            val = run.get(h, run.get(h.lower(), ""))
            if val is None:
                val = ""
            row.append(str(val))
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
    <p>v2.8.11 • Auto Log • Weather • Predict</p>
  </div>
</div>
""", unsafe_allow_html=True)

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
    if _restore_from_saved(cookie_auth):
        st.rerun()

if JS_AVAILABLE:
    persist_js = """
    (function(){
      const v = %s;
      localStorage.setItem('smartslip_auth', v);
      document.cookie = 'smartslip_auth=' + encodeURIComponent(v) + '; max-age=2592000; path=/; SameSite=Lax';
      return v;
    })();
    """
    clear_js = """
    (function(){
      localStorage.removeItem('smartslip_auth');
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

    notes = st.text_area("Additional Notes (spin / lift / brakes)", height=70, key="photo_notes")

    if st.button("Extract with Smart Slip", type="primary", use_container_width=True):
        if not str(car_number or "").strip():
            st.error("Enter the car number before Smart Slip can read the slip.")
        elif not uploaded:
            st.error("Please upload a photo first.")
        elif not get_xai_client():
            st.error("Smart Slip is not connected. Add `XAI_API_KEY` to Streamlit Secrets.")
        else:
            with st.spinner("🏁 Reading the timeslip..."):
                img_bytes = uploaded.read()
                prompt = f"""Read this Compulink timeslip photo.

Use ONLY the column for car number {car_number or 'the entered car'}.
LEFT and RIGHT are two cars. Match Car # on that side (example: 1215 is LEFT, N199 is RIGHT).

Row order on these slips is ALWAYS:
- DIAL
- R/T
- 60'     -> sixty_ft   (this is about 1.2 to 1.8 for a door car, NEVER 4+ seconds)
- 330     -> three_thirty_ft
- 1/8     -> eighth_et
- MPH     (the MPH directly under 1/8) -> eighth_mph
- 1000    -> thousand_et
- 1/4     -> et
- MPH     (the MPH directly under 1/4) -> trap_mph

Do not shift rows. 60' is not 330. 330 is not 1/8.
If a value is missing use None. Do not invent zeros.

Track name is in the header (example: NUMIDIA DRAGWAY).
date and time are at the top.

Output ONLY key=value lines:
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
                result, err = call_grok(prompt, image_bytes=img_bytes)
                if err:
                    st.error(f"Smart Slip error: {err}")
                else:
                    data = parse_import_block(result)
                    if not data:
                        st.error("Could not read the slip. Try a clearer photo.")
                    else:
                        try:
                            s = data.get("sixty_ft")
                            t330 = data.get("three_thirty_ft")
                            e8 = data.get("eighth_et")
                            if s not in [None, ""] and t330 not in [None, ""] and e8 in [None, ""] and float(s) > 2.8:
                                data["eighth_et"] = t330
                                data["three_thirty_ft"] = s
                                data["sixty_ft"] = None
                        except Exception:
                            pass
                        profile_name = ""
                        if selected_profile_id:
                            p = get_profile_by_id(selected_profile_id)
                            if p:
                                profile_name = p["name"]
                        final_notes = data.get("notes", "")
                        if notes:
                            final_notes = (final_notes + " | " + notes).strip(" |")
                        new_run = {
                            "id": str(datetime.now().timestamp()),
                            "user": st.session_state.get("user_email") or st.session_state.user_name,
                            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                            "time": data.get("time", ""),
                            "track": data.get("track", "Unknown"),
                            "vehicle": profile_name or "Main Car",
                            "profile_id": selected_profile_id,
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
                            "density_altitude": data.get("density_altitude"),
                            "temp_f": data.get("temp_f"),
                            "altimeter_inhg": data.get("altimeter_inhg"),
                            "humidity_pct": data.get("humidity_pct"),
                            "water_grains": data.get("water_grains"),
                            "air_density_pct": data.get("air_density_pct"),
                            "vapor_pressure": data.get("vapor_pressure"),
                            "notes": final_notes
                        }
                        auto_fp = str({
                            "date": new_run.get("date"),
                            "time": new_run.get("time"),
                            "et": new_run.get("et"),
                            "sixty_ft": new_run.get("sixty_ft"),
                            "profile_id": new_run.get("profile_id"),
                        })
                        if auto_fp == st.session_state.get("auto_last_fp"):
                            st.error("That slip was already saved.")
                        else:
                            sheet_ok = save_run_to_sheet(new_run)
                            st.session_state.runs.append(new_run)
                            st.session_state.auto_last_fp = auto_fp
                            try:
                                track_name = data.get("track") or "Numidia Dragway"
                                wx_text, wx_err = grok_lookup_weather(
                                    track_name, data.get("date"), data.get("time")
                                )
                                if wx_text:
                                    wx = parse_import_block(wx_text)
                                    for k in ["temp_f", "altimeter_inhg", "humidity_pct", "density_altitude",
                                              "water_grains", "air_density_pct", "vapor_pressure"]:
                                        if new_run.get(k) in [None, ""] and wx.get(k) not in [None, ""]:
                                            new_run[k] = wx[k]
                                    if new_run.get("temp_f") and new_run.get("altimeter_inhg"):
                                        extra = calculate_weather(
                                            new_run.get("temp_f"),
                                            new_run.get("altimeter_inhg"),
                                            new_run.get("humidity_pct", 50)
                                        )
                                        for k in ["density_altitude", "water_grains", "air_density_pct", "vapor_pressure"]:
                                            if not new_run.get(k) and extra.get(k) is not None:
                                                new_run[k] = extra.get(k)
                                    update_run_in_sheet(new_run)
                            except Exception:
                                pass
                            et_s = f" ET {float(new_run['et']):.3f}s" if new_run.get("et") not in [None, ""] else ""
                            if sheet_ok:
                                st.success(f"Run saved.{et_s}")
                            else:
                                st.error("Read the slip but could not save it to the Google Sheet.")

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
    track = st.text_input("Track", key="manual_track")
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
    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in st.session_state.runs)))
    if not all_vehicles:
        st.info("No runs yet for your account.")
    else:
        selected_vehicle = st.selectbox("Select Vehicle", all_vehicles, key="pred_vehicle")
        vehicle_runs = [
            r for r in st.session_state.runs
            if r.get("vehicle") == selected_vehicle
            and str(r.get("excluded") or "").lower() not in ["yes", "true", "1"]
        ]
        pred_track = st.selectbox("Drag Strip", list(TRACKS.keys()), key="pred_track")
        pred_info = TRACKS.get(pred_track, TRACKS["Other / Custom"])
        st.markdown("**Current Weather**")
        icao = st.text_input("Airport ICAO (auto from track)", value=pred_info["icao"], key="pred_icao")
        if st.button("Pull Current Weather", key="pred_wx"):
            wx = fetch_weather(icao)
            if wx:
                st.session_state.pred_temp = wx.get("temp_f", 78)
                st.session_state.pred_altim = wx.get("altimeter_inhg", 29.92)
                st.session_state.pred_hum = wx.get("humidity_pct", 50)
                st.success(f"Loaded from {icao}: {wx.get('temp_f')}°F / {wx.get('humidity_pct')}% / {wx.get('altimeter_inhg')} inHg / {wx.get('water_grains')} grains")
                st.rerun()
            else:
                st.error(f"Could not get weather for {icao}. Check the ICAO code.")
        temp = st.number_input("Temp °F", value=st.session_state.get("pred_temp", 78.0), step=0.5, key="pred_temp_input")
        altim = st.number_input("Barometer (inHg)", value=st.session_state.get("pred_altim", 29.92), step=0.01, format="%.2f", key="pred_altim_input")
        humidity = st.number_input("Humidity %", value=st.session_state.get("pred_hum", 50), key="pred_humidity_input")
        wx_calc = calculate_weather(temp, altim, humidity, pred_info["elevation"])
        target_da = wx_calc.get("density_altitude")
        target_grains = wx_calc.get("water_grains")
        target_air = wx_calc.get("air_density_pct")
        target_vapor = wx_calc.get("vapor_pressure")
        st.caption(f"**DA {target_da} ft** | **Grains {target_grains}** | **Air dens {target_air}%** | **Vapor {target_vapor} inHg**")

        if st.button("Ask Smart Slip for Prediction", type="primary", use_container_width=True):
            if not get_xai_client():
                st.error("Smart Slip is not connected. Add XAI_API_KEY to Streamlit Secrets first.")
            else:
                recent = vehicle_runs[-6:]
                prompt = f"You are helping with bracket racing predictions for {selected_vehicle} (user: {st.session_state.user_name}).\n\n"
                prompt += "Recent runs (keep cars and users completely separate):\n"
                for r in recent:
                    etv = r.get("et")
                    et_txt = f"{float(etv):.3f}s" if etv not in [None, ""] else "—"
                    prompt += f"- {r.get('date')}: ET {et_txt} @ {r.get('density_altitude', 'N/A')} ft DA"
                    if r.get("dial"): prompt += f" | dial {r.get('dial')}"
                    if r.get("reaction_time") not in [None, ""]: prompt += f" | RT {r.get('reaction_time')}"
                    if r.get("mov") not in [None, ""]: prompt += f" | MOV {r.get('mov')}"
                    if r.get("sixty_ft"): prompt += f" | 60ft: {r['sixty_ft']}"
                    if r.get("three_thirty_ft"): prompt += f" | 330ft: {r['three_thirty_ft']}"
                    if r.get("eighth_et") or r.get("eighth_mph"):
                        prompt += f" | 1/8: {r.get('eighth_et', 'N/A')} @ {r.get('eighth_mph', 'N/A')} mph"
                    if r.get("thousand_et"):
                        prompt += f" | 1000: {r.get('thousand_et')}"
                    if r.get("trap_mph"):
                        prompt += f" | trap: {r.get('trap_mph')} mph"
                    if r.get("notes"): prompt += f" | Notes: {r['notes']}"
                    prompt += "\n"
                prompt += f"\nTrack: {pred_track}\n"
                prompt += f"Target weather: Temp {temp}°F | Humidity {humidity}% | Barometer {altim} inHg | DA {target_da} ft | Water grains {target_grains} | Air density {target_air}% | Vapor pressure {target_vapor} inHg\n"
                prompt += "Use temp, humidity, barometer, and water grains together. Do not mix cars or users.\n"
                prompt += "\nGive a smart ET prediction with clear reasoning. Do not mix data from other cars or users."
                with st.spinner("🔥 Dialing it in..."):
                    result, err = call_grok(prompt)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.grok_prediction = result
                        st.success("Prediction ready")
        if st.session_state.grok_prediction:
            st.markdown("### Prediction")
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

        def day_key(r):
            return str(r.get("date") or "Unknown")

        by_day = {}
        for r in runs:
            by_day.setdefault(day_key(r), []).append(r)
        days = sorted(by_day.keys(), reverse=True)

        for day in days:
            day_runs = sorted(by_day[day], key=lambda r: str(r.get("time") or ""), reverse=True)
            names = []
            for r in day_runs:
                n = str(r.get("vehicle") or "").strip()
                if n and n not in names:
                    names.append(n)
            tracks = []
            for r in day_runs:
                t = str(r.get("track") or "").strip()
                if t and t not in tracks:
                    tracks.append(t)
            preview = " · ".join([p for p in [" / ".join(names), " / ".join(tracks), f"{len(day_runs)} runs"] if p])
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
                    key=f"grid_{day}",
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
                    if note:
                        st.write(note)
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
st.caption("Smart Slip v2.8.11")
