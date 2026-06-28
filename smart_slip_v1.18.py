import streamlit as st
import pandas as pd
import numpy as np
import requests
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
if "show_quick_log" not in st.session_state:
    st.session_state.show_quick_log = False
if "show_all_history" not in st.session_state:
    st.session_state.show_all_history = False

runs = st.session_state.runs

def save_runs():
    st.session_state.runs = runs

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

def calculate_clean_et(et, conditions):
    adjustment = 0.0
    if conditions.get("sprayed_before_330") or conditions.get("sprayed_after_330"):
        adjustment -= 0.08
    
    severity_multipliers = {"mild": 0.6, "moderate": 1.0, "severe": 1.5}
    
    if conditions.get("spin"):
        sev = conditions.get("spin_severity", "moderate")
        adjustment += 0.06 * severity_multipliers.get(sev, 1.0)
    
    if conditions.get("lift_before_330"):
        sev = conditions.get("lift_severity", "moderate")
        adjustment += 0.08 * severity_multipliers.get(sev, 1.0)
    
    if conditions.get("lift_after_330"):
        sev = conditions.get("lift_severity", "moderate")
        adjustment += 0.05 * severity_multipliers.get(sev, 1.0)
    
    if conditions.get("brakes_after_330"):
        adjustment += 0.04
    
    return round(et + adjustment, 3)

# ============== UI ==============
st.title("🏁 Smart Slip")
st.caption("v1.18 • Mobile Optimized")

runs = st.session_state.runs

with st.sidebar:
    st.header("Quick Stats")
    st.metric("Runs", len(runs))
    if runs:
        valid_ets = [r['et'] for r in runs if r.get('et') is not None]
        if valid_ets:
            st.metric("Best ET", f"{min(valid_ets):.3f}s")
    model = calculate_model(runs)
    if model:
        st.metric("R²", model["r2"])

    st.divider()
    if st.button("Export CSV"):
        if runs:
            df = pd.DataFrame(runs)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download", csv, f"smart_slip_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# Tabs with mobile-friendly names
tab_dashboard, tab_import, tab_manual, tab_predict, tab_history, tab_settings = st.tabs([
    "🏠", "📥", "✍️", "🔮", "📜", "⚙️"
])

# DASHBOARD
with tab_dashboard:
    st.subheader("Overview")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Runs", len(runs))
    with col2:
        valid_ets = [r['et'] for r in runs if r.get('et') is not None]
        if valid_ets:
            st.metric("Best ET", f"{min(valid_ets):.3f}s")

    if model:
        st.success(f"Model active ({model['runs_used']} runs)")
    else:
        st.info("Log 5+ runs with weather to activate predictions.")

    st.divider()
    
    if st.button("⚡ Quick Log", use_container_width=True):
        st.session_state.show_quick_log = True
        st.rerun()

# Quick Log
if st.session_state.get("show_quick_log", False):
    st.subheader("Quick Log")
    with st.form("quick_log"):
        q_vehicle = st.text_input("Vehicle", value="Main Bracket Car")
        q_et = st.number_input("ET", value=10.0, step=0.001, format="%.3f")
        q_notes = st.text_area("Notes", height=50)
        if st.form_submit_button("Save", use_container_width=True):
            if q_et > 0:
                new_run = {
                    "id": datetime.now().timestamp(),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "vehicle": q_vehicle,
                    "et": q_et,
                    "notes": q_notes
                }
                runs.append(new_run)
                save_runs()
                st.success("Saved!")
                st.session_state.show_quick_log = False
                st.rerun()

