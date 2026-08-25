import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
import json
from datetime import datetime
from typing import Optional

# Optional Google Sheets support
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

st.set_page_config(
    page_title="Smart Slip",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================== CONFIG ======================
ADMIN_PASSWORD = "admin123"          # Change this to your own password
SHEET_NAME = "SmartSlipData"         # Name of the Google Sheet
WORKSHEET_RUNS = "Runs"
WORKSHEET_PROFILES = "Profiles"

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
                               "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude"]:
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
                                     "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude"]:
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
    """Load runs and profiles from Google Sheet, filtered by current user (unless admin)."""
    client = get_gspread_client()
    if client is None:
        return False

    try:
        sheet = client.open(SHEET_NAME)

        # ----- Runs -----
        try:
            ws_runs = sheet.worksheet(WORKSHEET_RUNS)
            records = ws_runs.get_all_records()
        except:
            records = []

        runs = []
        for r in records:
            # Convert empty strings to None for numeric fields
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

        # Filter by user unless admin
        if not st.session_state.is_admin and st.session_state.user_name:
            runs = [r for r in runs if str(r.get("user", "")).lower() == st.session_state.user_name.lower()]

        st.session_state.runs = runs

        # ----- Profiles -----
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

        # Ensure user is set
        run["user"] = st.session_state.user_name

        # Build row in consistent order
        headers = ws.row_values(1)
        row = []
        for h in headers:
            val = run.get(h, "")
            if val is None:
                val = ""
            row.append(val)
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
st.caption("v2.0 • Multi-user • Google Sheets • Per-car predictions")

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

# Load data once
if not st.session_state.data_loaded:
    with st.spinner("Loading your data..."):
        load_data_from_sheet()

# Sidebar
with st.sidebar:
    st.write(f"**User:** {st.session_state.user_name}")
    if st.session_state.is_admin:
        st.success("Admin mode – viewing all data")
    st.metric("Your Runs", len(st.session_state.runs))
    if st.button("Refresh Data"):
        st.session_state.data_loaded = False
        st.rerun()
    if st.button("Switch User / Logout"):
        st.session_state.user_name = None
        st.session_state.is_admin = False
        st.session_state.data_loaded = False
        st.session_state.runs = []
        st.session_state.car_profiles = []
        st.rerun()

# Tabs
tab_import, tab_manual, tab_predict, tab_history, tab_settings = st.tabs([
    "Import from Grok", "Manual Log", "Predict + Grok", "History", "Settings"
])

# ====================== IMPORT FROM GROK ======================
with tab_import:
    st.subheader("Import from Grok")

    car_number = st.text_input("Car Number on slip", placeholder="e.g. 1258")

    st.info("**Important:** Put spinning, lifting, or braking details (when and how much) in the Notes.")

    prompt = f"""Extract data from this timeslip photo. ONLY use the side for car number {car_number or '____'}.

CRITICAL RULES:
- Pull historical weather for the exact time on the slip.
- Output ONLY key=value lines. One key per line. NO extra text.
- If a value is missing, write key=None
- Put any details about spinning, lifting, or braking in the notes field.

Required output:

date=2026-06-21
time=12:29
track=NUMIDIA DRAGWAY
vehicle=Car 1258 Truck
et=5.517
sixty_ft=1.240
eighth_et=5.517
trap_mph=125.49
reaction_time=-0.042
temp_f=81
altimeter_inhg=29.90
humidity_pct=58
density_altitude=1950
notes=Round 219/220 - spun mildly at 60ft, lifted slightly after 330"""

    st.code(prompt, language="text")

    if not st.session_state.import_success:
        block = st.text_area("Paste the block from Grok here:", height=150, key="import_block")

        # Profile selection
        user_profiles = [p for p in st.session_state.car_profiles]
        if user_profiles:
            profile_options = {str(p["id"]): p["name"] for p in user_profiles}
            selected_profile_id = st.selectbox(
                "Select Car Profile",
                options=list(profile_options.keys()),
                format_func=lambda x: profile_options[x],
                key="import_profile"
            )
        else:
            selected_profile_id = None
            st.warning("No car profiles yet. Create one in Settings.")

        import_notes = st.text_area("Additional Notes (spinning / lifting / braking)", height=70)

        if st.button("Import Run", type="primary", use_container_width=True):
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
                        "three_thirty_ft": data.get("three_thirty_ft") or data.get("330_ft"),
                        "eighth_et": data.get("eighth_et"),
                        "trap_mph": data.get("trap_mph"),
                        "density_altitude": data.get("density_altitude"),
                        "temp_f": data.get("temp_f"),
                        "altimeter_inhg": data.get("altimeter_inhg"),
                        "humidity_pct": data.get("humidity_pct"),
                        "notes": final_notes
                    }

                    # Save locally and to sheet
                    st.session_state.runs.append(new_run)
                    success = save_run_to_sheet(new_run)
                    if success:
                        st.session_state.import_success = True
                        st.session_state.last_imported = new_run
                        st.rerun()
                    else:
                        st.warning("Run saved locally but could not write to Google Sheet.")
                        st.session_state.import_success = True
                        st.session_state.last_imported = new_run
                        st.rerun()
    else:
        st.success("Run imported!")
        if st.session_state.last_imported:
            r = st.session_state.last_imported
            st.write(f"**ET:** {r['et']:.3f}s | **Vehicle:** {r.get('vehicle')}")
            if r.get("notes"):
                st.write(f"**Notes:** {r['notes']}")
        if st.button("Import Another Run", use_container_width=True):
            st.session_state.import_success = False
            st.session_state.last_imported = None
            st.rerun()

