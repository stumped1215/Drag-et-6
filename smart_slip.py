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

if ICON_URL:
    st.markdown(f"""
<script>
(function() {{
  const url = {ICON_URL!r};
  function setIcon() {{
    let link = document.querySelector('link[rel="apple-touch-icon"]');
    if (!link) {{
      link = document.createElement('link');
      link.rel = 'apple-touch-icon';
      document.head.appendChild(link);
    }}
    link.href = url;
    let short = document.querySelector('meta[name="apple-mobile-web-app-title"]');
    if (!short) {{
      short = document.createElement('meta');
      short.name = 'apple-mobile-web-app-title';
      document.head.appendChild(short);
    }}
    short.content = 'Smart Slip';
  }}
  setIcon();
}})();
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
  #MainMenu, header, footer, .stDeployButton, [data-testid="stToolbar"],
  [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
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
SHEET_NAME = "SmartSlipData"
WORKSHEET_RUNS = "Runs"
WORKSHEET_PROFILES = "Profiles"
WORKSHEET_USERS = "Users"
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
                               "water_grains", "vapor_pressure", "sat_pressure", "air_density_pct", "air_density_lbft3"]:
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
                                     "water_grains", "vapor_pressure", "sat_pressure", "air_density_pct", "air_density_lbft3"]:
                        data[k.lower()] = float(v)
                    else:
                        data[k.lower()] = v
                except:
                    data[k.lower()] = v
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

def load_data_from_sheet():
    client = get_gspread_client()
    if client is None:
        return False
    try:
        sheet = client.open(SHEET_NAME)
        try:
            ws_runs = sheet.worksheet(WORKSHEET_RUNS)
            records = ws_runs.get_all_records()
        except:
            records = []
        runs = []
        for r in records:
            for key in ["et", "sixty_ft", "three_thirty_ft", "eighth_et", "trap_mph",
                        "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct",
                        "water_grains", "air_density_pct", "vapor_pressure"]:
                if key in r and (r[key] == "" or r[key] is None):
                    r[key] = None
                elif key in r:
                    try:
                        r[key] = float(r[key])
                    except:
                        pass
            runs.append(r)
        if not st.session_state.is_admin:
            ident = [
                str(st.session_state.get("user_email") or "").lower(),
                str(st.session_state.get("user_name") or "").lower()
            ]
            runs = [r for r in runs if str(r.get("user", "")).lower() in ident]
        st.session_state.runs = runs

        try:
            ws_profiles = sheet.worksheet(WORKSHEET_PROFILES)
            profiles = ws_profiles.get_all_records()
        except:
            profiles = []
        if not st.session_state.is_admin and st.session_state.user_name:
            ident = [
                str(st.session_state.get("user_email") or "").lower(),
                str(st.session_state.get("user_name") or "").lower()
            ]
            profiles = [p for p in profiles if str(p.get("user", "")).lower() in ident]
        st.session_state.car_profiles = profiles
        st.session_state.data_loaded = True
        return True
    except Exception as e:
        st.warning(f"Could not load from Google Sheet: {e}")
        return False

def save_run_to_sheet(run: dict):
    client = get_gspread_client()
    if client is None:
        return False
    try:
        sheet = client.open(SHEET_NAME)
        try:
            ws = sheet.worksheet(WORKSHEET_RUNS)
        except:
            ws = sheet.add_worksheet(title=WORKSHEET_RUNS, rows=1000, cols=20)
            headers = ["id", "user", "date", "track", "vehicle", "profile_id", "et",
                       "sixty_ft", "three_thirty_ft", "eighth_et", "trap_mph",
                       "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct",
                       "water_grains", "air_density_pct", "vapor_pressure", "notes"]
            ws.append_row(headers)
        run["user"] = st.session_state.get("user_email") or st.session_state.user_name
        headers = ws.row_values(1)
        row = [run.get(h, "") if run.get(h) is not None else "" for h in headers]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save run: {e}")
        return False

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
            headers = ["id", "user", "name", "car_type", "fuel_type", "weight",
                       "tire_size", "tire_type", "trans_first_gear", "rear_gear"]
            ws.append_row(headers)
        profile["user"] = st.session_state.get("user_email") or st.session_state.user_name
        headers = ws.row_values(1)
        row = [profile.get(h, "") for h in headers]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save profile: {e}")
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
                       "reset_code", "reset_expires", "created_at"])
        return ws

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
        return False, "That email already has an account."
    salt, digest = _hash_pw(password)
    token = pysecrets.token_urlsafe(24)
    ws.append_row([email, display_name.strip() or email.split("@")[0],
                   salt, digest, token, "", "", datetime.now().isoformat()])
    return True, token

def login_user(email: str, password: str):
    row, idx = find_user(email)
    if not row:
        return False, None, "No account with that email."
    if not _verify_pw(password, str(row.get("pw_salt", "")), str(row.get("pw_hash", ""))):
        return False, None, "Wrong password."
    token = pysecrets.token_urlsafe(24)
    ws = get_users_ws()
    if ws and idx:
        headers = ws.row_values(1)
        if "session_token" in headers:
            ws.update_cell(idx, headers.index("session_token") + 1, token)
    return True, token, "ok"

def user_from_token(email: str, token: str):
    row, _ = find_user(email)
    if not row:
        return None
    saved = str(row.get("session_token", ""))
    if saved and token and hmac.compare_digest(saved, token):
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
    st.session_state.user_email = email
    st.session_state.user_name = display_name or email
    st.session_state.data_loaded = False
    if cookies is not None:
        cookies.set(AUTH_COOKIE, f"{email}|{token}", expires_at=datetime.now() + timedelta(days=AUTH_DAYS))

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
    if cookies is not None:
        cookies.delete(AUTH_COOKIE)

# ====================== UI ======================
st.markdown(f"""
<div class="ss-brand">
  <img src="{ICON_URL}" alt="Smart Slip">
  <div>
    <h1>Smart Slip</h1>
    <p>v2.6.7 • Photo • Weather • Predict</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Cookie component breaks on iPhone Streamlit ("not connected to a server").
# Stay-logged-in is session-only until we use a different method.
cookies = None

# Restore session from cookie
if st.session_state.user_name is None and cookies is not None:
    raw = cookies.get(AUTH_COOKIE)
    if raw and "|" in str(raw):
        email, token = str(raw).split("|", 1)
        row = user_from_token(email, token)
        if row:
            st.session_state.user_email = email
            st.session_state.user_name = row.get("display_name") or email

# ---------- User / Admin Login ----------
if st.session_state.user_name is None:
    st.subheader("Sign in to Smart Slip")
    mode = st.radio("Account", ["Log in", "Create account", "Reset password", "Admin"], horizontal=True)

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

    else:
        admin_pw = st.text_input("Admin password", type="password", key="admin_pw")
        if st.button("Admin Login", use_container_width=True):
            if admin_pw == _admin_password():
                st.session_state.is_admin = True
                st.session_state.user_name = "ADMIN"
                st.session_state.user_email = "admin"
                st.rerun()
            else:
                st.error("Wrong password")
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
    if st.button("Log out"):
        clear_login(cookies)
        st.rerun()

if "nav" not in st.session_state:
    st.session_state.nav = "Photo"
nav_cols = st.columns(5)
labels = ["Photo", "Log", "Predict", "History", "Settings"]
for i, label in enumerate(labels):
    if nav_cols[i].button(label, use_container_width=True, key=f"nav_{label}",
                          type="primary" if st.session_state.nav == label else "secondary"):
        st.session_state.nav = label
        st.rerun()
st.divider()

# ====================== PHOTO IMPORT (NEW) ======================
if st.session_state.nav == "Photo":
    st.subheader("Upload Timeslip Photo")
    st.write("Take a clear photo of your timeslip. Grok will extract the data automatically.")

    car_number = st.text_input("Car Number on the slip", placeholder="e.g. 1258", key="photo_car_num")
    uploaded = st.file_uploader("Upload timeslip photo", type=["jpg", "jpeg", "png"], key="photo_upload")

    user_profiles = st.session_state.car_profiles
    if user_profiles:
        profile_options = {str(p["id"]): p["name"] for p in user_profiles}
        selected_profile_id = st.selectbox("Select Car Profile", options=list(profile_options.keys()),
                                           format_func=lambda x: profile_options[x], key="photo_profile")
    else:
        selected_profile_id = None
        st.warning("Create a Car Profile in Settings first.")

    notes = st.text_area("Additional Notes (spin / lift / brakes)", height=70, key="photo_notes")

    if st.button("Extract with Grok", type="primary", use_container_width=True):
        if not uploaded:
            st.error("Please upload a photo first.")
        elif not get_xai_client():
            st.error("Grok API not configured. Add `XAI_API_KEY` to Streamlit Secrets.")
        else:
            with st.spinner("🏁 Grok is reading the timeslip..."):
                img_bytes = uploaded.read()
                prompt = f"""Extract data from this timeslip photo. ONLY use the side for car number {car_number or 'the main car'}.

Identify the drag strip / track name from the slip header if shown (example: NUMIDIA DRAGWAY).

Output ONLY key=value lines, one per line. No extra text.
If a value is missing write key=None

Required fields:
date=
time=
track=
vehicle=
et=
sixty_ft=
three_thirty_ft=
eighth_et=
trap_mph=
reaction_time=
temp_f=
altimeter_inhg=
humidity_pct=
density_altitude=
water_grains=
notes=
"""
                result, err = call_grok(prompt, image_bytes=img_bytes)
                if err:
                    st.error(f"Grok error: {err}")
                else:
                    st.code(result, language="text")
                    data = parse_import_block(result)
                    if "et" not in data:
                        st.error("Could not find ET in Grok's response. Try a clearer photo.")
                    else:
                        # Look up weather for the track + time on the slip
                        track_name = data.get("track") or "Numidia Dragway"
                        with st.spinner("🌤 Grok is looking up track weather for that time..."):
                            wx_text, wx_err = grok_lookup_weather(
                                track_name, data.get("date"), data.get("time")
                            )
                        if wx_text:
                            st.caption("Weather lookup")
                            st.code(wx_text, language="text")
                            wx = parse_import_block(wx_text)
                            for k in ["temp_f", "altimeter_inhg", "humidity_pct", "density_altitude",
                                      "water_grains", "air_density_pct", "vapor_pressure"]:
                                if data.get(k) in [None, ""] and wx.get(k) not in [None, ""]:
                                    data[k] = wx[k]
                            if wx.get("weather_source"):
                                src = str(wx.get("weather_source"))
                                data["notes"] = ((data.get("notes") or "") + f" | wx:{src}").strip(" |")
                        elif wx_err:
                            st.warning(f"Weather lookup failed: {wx_err}")
                        # Recalc grains/DA if we have temp + baro + humidity
                        if data.get("temp_f") and data.get("altimeter_inhg"):
                            extra = calculate_weather(
                                data.get("temp_f"),
                                data.get("altimeter_inhg"),
                                data.get("humidity_pct", 50)
                            )
                            for k in ["density_altitude", "water_grains", "air_density_pct", "vapor_pressure"]:
                                if not data.get(k) and extra.get(k) is not None:
                                    data[k] = extra.get(k)
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
                            "user": st.session_state.user_name,
                            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                            "track": data.get("track", "Unknown"),
                            "vehicle": data.get("vehicle", profile_name or car_number or "Main Car"),
                            "profile_id": selected_profile_id,
                            "et": data["et"],
                            "sixty_ft": data.get("sixty_ft"),
                            "three_thirty_ft": data.get("three_thirty_ft"),
                            "eighth_et": data.get("eighth_et"),
                            "trap_mph": data.get("trap_mph"),
                            "density_altitude": data.get("density_altitude"),
                            "temp_f": data.get("temp_f"),
                            "altimeter_inhg": data.get("altimeter_inhg"),
                            "humidity_pct": data.get("humidity_pct"),
                            "water_grains": data.get("water_grains"),
                            "air_density_pct": data.get("air_density_pct"),
                            "vapor_pressure": data.get("vapor_pressure"),
                            "notes": final_notes
                        }
                        st.session_state.runs.append(new_run)
                        if save_run_to_sheet(new_run):
                            st.success(f"Run saved! ET {new_run['et']:.3f}s")
                        else:
                            st.warning("Saved locally only.")
                        st.rerun()

