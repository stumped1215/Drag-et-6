import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import json
import base64
from datetime import datetime
from typing import Optional

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

st.set_page_config(
    page_title="Smart Slip",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================== CONFIG ======================
ADMIN_PASSWORD = "admin123"
SHEET_NAME = "SmartSlipData"
WORKSHEET_RUNS = "Runs"
WORKSHEET_PROFILES = "Profiles"

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
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
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

# ====================== HELPERS ======================
def calculate_da(temp_f, altim_inhg, humidity=50, elevation=400):
    if temp_f is None or altim_inhg is None:
        return None
    try:
        pa = (29.92 - float(altim_inhg)) * 1000 + elevation
        da = pa + 120 * (float(temp_f) - 59) + (float(humidity) / 100) * 25
        return round(da)
    except:
        return None

def fetch_weather(icao):
    try:
        url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2"
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                m = data[0]
                temp_f = round(m["temp"] * 9/5 + 32, 1) if m.get("temp") is not None else None
                altim = round(m["altim_in_hg"], 2) if m.get("altim_in_hg") is not None else None
                return {"temp_f": temp_f, "altimeter_inhg": altim, "humidity_pct": 50}
    except:
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
                               "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude", "three_thirty_ft"]:
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
                                     "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude", "three_thirty_ft"]:
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
                        "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct"]:
                if key in r and (r[key] == "" or r[key] is None):
                    r[key] = None
                elif key in r:
                    try:
                        r[key] = float(r[key])
                    except:
                        pass
            runs.append(r)
        if not st.session_state.is_admin and st.session_state.user_name:
            runs = [r for r in runs if str(r.get("user", "")).lower() == st.session_state.user_name.lower()]
        st.session_state.runs = runs

        try:
            ws_profiles = sheet.worksheet(WORKSHEET_PROFILES)
            profiles = ws_profiles.get_all_records()
        except:
            profiles = []
        if not st.session_state.is_admin and st.session_state.user_name:
            profiles = [p for p in profiles if str(p.get("user", "")).lower() == st.session_state.user_name.lower()]
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
                       "density_altitude", "temp_f", "altimeter_inhg", "humidity_pct", "notes"]
            ws.append_row(headers)
        run["user"] = st.session_state.user_name
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
        profile["user"] = st.session_state.user_name
        headers = ws.row_values(1)
        row = [profile.get(h, "") for h in headers]
        ws.append_row(row)
        return True
    except Exception as e:
        st.error(f"Failed to save profile: {e}")
        return False

# ====================== UI ======================
st.title("🏁 Smart Slip")
st.caption("v2.2.1 • Grok API + Photo Import + Smart Defaults")

# ---------- User / Admin Login ----------
if st.session_state.user_name is None:
    st.subheader("Welcome to Smart Slip")
    st.write("Enter a name or nickname so your runs stay separate from everyone else.")
    name = st.text_input("Your name / nickname", placeholder="e.g. Cooper, 1258, John")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Continue", type="primary", use_container_width=True):
            if name and name.strip():
                st.session_state.user_name = name.strip()
                st.rerun()
            else:
                st.error("Please enter a name.")
    with col2:
        admin_pw = st.text_input("Admin password (optional)", type="password")
        if st.button("Admin Login", use_container_width=True):
            if admin_pw == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.session_state.user_name = "ADMIN"
                st.rerun()
            else:
                st.error("Wrong password")
    st.stop()

if not st.session_state.data_loaded:
    with st.spinner("Loading your data..."):
        load_data_from_sheet()