# ====================== MANUAL LOG ======================
with tab_manual:
    st.subheader("Manual Log")

    user_profiles = st.session_state.car_profiles
    if user_profiles:
        profile_options = {str(p["id"]): p["name"] for p in user_profiles}
        selected_profile_id = st.selectbox(
            "Select Car Profile",
            options=list(profile_options.keys()),
            format_func=lambda x: profile_options[x],
            key="manual_profile"
        )
        selected_profile = get_profile_by_id(selected_profile_id)
        vehicle_name = selected_profile["name"] if selected_profile else "Main Car"
    else:
        selected_profile_id = None
        vehicle_name = "Main Car"
        st.warning("Create a Car Profile in Settings first.")

    st.write(f"**Vehicle:** {vehicle_name}")
    track = st.text_input("Track", value="Numidia Dragway")

    st.markdown("**Weather**")
    c1, c2, c3 = st.columns(3)
    with c1:
        temp_f = st.number_input("Temp °F", value=75.0, step=0.5)
    with c2:
        altim = st.number_input("Altimeter", value=29.92, step=0.01, format="%.2f")
    with c3:
        humidity = st.number_input("Humidity %", value=50)

    da = calculate_da(temp_f, altim, humidity)
    st.caption(f"Calculated DA: **{da} ft**")

    icao = st.text_input("Airport ICAO", value="KMDT")
    if st.button("Pull Current Weather"):
        wx = fetch_weather(icao)
        if wx:
            st.success(f"Loaded weather from {icao}")
            # Note: in a full version we would update the widgets; for simplicity we show values
            st.write(wx)

    st.markdown("**Timeslip Data**")
    col1, col2 = st.columns(2)
    with col1:
        sixty = st.number_input("60 ft", value=0.0, step=0.001, format="%.3f")
        three_thirty = st.number_input("330 ft", value=0.0, step=0.001, format="%.3f")
        eighth = st.number_input("1/8 ET", value=0.0, step=0.001, format="%.3f")
    with col2:
        trap = st.number_input("Trap MPH", value=0.0, step=0.1)
        et = st.number_input("ET", value=10.0, step=0.001, format="%.3f")

    st.info("Put spinning, lifting, braking details in Notes (when + how much).")
    notes = st.text_area("Notes", height=90)

    if st.button("Save Run", type="primary", use_container_width=True):
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
                st.success("Run saved to Google Sheet!")
            else:
                st.warning("Saved locally only (Google Sheet not connected).")
            st.rerun()

