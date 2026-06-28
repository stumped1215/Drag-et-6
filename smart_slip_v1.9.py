import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

st.set_page_config(
    page_title="Smart Slip",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== SESSION STATE ==============
if "runs" not in st.session_state:
    st.session_state.runs = []
if "import_success" not in st.session_state:
    st.session_state.import_success = False
if "last_imported" not in st.session_state:
    st.session_state.last_imported = None

runs = st.session_state.runs

def save_runs():
    st.session_state.runs = runs

def calculate_da(temp_f, altim_inhg, humidity=50, elevation=400):
    if temp_f is None or altim_inhg is None:
        return None
    pa = (29.92 - altim_inhg) * 1000 + elevation
    da = pa + 120 * (temp_f - 59) + (humidity / 100) * 25
    return round(da)

def calculate_model(runs):
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
        "runs_used": len(valid)
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

# ============== UI ==============
st.title("🏁 Smart Slip")
st.caption("Bracket Racing • Formula + Grok Hybrid  •  v1.9")

runs = st.session_state.runs

with st.sidebar:
    st.header("Quick Stats")
    st.metric("Total Runs", len(runs))
    if runs:
        st.metric("Best ET", f"{min(r['et'] for r in runs):.3f}s")
    model = calculate_model(runs)
    if model:
        st.metric("Model R²", model["r2"])
        st.metric("Sensitivity", f"{model['sensitivity']:.4f}s / 1000ft DA")

tab_dashboard, tab_import, tab_manual, tab_predict, tab_history, tab_settings = st.tabs([
    "Dashboard", "Import from Grok", "Manual Log", "Predict + Grok", "History", "Settings"
])

# DASHBOARD
with tab_dashboard:
    st.subheader("Overview")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Runs Logged", len(runs))
    with col2:
        if runs: st.metric("Best ET", f"{min(r['et'] for r in runs):.3f}s")
    with col3:
        if model: st.metric("Model R²", model["r2"])
    if model:
        st.success(f"Formula model active ({model['runs_used']} runs)")
    else:
        st.info("Log 5+ runs with weather to activate smart predictions.")

# IMPORT FROM GROK
with tab_import:
    st.subheader("Import from Grok")
    st.markdown("""
    **How to import a timeslip:**
    1. Take a clear photo of your timeslip.
    2. Upload the photo to Grok (me) in this chat.
    3. Use the prompt below when sending the photo.
    """)

    prompt_template = """Please extract all data from this timeslip photo and format it as a clean import block for Smart Slip.

Include these fields if available:
- date
- time (if shown)
- track
- vehicle (include car number if visible)
- et
- sixty_ft
- 330_ft
- eighth_et (1/8 mile)
- trap_mph
- reaction_time
- Any notes from the slip

Also pull the weather for the time shown on the slip and include:
- temp_f
- altimeter_inhg
- humidity_pct
- density_altitude

Format everything as key=value lines, one per line."""

    st.code(prompt_template, language="text")

    if not st.session_state.import_success:
        block = st.text_area("Paste the formatted block from Grok here:", height=180, key="import_block")

        st.markdown("**Special Conditions (timing matters):**")
        col1, col2 = st.columns(2)
        with col1:
            spin = st.checkbox("Spin")
            lift_before = st.checkbox("Lift before 330'")
            lift_after = st.checkbox("Lift after 330'")
        with col2:
            brakes_after = st.checkbox("Brakes after 330'")
            sprayed_before = st.checkbox("Sprayed (nitrous) before 330'")
            sprayed_after = st.checkbox("Sprayed (nitrous) after 330'")

        if st.button("Import Run", type="primary", disabled=st.session_state.import_success):
            if not block or not block.strip():
                st.error("Please paste the block first.")
            else:
                data = {}
                for line in block.strip().split("\n"):
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

                if "et" not in data:
                    st.error("Could not find ET in the block.")
                else:
                    new_run = {
                        "id": datetime.now().timestamp(),
                        "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        "vehicle": data.get("vehicle", "Main Car"),
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
                        "spin": spin,
                        "lift_before_330": lift_before,
                        "lift_after_330": lift_after,
                        "brakes_after_330": brakes_after,
                        "sprayed_before_330": sprayed_before,
                        "sprayed_after_330": sprayed_after
                    }
                    runs.append(new_run)
                    save_runs()
                    st.session_state.import_success = True
                    st.session_state.last_imported = new_run
                    st.rerun()
    else:
        st.success("✅ Run imported successfully!")
        if st.session_state.last_imported:
            r = st.session_state.last_imported
            st.write(f"**ET:** {r['et']:.3f}s | **Vehicle:** {r.get('vehicle', 'N/A')}")
            if r.get("density_altitude"):
                st.write(f"**Density Altitude:** {r['density_altitude']} ft")
            if r.get("notes"):
                st.write(f"**Notes:** {r['notes']}")

        if st.button("Import Another Run"):
            st.session_state.import_success = False
            st.session_state.last_imported = None
            st.rerun()

# MANUAL LOG (now with same special condition options + 330 ft)
with tab_manual:
    st.subheader("Manual Log")
    col1, col2 = st.columns(2)
    with col1:
        vehicle = st.text_input("Vehicle / Setup", value="Main Bracket Car")
        st.markdown("**Weather**")
        c1, c2, c3 = st.columns(3)
        with c1: temp_f = st.number_input("Temp °F", value=75.0, step=0.5)
        with c2: altim = st.number_input("Altimeter", value=29.92, step=0.01, format="%.2f")
        with c3: humidity = st.number_input("Humidity %", value=50)
        da = calculate_da(temp_f, altim, humidity)
        st.caption(f"DA: **{da} ft**")
        icao = st.text_input("Airport ICAO", value="KMDT")
        if st.button("Fetch Weather"):
            wx = fetch_weather(icao)
            if wx:
                st.success(f"Weather loaded from {icao}")
    with col2:
        et = st.number_input("ET", value=10.0, step=0.001, format="%.3f")
        sixty = st.number_input("60 ft", value=0.0, step=0.001, format="%.3f")
        three_thirty = st.number_input("330 ft", value=0.0, step=0.001, format="%.3f")
        trap = st.number_input("Trap MPH", value=0.0, step=0.1)
        
        st.markdown("**Special Conditions (timing matters):**")
        colA, colB = st.columns(2)
        with colA:
            spin = st.checkbox("Spin")
            lift_before = st.checkbox("Lift before 330'")
            lift_after = st.checkbox("Lift after 330'")
        with colB:
            brakes_after = st.checkbox("Brakes after 330'")
            sprayed_before = st.checkbox("Sprayed (nitrous) before 330'")
            sprayed_after = st.checkbox("Sprayed (nitrous) after 330'")

        notes = st.text_area("Notes (optional)")
        adjustment = 0.0
        if sprayed_before or sprayed_after: adjustment -= 0.08   # nitrous benefit
        if lift_before or lift_after: adjustment += 0.05         # rough penalty
        if spin: adjustment += 0.06
        if brakes_after: adjustment += 0.04
        if et > 0:
            st.caption(f"**Estimated clean ET:** {et + adjustment:.3f}s")

    if st.button("Save Run", type="primary"):
        if et <= 0:
            st.error("Enter a valid ET")
        else:
            new_run = {
                "id": datetime.now().timestamp(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "vehicle": vehicle,
                "et": et,
                "sixty_ft": sixty if sixty > 0 else None,
                "three_thirty_ft": three_thirty if three_thirty > 0 else None,
                "trap_mph": trap if trap > 0 else None,
                "density_altitude": da,
                "temp_f": temp_f,
                "altimeter_inhg": altim,
                "humidity_pct": humidity,
                "notes": notes,
                "spin": spin,
                "lift_before_330": lift_before,
                "lift_after_330": lift_after,
                "brakes_after_330": brakes_after,
                "sprayed_before_330": sprayed_before,
                "sprayed_after_330": sprayed_after
            }
            runs.append(new_run)
            save_runs()
            st.success("Run saved!")
            st.rerun()

# PREDICT + GROK
with tab_predict:
    st.subheader("Predict ET (Vehicle Specific)")
    all_vehicles = sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
    if all_vehicles:
        selected_vehicle = st.selectbox("Predict for which vehicle?", all_vehicles, index=0)
        vehicle_runs = [r for r in runs if r.get("vehicle") == selected_vehicle]
    else:
        selected_vehicle = "Main Car"
        vehicle_runs = []

    target_da = st.number_input("Target Density Altitude", value=1500, step=50)

    if st.button("Calculate Prediction for Vehicle"):
        model = calculate_model(vehicle_runs)
        if not model or len(vehicle_runs) < 3:
            st.error(f"Need at least 3 runs with weather data for **{selected_vehicle}**.")
        else:
            baseline = vehicle_runs[-1]
            if baseline.get("density_altitude"):
                da_diff = target_da - baseline["density_altitude"]
                predicted = baseline["et"] + (da_diff / 1000) * model["sensitivity"]
                safe = predicted + 0.02
                st.success(f"**Predicted ET for {selected_vehicle}: {predicted:.3f}s**")
                st.info(f"**Recommended safe dial-in: {safe:.3f}s**")

    st.divider()
    st.subheader("Consult Grok (One-Press Prompt)")

    if st.button("Generate Full Prompt for Grok", type="primary"):
        if not vehicle_runs:
            st.warning("No runs found for this vehicle yet.")
        else:
            recent = vehicle_runs[-8:]
            prompt = f"You are helping with bracket racing predictions for {selected_vehicle}.\n\n"
            prompt += "Recent runs:\n"
            for r in recent:
                prompt += f"- {r['date']}: ET {r['et']:.3f}s @ {r.get('density_altitude', 'N/A')} ft DA"
                conditions = []
                if r.get("spin"): conditions.append("spin")
                if r.get("lift_before_330"): conditions.append("lift before 330' (big negative)")
                if r.get("lift_after_330"): conditions.append("lift after 330'")
                if r.get("brakes_after_330"): conditions.append("brakes after 330'")
                if r.get("sprayed_before_330"): conditions.append("sprayed nitrous before 330' (positive - more time on nitrous)")
                if r.get("sprayed_after_330"): conditions.append("sprayed nitrous after 330' (positive but smaller impact)")
                if conditions:
                    prompt += f" | Conditions: {', '.join(conditions)}"
                if r.get("notes"):
                    prompt += f" | Notes: {r['notes']}"
                prompt += "\n"
            prompt += f"\nTarget Density Altitude: {target_da} ft\n"
            prompt += "\nPlease give a smart ET prediction with reasoning and a recommended safe dial-in. Note that early nitrous helps more, while early lift/spin hurts much more."
            
            st.code(prompt, language="text")
            st.caption("Copy the prompt above and send it to me. Paste my response below to save it.")

    grok_reply = st.text_area("Paste Grok's response here to save it")
    if st.button("Save Grok Prediction"):
        if grok_reply.strip() and runs:
            runs[-1]["grok_prediction"] = grok_reply.strip()
            save_runs()
            st.success("Saved to latest run!")

# HISTORY
with tab_history:
    st.subheader("Run History")
    if not runs:
        st.info("No runs yet.")
    else:
        all_vehicles = ["All Vehicles"] + sorted(list(set(r.get("vehicle", "Unknown") for r in runs)))
        selected_filter = st.selectbox("Filter by Vehicle", all_vehicles)
        
        filtered_runs = runs
        if selected_filter != "All Vehicles":
            filtered_runs = [r for r in runs if r.get("vehicle") == selected_filter]
        
        if filtered_runs:
            df = pd.DataFrame(filtered_runs)
            editable_cols = ["notes"]
            display_cols = ["date", "vehicle", "et", "density_altitude", "notes"]
            available_cols = [c for c in display_cols if c in df.columns]
            
            edited_df = st.data_editor(
                df[available_cols],
                use_container_width=True,
                num_rows="fixed",
                disabled=[col for col in available_cols if col not in editable_cols],
                key="history_editor"
            )
            
            if not edited_df.equals(df[available_cols]):
                for idx, row in edited_df.iterrows():
                    original_idx = df.index[idx]
                    if "notes" in row:
                        runs[original_idx]["notes"] = row["notes"]
                save_runs()
                st.success("Notes updated!")
                st.rerun()
        else:
            st.info("No runs for this vehicle.")

# SETTINGS
with tab_settings:
    st.subheader("Settings")
    st.text_input("Default Vehicle", value="Main Bracket Car")
    st.number_input("Safety Margin (sec)", value=0.020, step=0.005, format="%.3f")
    st.caption("More settings coming soon.")

st.divider()
st.caption("Smart Slip v1.9 • Formula + Grok Hybrid Intelligence • Built for bracket racers")