# IMPORT FROM GROK
with tab_import:
    st.subheader("Import from Grok")

    car_number = st.text_input("Car Number", placeholder="e.g. 1258")

    st.markdown("**Steps:** 1. Take photo → 2. Send to Grok with prompt below → 3. Paste block")

    prompt = f"""Car number: {car_number or '____'}. Extract data from the correct side of the slip.

Format as key=value lines:
date, time, track, vehicle, et, sixty_ft, eighth_et, trap_mph, reaction_time, temp_f, altimeter_inhg, humidity_pct, density_altitude, notes"""

    st.code(prompt, language="text")

    if not st.session_state.import_success:
        block = st.text_area("Paste block from Grok", height=140, key="import_block")

        st.markdown("**Special Conditions:**")
        spin = st.checkbox("Spin", key="import_spin")
        lift_before = st.checkbox("Lift before 330'", key="import_lift_before")
        lift_after = st.checkbox("Lift after 330'", key="import_lift_after")
        brakes_after = st.checkbox("Brakes after 330'", key="import_brakes")
        sprayed_before = st.checkbox("Sprayed nitrous before 330'", key="import_sprayed_before")
        sprayed_after = st.checkbox("Sprayed nitrous after 330'", key="import_sprayed_after")

        if st.button("Import Run", type="primary", use_container_width=True):
            if not block or not block.strip():
                st.error("Paste the block first.")
            else:
                data = {}
                for line in block.strip().split("\n"):
                    if "=" in line:
                        k, v = [x.strip() for x in line.split("=", 1)]
                        if v.lower() not in ["none", "null", ""]:
                            try:
                                if k.lower() in ["et", "sixty_ft", "eighth_et", "trap_mph", "reaction_time", "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude"]:
                                    data[k.lower()] = float(v)
                                else:
                                    data[k.lower()] = v
                            except:
                                data[k.lower()] = v

                if "et" not in data:
                    st.error("Could not find ET.")
                else:
                    conditions = {
                        "spin": spin, "lift_before_330": lift_before, "lift_after_330": lift_after,
                        "brakes_after_330": brakes_after, "sprayed_before_330": sprayed_before, "sprayed_after_330": sprayed_after
                    }
                    clean_et = calculate_clean_et(data["et"], conditions)
                    
                    new_run = {
                        "id": datetime.now().timestamp(),
                        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        "track": data.get("track", "Unknown"),
                        "vehicle": data.get("vehicle", car_number or "Main Car"),
                        "et": data["et"],
                        "sixty_ft": data.get("sixty_ft"),
                        "eighth_et": data.get("eighth_et"),
                        "trap_mph": data.get("trap_mph"),
                        "reaction_time": data.get("reaction_time"),
                        "density_altitude": data.get("density_altitude"),
                        "temp_f": data.get("temp_f"),
                        "altimeter_inhg": data.get("altimeter_inhg"),
                        "humidity_pct": data.get("humidity_pct"),
                        "notes": data.get("notes", ""),
                        "clean_et_estimate": clean_et,
                        **conditions
                    }
                    runs.append(new_run)
                    save_runs()
                    st.session_state.import_success = True
                    st.session_state.last_imported = new_run
                    st.rerun()
    else:
        st.success("Run imported!")
        if st.session_state.last_imported:
            r = st.session_state.last_imported
            st.write(f"**ET:** {r['et']:.3f}s | **Clean ET:** {r.get('clean_et_estimate', 'N/A')}")
        if st.button("Import Another", use_container_width=True):
            st.session_state.import_success = False
            st.session_state.last_imported = None
            st.rerun()