# ====================== MANUAL LOG ======================
if st.session_state.nav == "Log":
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
    st.write(f"**Vehicle:** {vehicle_name}")
    track = st.selectbox("Drag Strip", list(TRACKS.keys()), key="manual_track")
    track_info = TRACKS.get(track, TRACKS["Other / Custom"])
    default_icao = track_info["icao"]
    elevation = track_info["elevation"]
    st.markdown("**Weather**")
    icao = st.text_input("Airport ICAO (auto from track)", value=default_icao, key="manual_icao")
    cwx1, cwx2 = st.columns(2)
    with cwx1:
        pull_metar = st.button("Pull Airport Weather", key="manual_pull_wx")
    with cwx2:
        pull_grok_wx = st.button("Grok Track Weather", key="manual_grok_wx")
    if pull_metar:
        wx = fetch_weather(icao)
        if wx:
            st.session_state.manual_temp_val = wx.get("temp_f", 75.0)
            st.session_state.manual_altim_val = wx.get("altimeter_inhg", 29.92)
            st.session_state.manual_hum_val = wx.get("humidity_pct", 50)
            st.session_state.manual_grains_val = wx.get("water_grains")
            st.success(f"Airport {icao}: {wx.get('temp_f')}°F / {wx.get('humidity_pct')}% / {wx.get('altimeter_inhg')} inHg / {wx.get('water_grains')} grains")
            st.rerun()
        else:
            st.error(f"Could not get weather for {icao}.")
    if pull_grok_wx:
        with st.spinner("🌤 Grok is searching track weather..."):
            wx_text, wx_err = grok_lookup_weather(track)
        if wx_text:
            wx = parse_import_block(wx_text)
            if wx.get("temp_f"):
                st.session_state.manual_temp_val = wx.get("temp_f")
            if wx.get("altimeter_inhg"):
                st.session_state.manual_altim_val = wx.get("altimeter_inhg")
            if wx.get("humidity_pct"):
                st.session_state.manual_hum_val = wx.get("humidity_pct")
            st.success("Grok weather loaded")
            st.code(wx_text, language="text")
            st.rerun()
        else:
            st.error(wx_err or "Grok weather lookup failed")
    c1, c2, c3 = st.columns(3)
    with c1:
        temp_f = st.number_input("Temp °F", value=st.session_state.get("manual_temp_val", 75.0), step=0.5, key="manual_temp")
    with c2:
        altim = st.number_input("Barometer (inHg)", value=st.session_state.get("manual_altim_val", 29.92), step=0.01, format="%.2f", key="manual_altim")
    with c3:
        humidity = st.number_input("Humidity %", value=st.session_state.get("manual_hum_val", 50), key="manual_humidity")
    wx_calc = calculate_weather(temp_f, altim, humidity, elevation)
    da = wx_calc.get("density_altitude")
    grains = wx_calc.get("water_grains")
    air_pct = wx_calc.get("air_density_pct")
    vapor = wx_calc.get("vapor_pressure")
    st.caption(f"**DA {da} ft** | **Grains {grains}** | **Air dens {air_pct}%** | **Vapor {vapor} inHg** | Elev {elevation} ft")
    st.markdown("**Timeslip Data**")
    col1, col2 = st.columns(2)
    with col1:
        sixty = st.number_input("60 ft", value=0.0, step=0.001, format="%.3f", key="manual_sixty")
        three_thirty = st.number_input("330 ft", value=0.0, step=0.001, format="%.3f", key="manual_330")
        eighth = st.number_input("1/8 ET", value=0.0, step=0.001, format="%.3f", key="manual_eighth")
    with col2:
        trap = st.number_input("Trap MPH", value=0.0, step=0.1, key="manual_trap")
        et = st.number_input("ET", value=10.0, step=0.001, format="%.3f", key="manual_et")
    st.info("Put spinning, lifting, braking details in Notes.")
    notes = st.text_area("Notes", height=90, key="manual_notes")
    if st.button("Save Run", type="primary", use_container_width=True, key="manual_save"):
        if et <= 0:
            st.error("Enter a valid ET")
        else:
            new_run = {
                "id": str(datetime.now().timestamp()),
                "user": st.session_state.user_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "track": track,
                "vehicle": vehicle_name,
                "profile_id": selected_profile_id,
                "et": et,
                "sixty_ft": sixty if sixty > 0 else None,
                "three_thirty_ft": three_thirty if three_thirty > 0 else None,
                "eighth_et": eighth if eighth > 0 else None,
                "trap_mph": trap if trap > 0 else None,
                "density_altitude": da,
                "temp_f": temp_f,
                "altimeter_inhg": altim,
                "humidity_pct": humidity,
                "water_grains": grains,
                "air_density_pct": air_pct,
                "vapor_pressure": vapor,
                "notes": notes
            }
            st.session_state.runs.append(new_run)
            if save_run_to_sheet(new_run):
                st.success("Run saved!")
            else:
                st.warning("Saved locally only.")
            st.rerun()

