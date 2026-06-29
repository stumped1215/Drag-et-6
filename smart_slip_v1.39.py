import streamlit as st
import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime

st.set_page_config(
    page_title="Smart Slip",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============== SESSION STATE ==============
if "runs" not in st.session_state:
    st.session_state.runs = []
if "import_success" not in st.session_state:
    st.session_state.import_success = False
if "last_imported" not in st.session_state:
    st.session_state.last_imported = None
if "show_all_history" not in st.session_state:
    st.session_state.show_all_history = False
if "car_profiles" not in st.session_state:
    st.session_state.car_profiles = []

runs = st.session_state.runs
car_profiles = st.session_state.car_profiles

def save_runs():
    st.session_state.runs = runs

def save_profiles():
    st.session_state.car_profiles = car_profiles

def calculate_da(temp_f, altim_inhg, humidity=50, elevation=400):
    if temp_f is None or altim_inhg is None:
        return None
    pa = (29.92 - altim_inhg) * 1000 + elevation
    da = pa + 120 * (temp_f - 59) + (humidity / 100) * 25
    return round(da)

def calculate_model(runs, track_filter=None):
    if track_filter:
        valid = [r for r in runs if r.get("density_altitude") and r.get("et") and r.get("track") == track_filter]
    else:
        valid = [r for r in runs if r.get("density_altitude") and r.get("et")]
    
    if len(valid) < 3:
        return None
    X = np.array([r["density_altitude"] for r in valid])
    y = np.array([r["et"] for r in valid])
    slope, intercept = np.polyfit(X, y, 1)
    y_pred = slope * X + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    return {
        "r2": round(r2, 3),
        "sensitivity": round(abs(slope) * 1000, 4),
        "runs_used": len(valid),
        "track": track_filter
    }

def fetch_weather(icao):
    try:
        url = f"https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and len(data) > 0:
                m = data[0]
                temp_f = round(m["temp"] * 9/5 + 32, 1) if m.get("temp") else None
                altim = round(m["altim_in_hg"], 2) if m.get("altim_in_hg") else None
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
            if v.lower() in ["none", "null", ""]: continue
            try:
                if k.lower() in ["et", "sixty_ft", "eighth_et", "trap_mph", "reaction_time", 
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
                if v.lower() in ["none", "null", ""]: continue
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
    for p in car_profiles:
        if p["id"] == profile_id:
            return p
    return None

# ============== UI ==============
st.title("🏁 Smart Slip")
st.caption("v1.39 • Import CSV Added")

runs = st.session_state.runs

with st.sidebar:
    st.header("Quick Stats")
    st.metric("Total Runs", len(runs))
    if runs:
        valid_ets = [r['et'] for r in runs if r.get('et') is not None]
        if valid_ets:
            st.metric("Best ET", f"{min(valid_ets):.3f}s")
    model = calculate_model(runs)
    if model:
        st.metric("R²", model["r2"])

    st.divider()
    
    # Export CSV
    if st.button("Export CSV"):
        if runs:
            df = pd.DataFrame(runs)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, f"smart_slip_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.warning("No data to export.")

tab_import, tab_manual, tab_predict, tab_history, tab_settings = st.tabs([
    "Import from Grok", "Manual Log", "Predict + Grok", "History", "Settings"
])

# IMPORT FROM GROK
with tab_import:
    st.subheader("Import from Grok")

    car_number = st.text_input("Car Number", placeholder="e.g. 1258")

    st.markdown("**How to import a timeslip:**")
    st.markdown("1. Take a clear photo of your timeslip")
    st.markdown("2. Come back to this chat with Grok")
    st.markdown("3. Send the photo + the prompt below")
    st.markdown("4. Paste the block Grok gives you here")

    st.info("**Important:** Put details about spinning, lifting, or braking (when and how bad) in the **Notes** section.")

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
        block = st.text_area("Paste the block from Grok here:", height=160, key="import_block")

        if car_profiles:
            profile_options = {p["id"]: p["name"] for p in car_profiles}
            import_profile_id = st.selectbox(
                "Select Car Profile",
                options=list(profile_options.keys()),
                format_func=lambda x: profile_options[x],
                key="import_profile_select"
            )
        else:
            import_profile_id = None

        import_notes = st.text_area("Additional Notes (very important - include spinning, lifting, braking details here)", height=80, key="import_notes")

        if st.button("Import Run", type="primary", use_container_width=True):
            if not block or not block.strip():
                st.error("Please paste the block first.")
            else:
                data = parse_import_block(block)

                if "et" not in data:
                    st.error("Could not find ET in the block.")
                else:
                    final_notes = data.get("notes", "")
                    if import_notes:
                        final_notes = (final_notes + " | " + import_notes).strip(" |")
                    
                    profile_name = ""
                    if import_profile_id:
                        profile = get_profile_by_id(import_profile_id)
                        if profile:
                            profile_name = profile["name"]
                    
                    new_run = {
                        "id": datetime.now().timestamp(),
                        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        "track": data.get("track", "Unknown"),
                        "vehicle": data.get("vehicle", car_number or profile_name or "Main Car"),
                        "profile_id": import_profile_id,
                        "et": data["et"],
                        "sixty_ft": data.get("sixty_ft"),
                        "eighth_et": data.get("eighth_et"),
                        "trap_mph": data.get("trap_mph"),
                        "reaction_time": data.get("reaction_time"),
                        "density_altitude": data.get("density_altitude"),
                        "temp_f": data.get("temp_f"),
                        "altimeter_inhg": data.get("altimeter_inhg"),
                        "humidity_pct": data.get("humidity_pct"),
                        "notes": final_notes
                    }
                    runs.append(new_run)
                    save_runs()
                    st.session_state.import_success = True
                    st.session_state.last_imported = new_run
                    st.rerun()
    else:
        st.success("Run imported successfully!")
        if st.session_state.last_imported:
            r = st.session_state.last_imported
            st.write(f"**ET:** {r['et']:.3f}s")
            if r.get("notes"):
                st.write(f"**Notes:** {r['notes']}")
        if st.button("Import Another Run", use_container_width=True):
            st.session_state.import_success = False
            st.session_state.last_imported = None
            st.rerun()

# MANUAL LOG
with tab_manual:
    st.subheader("Manual Log")
    
    last_run = runs[-1] if runs else {}
    
    if car_profiles:
        profile_options = {p["id"]: p["name"] for p in car_profiles}
        manual_profile_id = st.selectbox(
            "Select Car Profile",
            options=list(profile_options.keys()),
            format_func=lambda x: profile_options[x],
            key="manual_profile_select"
        )
        selected_profile = get_profile_by_id(manual_profile_id)
        vehicle_name = selected_profile["name"] if selected_profile else "Main Car"
    else:
        manual_profile_id = None
        selected_profile = None
        vehicle_name = "Main Car"

    st.write(f"**Vehicle:** {vehicle_name}")
    track = st.text_input("Track", value=last_run.get("track", "Numidia Dragway"))
    
    st.markdown("**Weather**")
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1: temp_f = st.number_input("Temp °F", value=last_run.get("temp_f", 75.0), step=0.5)
    with col_w2: altim = st.number_input("Altimeter", value=last_run.get("altimeter_inhg", 29.92), step=0.01, format="%.2f")
    with col_w3: humidity = st.number_input("Humidity %", value=last_run.get("humidity_pct", 50))
    
    da = calculate_da(temp_f, altim, humidity)
    st.caption(f"Calculated DA: **{da} ft**")
    
    col_icao, col_fetch = st.columns([3, 1])
    with col_icao: icao = st.text_input("Airport ICAO", value="KMDT")
    with col_fetch:
        if st.button("Fetch Weather"):
            wx = fetch_weather(icao)
            if wx: st.success(f"Weather loaded from {icao}")

    st.markdown("**All Time Slip Increments**")
    col1, col2 = st.columns(2)
    with col1:
        sixty = st.number_input("60 ft", value=0.0, step=0.001, format="%.3f")
        three_thirty = st.number_input("330 ft", value=0.0, step=0.001, format="%.3f")
        eighth = st.number_input("1/8 ET", value=0.0, step=0.001, format="%.3f")
    with col2:
        trap = st.number_input("Trap MPH", value=0.0, step=0.1)
        et = st.number_input("ET", value=10.0, step=0.001, format="%.3f")

    st.info("**Important:** Use the Notes section below to record spinning, lifting, or braking (when it happened and how bad).")

    notes = st.text_area("Notes (include spinning, lifting, braking details here)", height=100)

    if st.button("Save Run", type="primary", use_container_width=True):
        if et <= 0:
            st.error("Enter a valid ET")
        else:
            new_run = {
                "id": datetime.now().timestamp(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "track": track,
                "vehicle": vehicle_name,
                "profile_id": manual_profile_id,
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
            runs.append(new_run)
            save_runs()
            st.success("Run saved!")
            st.rerun()

# PREDICT + GROK
with tab_predict:
    st.subheader("Predict ET (Ask Grok)")

    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
    if all_vehicles:
        selected_vehicle = st.selectbox("Select Vehicle", all_vehicles, index=0)
        vehicle_runs = [r for r in runs if r.get("vehicle") == selected_vehicle]
    else:
        selected_vehicle = "Main Car"
        vehicle_runs = []

    st.markdown("**Current Weather**")
    col_icao, col_fetch = st.columns([3, 1])
    with col_icao: pred_icao = st.text_input("Airport ICAO", value="KMDT", key="pred_icao")
    with col_fetch:
        if st.button("Pull Current Weather", key="pull_weather_btn"):
            wx = fetch_weather(pred_icao)
            if wx:
                st.session_state.pred_temp = wx["temp_f"]
                st.session_state.pred_altim = wx["altimeter_inhg"]
                st.session_state.pred_hum = wx.get("humidity_pct", 50)
                st.success(f"Weather loaded from {pred_icao}")

    default_temp = st.session_state.get("pred_temp", 78.0)
    default_altim = st.session_state.get("pred_altim", 29.92)
    default_hum = st.session_state.get("pred_hum", 50)

    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1: target_temp = st.number_input("Temp °F", value=default_temp, step=0.5, key="target_temp")
    with col_t2: target_altim = st.number_input("Altimeter", value=default_altim, step=0.01, format="%.2f", key="target_altim")
    with col_t3: target_hum = st.number_input("Humidity %", value=default_hum, step=1, key="target_hum")

    target_da = calculate_da(target_temp, target_altim, target_hum)
    st.caption(f"**Target Density Altitude: {target_da} ft**")

    st.divider()
    st.subheader("Ask Grok (Full Context + Profile)")

    if st.button("Generate Prompt for Grok", use_container_width=True):
        if vehicle_runs:
            recent = vehicle_runs[-6:]
            prompt = f"You are helping with bracket racing predictions for {selected_vehicle}.\n\n"
            
            latest_profile_id = recent[0].get("profile_id") if recent else None
            if latest_profile_id:
                profile = get_profile_by_id(latest_profile_id)
                if profile:
                    prompt += "Car Profile:\n"
                    prompt += f"- {profile['name']} ({profile['car_type']}, {profile['fuel_type']})\n"
                    prompt += f"- Weight: {profile['weight']} lbs | Tire: {profile['tire_size']} {profile['tire_type']}\n"
                    prompt += f"- 1st Gear: {profile['trans_first_gear']} | Rear Gear: {profile['rear_gear']}\n\n"
            
            prompt += "Recent runs:\n"
            for r in recent:
                prompt += f"- {r['date']}: ET {r['et']:.3f}s @ {r.get('density_altitude', 'N/A')} ft DA"
                if r.get("sixty_ft"): prompt += f" | 60ft: {r['sixty_ft']}"
                if r.get("three_thirty_ft"): prompt += f" | 330ft: {r['three_thirty_ft']}"
                if r.get("eighth_et"): prompt += f" | 1/8: {r['eighth_et']} @ {r.get('trap_mph', 'N/A')}"
                if r.get("notes"): prompt += f" | Notes: {r['notes']}"
                prompt += "\n"
            prompt += f"\nTarget Density Altitude: {target_da} ft\n"
            prompt += "\nPlease give a smart ET prediction with reasoning."
            st.code(prompt, language="text")

    grok_reply = st.text_area("Paste Grok's reply")
    if st.button("Save Grok Prediction", use_container_width=True):
        if grok_reply.strip() and runs:
            runs[-1]["grok_prediction"] = grok_reply.strip()
            save_runs()
            st.success("Saved!")

# HISTORY
with tab_history:
    st.subheader("History")
    
    if not runs:
        st.info("No runs yet.")
    else:
        all_vehicles = ["All Vehicles"] + sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
        selected_filter = st.selectbox("Filter by Vehicle", all_vehicles)
        
        filtered_runs = runs
        if selected_filter != "All Vehicles":
            filtered_runs = [r for r in runs if r.get("vehicle") == selected_filter]
        
        if not st.session_state.show_all_history:
            display_runs = filtered_runs[-20:][::-1]
            st.caption(f"Showing last {len(display_runs)} runs")
            if st.button("Show All Runs"):
                st.session_state.show_all_history = True
                st.rerun()
        else:
            display_runs = filtered_runs[::-1]
            st.caption(f"Showing all {len(display_runs)} runs")
            if st.button("Show Recent Only"):
                st.session_state.show_all_history = False
                st.rerun()

        if display_runs:
            df = pd.DataFrame(display_runs)
            editable_cols = ["notes"]
            display_cols = ["date", "vehicle", "et", "sixty_ft", "three_thirty_ft", "eighth_et", "trap_mph", 
                           "density_altitude", "track", "notes"]
            available_cols = [c for c in display_cols if c in df.columns]
            
            edited_df = st.data_editor(
                df[available_cols],
                use_container_width=True,
                num_rows="fixed",
                disabled=[col for col in available_cols if col not in editable_cols],
                key="history_editor_v11"
            )
            
            if not edited_df.equals(df[available_cols]):
                for idx, row in edited_df.iterrows():
                    original_idx = df.index[idx]
                    for col in editable_cols:
                        if col in row:
                            runs[original_idx][col] = row[col]
                save_runs()
                st.success("Changes saved!")
                st.rerun()
        else:
            st.info("No runs for this vehicle.")

# SETTINGS (with Import CSV)
with tab_settings:
    st.subheader("Settings")

    # === IMPORT CSV ===
    st.subheader("Import from CSV")
    st.markdown("""
    **How to restore your data:**
    1. Export your data using the **Export CSV** button in the sidebar.
    2. Save the file somewhere safe.
    3. Later, upload that same CSV file here to restore your runs.
    """)

    uploaded_file = st.file_uploader("Upload your Smart Slip CSV file", type=["csv"], key="csv_import")

    if uploaded_file is not None:
        try:
            df_import = pd.read_csv(uploaded_file)
            
            # Convert DataFrame back to list of dicts
            imported_runs = df_import.to_dict('records')
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Add to Existing Data"):
                    runs.extend(imported_runs)
                    save_runs()
                    st.success(f"Successfully imported {len(imported_runs)} runs!")
                    st.rerun()
            
            with col2:
                if st.button("Replace All Data (Warning: Deletes current data)"):
                    st.session_state.runs = imported_runs
                    save_runs()
                    st.success(f"Replaced all data with {len(imported_runs)} runs from CSV!")
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error reading CSV file: {str(e)}")

    st.divider()

    # Car Profiles
    st.subheader("Car Profiles")

    with st.expander("Create New Car Profile"):
        new_name = st.text_input("Profile Name", key="new_profile_name")
        new_car_type = st.selectbox("Car Type", ["Dragster", "Door Car"], key="new_car_type")
        new_fuel_type = st.selectbox("Fuel Type", ["Gas", "E85", "Alcohol"], key="new_fuel_type")
        new_weight = st.number_input("Weight (lbs)", value=2200, step=50, key="new_weight")
        new_tire_size = st.text_input("Tire Size (e.g. 28x10.5)", key="new_tire_size")
        new_tire_type = st.selectbox("Tire Type", ["Radial", "Bias"], key="new_tire_type")
        new_trans_first = st.number_input("Transmission 1st Gear Ratio", value=2.5, step=0.1, format="%.2f", key="new_trans_first")
        new_rear_gear = st.number_input("Rear Gear Ratio", value=4.10, step=0.05, format="%.2f", key="new_rear_gear")

        if st.button("Create Profile"):
            if new_name.strip():
                new_profile = {
                    "id": datetime.now().timestamp(),
                    "name": new_name.strip(),
                    "car_type": new_car_type,
                    "fuel_type": new_fuel_type,
                    "weight": new_weight,
                    "tire_size": new_tire_size,
                    "tire_type": new_tire_type,
                    "trans_first_gear": new_trans_first,
                    "rear_gear": new_rear_gear
                }
                car_profiles.append(new_profile)
                save_profiles()
                st.success(f"Profile '{new_name}' created!")
                st.rerun()
            else:
                st.error("Please enter a profile name.")

    if car_profiles:
        st.markdown("**Existing Profiles**")
        for profile in car_profiles:
            with st.expander(f"{profile['name']} ({profile['car_type']})"):
                st.write(f"**Fuel:** {profile['fuel_type']}")
                st.write(f"**Weight:** {profile['weight']} lbs")
                st.write(f"**Tire Size:** {profile['tire_size']}")
                st.write(f"**Tire Type:** {profile['tire_type']}")
                st.write(f"**1st Gear:** {profile['trans_first_gear']}")
                st.write(f"**Rear Gear:** {profile['rear_gear']}")
                
                if st.button("Delete Profile", key=f"delete_{profile['id']}"):
                    car_profiles.remove(profile)
                    save_profiles()
                    st.rerun()
    else:
        st.info("No car profiles yet. Create one above.")

    st.caption("v1.39 • Import CSV Added")

st.divider()
st.caption("Smart Slip v1.39 • Built for bracket racers")