# MANUAL LOG
with tab_manual:
    st.subheader("Manual Log")
    
    vehicle = st.text_input("Vehicle", value="Main Bracket Car")
    track = st.text_input("Track", value="Numidia Dragway")
    
    col1, col2 = st.columns(2)
    with col1:
        sixty = st.number_input("60 ft", value=0.0, step=0.001, format="%.3f")
        three_thirty = st.number_input("330 ft", value=0.0, step=0.001, format="%.3f")
    with col2:
        et = st.number_input("ET", value=10.0, step=0.001, format="%.3f")
        trap = st.number_input("Trap MPH", value=0.0, step=0.1)

    st.markdown("**Special Conditions:**")
    spin = st.checkbox("Spin")
    lift_before = st.checkbox("Lift before 330'")
    lift_after = st.checkbox("Lift after 330'")
    brakes_after = st.checkbox("Brakes after 330'")
    sprayed_before = st.checkbox("Sprayed nitrous before 330'")
    sprayed_after = st.checkbox("Sprayed nitrous after 330'")

    notes = st.text_area("Notes", height=50)
    
    conditions = {
        "spin": spin, "lift_before_330": lift_before, "lift_after_330": lift_after,
        "brakes_after_330": brakes_after, "sprayed_before_330": sprayed_before, "sprayed_after_330": sprayed_after
    }
    clean_et = calculate_clean_et(et, conditions) if et > 0 else None
    if clean_et:
        st.caption(f"Estimated Clean ET: {clean_et:.3f}s")

    if st.button("Save Run", type="primary", use_container_width=True):
        if et <= 0:
            st.error("Enter a valid ET")
        else:
            new_run = {
                "id": datetime.now().timestamp(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "track": track,
                "vehicle": vehicle,
                "et": et,
                "sixty_ft": sixty if sixty > 0 else None,
                "three_thirty_ft": three_thirty if three_thirty > 0 else None,
                "trap_mph": trap if trap > 0 else None,
                "density_altitude": calculate_da(75, 29.92, 50),
                "notes": notes,
                "clean_et_estimate": clean_et,
                **conditions
            }
            runs.append(new_run)
            save_runs()
            st.success("Saved!")
            st.rerun()

# PREDICT + GROK
with tab_predict:
    st.subheader("Predict ET")

    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
    if all_vehicles:
        selected_vehicle = st.selectbox("Vehicle", all_vehicles)
        vehicle_runs = [r for r in runs if r.get("vehicle") == selected_vehicle]
    else:
        selected_vehicle = "Main Car"
        vehicle_runs = []

    target_da = st.number_input("Target DA", value=1500, step=50)

    if st.button("Calculate Prediction", type="primary", use_container_width=True):
        model = calculate_model(vehicle_runs)
        if not model or len(vehicle_runs) < 3:
            st.error("Need at least 3 runs with weather data.")
        else:
            baseline = vehicle_runs[-1]
            if baseline.get("density_altitude"):
                da_diff = target_da - baseline["density_altitude"]
                predicted = baseline["et"] + (da_diff / 1000) * model["sensitivity"]
                st.success(f"**Predicted ET: {predicted:.3f}s** | Safe dial: {(predicted + 0.02):.3f}s")

    st.divider()
    st.subheader("Ask Grok")

    if st.button("Generate Prompt for Grok", use_container_width=True):
        if vehicle_runs:
            recent = vehicle_runs[-5:]
            prompt = f"Recent runs for {selected_vehicle}:\n"
            for r in recent:
                prompt += f"- {r['date']}: {r['et']:.3f}s @ {r.get('density_altitude', 'N/A')} ft\n"
            prompt += f"\nTarget DA: {target_da} ft\nGive a smart prediction and safe dial-in."
            st.code(prompt, language="text")

    grok_reply = st.text_area("Paste Grok reply")
    if st.button("Save Grok Prediction", use_container_width=True):
        if grok_reply.strip() and runs:
            runs[-1]["grok_prediction"] = grok_reply.strip()
            save_runs()
            st.success("Saved!")

# HISTORY (Lightweight version for mobile)
with tab_history:
    st.subheader("History")
    
    if not runs:
        st.info("No runs yet.")
    else:
        # Show only recent runs by default for mobile performance
        if not st.session_state.show_all_history:
            display_runs = runs[-15:][::-1]  # Last 15 runs
            st.caption(f"Showing last {len(display_runs)} runs")
            if st.button("Show All Runs"):
                st.session_state.show_all_history = True
                st.rerun()
        else:
            display_runs = runs[::-1]
            st.caption(f"Showing all {len(display_runs)} runs")
            if st.button("Show Recent Only"):
                st.session_state.show_all_history = False
                st.rerun()

        for r in display_runs:
            with st.expander(f"{r['date']} • {r.get('vehicle','')} • {r['et']:.3f}s"):
                st.write(f"**ET:** {r['et']:.3f}s")
                if r.get("clean_et_estimate"):
                    st.write(f"**Clean ET:** {r['clean_et_estimate']:.3f}s")
                if r.get("density_altitude"):
                    st.write(f"**DA:** {r['density_altitude']} ft")
                if r.get("track"):
                    st.write(f"**Track:** {r['track']}")
                if r.get("notes"):
                    st.write(f"**Notes:** {r['notes']}")

# SETTINGS
with tab_settings:
    st.subheader("Settings")
    st.text_input("Default Vehicle", value="Main Bracket Car")
    st.number_input("Safety Margin", value=0.020, step=0.005, format="%.3f")
    st.caption("v1.18 • Mobile Optimized • Lightweight History")

st.divider()
st.caption("Smart Slip v1.18 • Built for bracket racers")