# ====================== PREDICT + GROK ======================
if st.session_state.nav == "Predict":
    st.subheader("Predict ET with Grok")
    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in st.session_state.runs)))
    if not all_vehicles:
        st.info("No runs yet for your account.")
    else:
        selected_vehicle = st.selectbox("Select Vehicle", all_vehicles, key="pred_vehicle")
        vehicle_runs = [r for r in st.session_state.runs if r.get("vehicle") == selected_vehicle]
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

        if st.button("Ask Grok for Prediction", type="primary", use_container_width=True):
            if not get_xai_client():
                st.error("Add XAI_API_KEY to Streamlit Secrets first.")
            else:
                recent = vehicle_runs[-6:]
                prompt = f"You are helping with bracket racing predictions for {selected_vehicle} (user: {st.session_state.user_name}).\n\n"
                prompt += "Recent runs (keep cars and users completely separate):\n"
                for r in recent:
                    prompt += f"- {r.get('date')}: ET {r.get('et'):.3f}s @ {r.get('density_altitude', 'N/A')} ft DA"
                    if r.get("sixty_ft"): prompt += f" | 60ft: {r['sixty_ft']}"
                    if r.get("three_thirty_ft"): prompt += f" | 330ft: {r['three_thirty_ft']}"
                    if r.get("eighth_et"): prompt += f" | 1/8: {r['eighth_et']} @ {r.get('trap_mph', 'N/A')}"
                    if r.get("notes"): prompt += f" | Notes: {r['notes']}"
                    prompt += "\n"
                prompt += f"\nTrack: {pred_track}\n"
                prompt += f"Target weather: Temp {temp}°F | Humidity {humidity}% | Barometer {altim} inHg | DA {target_da} ft | Water grains {target_grains} | Air density {target_air}% | Vapor pressure {target_vapor} inHg\n"
                prompt += "Use temp, humidity, barometer, and water grains together. Do not mix cars or users.\n"
                prompt += "\nGive a smart ET prediction with clear reasoning. Do not mix data from other cars or users."
                with st.spinner("🔥 Grok is dialing it in..."):
                    result, err = call_grok(prompt)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.grok_prediction = result
                        st.success("Prediction ready")
        if st.session_state.grok_prediction:
            st.markdown("### Grok's Prediction")
            st.write(st.session_state.grok_prediction)