with st.sidebar:
    st.write(f"**User:** {st.session_state.user_name}")
    if st.session_state.is_admin:
        st.success("Admin mode – viewing all data")
    st.metric("Your Runs", len(st.session_state.runs))
    if st.button("Refresh Data"):
        st.session_state.data_loaded = False
        st.rerun()
    if st.button("Switch User / Logout"):
        for k in ["user_name", "is_admin", "data_loaded", "runs", "car_profiles", "grok_prediction"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

tab_photo, tab_import, tab_manual, tab_predict, tab_history, tab_settings = st.tabs([
    "Photo Import", "Import from Grok", "Manual Log", "Predict + Grok", "History", "Settings"
])

# ====================== PHOTO IMPORT (NEW) ======================
with tab_photo:
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
            with st.spinner("Grok is reading the timeslip..."):
                img_bytes = uploaded.read()
                prompt = f"""Extract data from this timeslip photo. ONLY use the side for car number {car_number or 'the main car'}.

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
                            "notes": final_notes
                        }
                        st.session_state.runs.append(new_run)
                        if save_run_to_sheet(new_run):
                            st.success(f"Run saved! ET {new_run['et']:.3f}s")
                        else:
                            st.warning("Saved locally only.")
                        st.rerun()

# ====================== IMPORT FROM GROK (text) ======================
with tab_import:
    st.subheader("Import from Grok (text paste)")
    st.caption("Use this if you prefer the old copy-paste method.")
    car_number = st.text_input("Car Number", placeholder="e.g. 1258", key="text_car_num")
    st.info("Put spinning, lifting, or braking details in Notes.")
    block = st.text_area("Paste the block from Grok here:", height=150, key="import_block")
    if user_profiles:
        profile_options = {str(p["id"]): p["name"] for p in user_profiles}
        selected_profile_id = st.selectbox("Select Car Profile", options=list(profile_options.keys()),
                                           format_func=lambda x: profile_options[x], key="text_profile")
    else:
        selected_profile_id = None
    import_notes = st.text_area("Additional Notes", height=70, key="text_notes")
    if st.button("Import Run", type="primary", use_container_width=True, key="text_import_btn"):
        if not block.strip():
            st.error("Paste the block first.")
        else:
            data = parse_import_block(block)
            if "et" not in data:
                st.error("Could not find ET.")
            else:
                profile_name = ""
                if selected_profile_id:
                    p = get_profile_by_id(selected_profile_id)
                    if p:
                        profile_name = p["name"]
                final_notes = data.get("notes", "")
                if import_notes:
                    final_notes = (final_notes + " | " + import_notes).strip(" |")
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
                    "notes": final_notes
                }
                st.session_state.runs.append(new_run)
                save_run_to_sheet(new_run)
                st.success("Run imported!")
                st.rerun()

# ====================== MANUAL LOG ======================
with tab_manual:
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
    track = st.text_input("Track", value="Numidia Dragway", key="manual_track")
    st.markdown("**Weather**")
    c1, c2, c3 = st.columns(3)
    with c1:
        temp_f = st.number_input("Temp °F", value=75.0, step=0.5, key="manual_temp")
    with c2:
        altim = st.number_input("Altimeter", value=29.92, step=0.01, format="%.2f", key="manual_altim")
    with c3:
        humidity = st.number_input("Humidity %", value=50, key="manual_humidity")
    da = calculate_da(temp_f, altim, humidity)
    st.caption(f"Calculated DA: **{da} ft**")
    icao = st.text_input("Airport ICAO", value="KMDT", key="manual_icao")
    if st.button("Pull Current Weather", key="manual_pull_wx"):
        wx = fetch_weather(icao)
        if wx:
            st.success(f"Loaded weather from {icao}")
            st.write(wx)
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
                "notes": notes
            }
            st.session_state.runs.append(new_run)
            if save_run_to_sheet(new_run):
                st.success("Run saved!")
            else:
                st.warning("Saved locally only.")
            st.rerun()

# ====================== PREDICT + GROK ======================
with tab_predict:
    st.subheader("Predict ET with Grok")
    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in st.session_state.runs)))
    if not all_vehicles:
        st.info("No runs yet for your account.")
    else:
        selected_vehicle = st.selectbox("Select Vehicle", all_vehicles, key="pred_vehicle")
        vehicle_runs = [r for r in st.session_state.runs if r.get("vehicle") == selected_vehicle]
        st.markdown("**Current Weather**")
        icao = st.text_input("Airport ICAO", value="KMDT", key="pred_icao")
        if st.button("Pull Current Weather", key="pred_wx"):
            wx = fetch_weather(icao)
            if wx:
                st.session_state.pred_temp = wx.get("temp_f", 78)
                st.session_state.pred_altim = wx.get("altimeter_inhg", 29.92)
                st.success("Weather loaded")
        temp = st.number_input("Temp °F", value=st.session_state.get("pred_temp", 78.0), step=0.5, key="pred_temp_input")
        altim = st.number_input("Altimeter", value=st.session_state.get("pred_altim", 29.92), step=0.01, format="%.2f", key="pred_altim_input")
        humidity = st.number_input("Humidity %", value=50, key="pred_humidity_input")
        target_da = calculate_da(temp, altim, humidity)
        st.caption(f"**Target DA: {target_da} ft**")

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
                prompt += f"\nTarget Density Altitude: {target_da} ft\n"
                prompt += "\nGive a smart ET prediction with clear reasoning. Do not mix data from other cars or users."
                with st.spinner("Grok is thinking..."):
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
with tab_history:
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
                    "trap_mph", "density_altitude", "track", "notes"]
            available = [c for c in cols if c in df.columns]
            st.dataframe(df[available], use_container_width=True)

# ====================== SETTINGS ======================
with tab_settings:
    st.subheader("Settings & Car Profiles")
    st.markdown("### Create Car Profile")
    with st.expander("New Profile", expanded=True):
        name = st.text_input("Profile Name", key="prof_name")
        car_type = st.selectbox("Car Type", ["Dragster", "Door Car"], key="prof_type")
        # Apply defaults based on car type
        defaults = DRAGSTER_DEFAULTS if car_type == "Dragster" else DOOR_CAR_DEFAULTS
        fuel = st.selectbox("Fuel Type", ["Gas", "E85", "Alcohol"],
                            index=["Gas", "E85", "Alcohol"].index(defaults["fuel_type"]), key="prof_fuel")
        weight = st.number_input("Weight (lbs)", value=defaults["weight"], step=50, key="prof_weight")
        tire_size = st.text_input("Tire Size", value=defaults["tire_size"], key="prof_tire_size")
        tire_type = st.selectbox("Tire Type", ["Radial", "Bias"],
                                 index=0 if defaults["tire_type"] == "Radial" else 1, key="prof_tire_type")
        first_gear = st.number_input("1st Gear Ratio", value=defaults["trans_first_gear"], step=0.05, format="%.2f", key="prof_first")
        rear_gear = st.number_input("Rear Gear Ratio", value=defaults["rear_gear"], step=0.05, format="%.2f", key="prof_rear")
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
```
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
st.caption("Smart Slip v2.2.1 • Grok API + Photo Import + Smart Defaults")