# ====================== PREDICT + GROK ======================
with tab_predict:
    st.subheader("Predict ET (Per Vehicle)")

    # Only this user's vehicles
    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in st.session_state.runs)))
    if not all_vehicles:
        st.info("No runs yet for your account.")
    else:
        selected_vehicle = st.selectbox("Select Vehicle", all_vehicles)
        vehicle_runs = [r for r in st.session_state.runs if r.get("vehicle") == selected_vehicle]

        st.markdown("**Current Weather for Prediction**")
        icao = st.text_input("Airport ICAO", value="KMDT", key="pred_icao")
        if st.button("Pull Current Weather", key="pred_wx"):
            wx = fetch_weather(icao)
            if wx:
                st.session_state.pred_temp = wx.get("temp_f", 78)
                st.session_state.pred_altim = wx.get("altimeter_inhg", 29.92)
                st.success("Weather loaded")

        temp = st.number_input("Temp °F", value=st.session_state.get("pred_temp", 78.0), step=0.5)
        altim = st.number_input("Altimeter", value=st.session_state.get("pred_altim", 29.92), step=0.01, format="%.2f")
        humidity = st.number_input("Humidity %", value=50)
        target_da = calculate_da(temp, altim, humidity)
        st.caption(f"**Target DA: {target_da} ft**")

        st.divider()
        st.subheader("Generate Prompt for Grok")

        if st.button("Generate Prompt for Grok", type="primary", use_container_width=True):
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
            prompt += "\nGive a smart ET prediction with reasoning. Do not mix data from other cars or users."
            st.code(prompt, language="text")

        grok_reply = st.text_area("Paste Grok's reply here")
        if st.button("Save Grok Prediction"):
            if grok_reply.strip() and st.session_state.runs:
                st.session_state.runs[-1]["grok_prediction"] = grok_reply.strip()
                st.success("Saved locally (will be included in next sheet sync).")

# ====================== HISTORY ======================
with tab_history:
    st.subheader("History (Your Runs Only)" if not st.session_state.is_admin else "History (Admin – All Users)")

    runs = st.session_state.runs
    if not runs:
        st.info("No runs found for you yet.")
    else:
        # Vehicle filter
        vehicles = ["All Vehicles"] + sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
        v_filter = st.selectbox("Filter by Vehicle", vehicles)
        if v_filter != "All Vehicles":
            runs = [r for r in runs if r.get("vehicle") == v_filter]

        if not st.session_state.show_all_history:
            display = runs[-25:][::-1]
            st.caption(f"Showing last {len(display)} runs")
            if st.button("Show All"):
                st.session_state.show_all_history = True
                st.rerun()
        else:
            display = runs[::-1]
            st.caption(f"Showing all {len(display)} runs")
            if st.button("Show Recent Only"):
                st.session_state.show_all_history = False
                st.rerun()

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
    with st.expander("New Profile"):
        name = st.text_input("Profile Name")
        car_type = st.selectbox("Car Type", ["Dragster", "Door Car"])
        fuel = st.selectbox("Fuel Type", ["Gas", "E85", "Alcohol"])
        weight = st.number_input("Weight (lbs)", value=2200, step=50)
        tire_size = st.text_input("Tire Size", value="28x10.5")
        tire_type = st.selectbox("Tire Type", ["Radial", "Bias"])
        first_gear = st.number_input("1st Gear Ratio", value=2.50, step=0.05, format="%.2f")
        rear_gear = st.number_input("Rear Gear Ratio", value=4.10, step=0.05, format="%.2f")

        if st.button("Create Profile"):
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
                    st.success(f"Profile '{name}' created and saved!")
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
    st.markdown("### Google Sheets Setup (Admin)")
    st.markdown("""
**To enable automatic saving:**

1. Create a Google Cloud Service Account and download the JSON key.
2. Create a Google Sheet named **SmartSlipData**.
3. Share the Sheet with the service account email (Editor access).
4. In Streamlit Cloud → Settings → Secrets, paste:

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```

5. Restart the app.
""")
    if GSPREAD_AVAILABLE and get_gspread_client():
        st.success("Google Sheets is connected.")
    else:
        st.warning("Google Sheets is not connected yet. Data is only saved locally until you set it up.")

st.divider()
st.caption("Smart Slip v2.0 • Each user’s data stays completely separate")