# ====================== HISTORY ======================
if st.session_state.nav == "History":
    st.subheader("History (Your Runs Only)" if not st.session_state.is_admin else "History (Admin – All Users)")
    runs = st.session_state.runs
    if not runs:
        st.info("No runs found yet.")
    else:
        vehicles = ["All Vehicles"] + sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
        v_filter = st.selectbox("Filter by Vehicle", vehicles, key="hist_filter")
        if v_filter != "All Vehicles":
            runs = [r for r in runs if r.get("vehicle") == v_filter]
        display = runs[-25:][::-1] if not st.session_state.show_all_history else runs[::-1]
        st.caption(f"Showing {len(display)} runs")
        if display:
            df = pd.DataFrame(display)
            cols = ["date", "user", "vehicle", "et", "sixty_ft", "three_thirty_ft", "eighth_et",
                    "trap_mph", "temp_f", "humidity_pct", "altimeter_inhg", "density_altitude",
                    "water_grains", "air_density_pct", "vapor_pressure", "track", "notes"]
            available = [c for c in cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True)

# ====================== SETTINGS ======================
if st.session_state.nav == "Settings":
    st.subheader("Settings & Car Profiles")
    st.markdown("### Create Car Profile")
    with st.expander("New Profile", expanded=True):
        name = st.text_input("Profile Name", key="prof_name")
        car_type = st.selectbox("Car Type", ["Dragster", "Door Car"], key="prof_type")
        defaults = DRAGSTER_DEFAULTS if car_type == "Dragster" else DOOR_CAR_DEFAULTS
        st.caption(f"Defaults for {car_type}: {defaults['weight']} lbs • {defaults['tire_size']} • {defaults['fuel_type']} • 1st {defaults['trans_first_gear']} • Rear {defaults['rear_gear']}")
        fuel = st.selectbox("Fuel Type", ["Gas", "E85", "Alcohol"],
                            index=["Gas", "E85", "Alcohol"].index(defaults["fuel_type"]), key=f"prof_fuel_{car_type}")
        weight = st.number_input("Weight (lbs)", value=defaults["weight"], step=50, key=f"prof_weight_{car_type}")
        tire_size = st.text_input("Tire Size", value=defaults["tire_size"], key=f"prof_tire_size_{car_type}")
        tire_type = st.selectbox("Tire Type", ["Radial", "Bias"],
                                 index=0 if defaults["tire_type"] == "Radial" else 1, key=f"prof_tire_type_{car_type}")
        first_gear = st.number_input("1st Gear Ratio", value=defaults["trans_first_gear"], step=0.05, format="%.2f", key=f"prof_first_{car_type}")
        rear_gear = st.number_input("Rear Gear Ratio", value=defaults["rear_gear"], step=0.05, format="%.2f", key=f"prof_rear_{car_type}")
        if st.button("Create Profile", key="create_prof"):
            if name.strip():
                profile = {
                    "id": str(datetime.now().timestamp()),
                    "user": st.session_state.user_name,
                    "name": name.strip(),
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
                st.write(f"Fuel: {p.get('fuel_type')} | Weight: {p.get('weight')} lbs")
                st.write(f"Tire: {p.get('tire_size')} {p.get('tire_type')}")
                st.write(f"1st: {p.get('trans_first_gear')} | Rear: {p.get('rear_gear')}")

    st.divider()
    st.markdown("### API Keys")
    st.markdown("""
**Required in Streamlit Secrets:**

```toml
[gcp_service_account]
# ... your Google service account ...

XAI_API_KEY = "xai-your-key-here"
ADMIN_PASSWORD = "change-me"

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "you@gmail.com"
SMTP_PASSWORD = "your-app-password"
SMTP_FROM = "you@gmail.com"
```

Also add `extra-streamlit-components` to requirements.txt so login stays saved on the phone.
""")
    # Debug: show what top-level keys exist in secrets (not values)
    try:
        secret_keys = list(st.secrets.keys())
        st.write("**Top-level keys found in Secrets:**", secret_keys)
    except Exception as e:
        st.write("Could not list secrets:", e)

    if get_xai_client():
        st.success("Grok API key detected and loaded.")
    else:
        st.warning("Grok API key not found in Secrets.")
        st.info("Make sure the line `XAI_API_KEY = \"xai-...\"` is **outside** the [gcp_service_account] section, then Save + Reboot.")

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
                    sheet = client.open(SHEET_NAME)
                    st.success(f"Google Sheets connected: **{SHEET_NAME}**")
                else:
                    st.error("Client creation failed")
            except Exception as e:
                st.error(f"Sheet error: {e}")

st.divider()
st.caption("Smart Slip v2.6.7")
