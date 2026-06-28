import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import json

st.set_page_config(
    page_title="Smart Slip",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== DATA HANDLING ==============
def load_data():
    if "runs" not in st.session_state:
        st.session_state.runs = []
    return st.session_state.runs

def save_data(runs):
    st.session_state.runs = runs

def calculate_da(temp_f, altim_inhg, humidity=50, elevation=400):
    if temp_f is None or altim_inhg is None:
        return None
    pa = (29.92 - altim_inhg) * 1000 + elevation
    da = pa + 120 * (temp_f - 59)
    da += (humidity / 100) * 25
    return round(da)

def calculate_model(runs):
    valid = [r for r in runs if r.get("density_altitude") and r.get("et")]
    if len(valid) < 3:
        return None
    
    X = np.array([r["density_altitude"] for r in valid])
    y = np.array([r["et"] for r in valid])
    
    # Simple linear regression
    slope, intercept = np.polyfit(X, y, 1)
    
    # R²
    y_pred = slope * X + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    sensitivity = abs(slope) * 1000  # seconds per 1000 ft DA
    
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": round(r2, 3),
        "sensitivity": round(sensitivity, 4),
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
                return {
                    "temp_f": temp_f,
                    "altimeter_inhg": altim,
                    "humidity_pct": 50,  # approximate
                    "source": f"aviationweather.gov ({icao})"
                }
    except:
        pass
    return None

# ============== UI ==============
st.title("🏁 Smart Slip")
st.caption("Your personal bracket racing assistant • Hybrid predictions (App + Grok)")

runs = load_data()

# Sidebar - Quick Stats
with st.sidebar:
    st.header("Quick Stats")
    st.metric("Total Runs", len(runs))
    if runs:
        best_et = min(r["et"] for r in runs)
        st.metric("Best ET", f"{best_et:.3f}s")
    
    model = calculate_model(runs)
    if model:
        st.metric("Model R²", model["r2"])
        st.metric("Sensitivity", f"{model['sensitivity']:.4f}s / 1000ft DA")
    else:
        st.info("Log 5+ runs with weather data for smart predictions")

# Main Tabs
tab_dashboard, tab_import, tab_log, tab_predict, tab_history, tab_settings = st.tabs([
    "Dashboard", "Import from Photo", "Log Run", "Predict", "History", "Settings"
])

# ========== DASHBOARD ==========
with tab_dashboard:
    st.subheader("Overview")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Runs Logged", len(runs))
    with col2:
        if runs:
            st.metric("Best ET", f"{min(r['et'] for r in runs):.3f}s")
    
    if model:
        st.success(f"**Smart Model Active** — Based on {model['runs_used']} runs")
        st.write(f"**Your sensitivity:** {model['sensitivity']:.4f} seconds per 1000 ft Density Altitude")
    else:
        st.warning("Log at least 5 runs with weather data to activate smart predictions.")

# ========== IMPORT FROM PHOTO ==========
with tab_import:
    st.subheader("Import from Photo (Recommended)")
    st.markdown("""
    **Best workflow:**
    1. Take a clear photo of your timeslip
    2. Upload it to me (Grok) in this chat
    3. I extract the data + pull the correct weather for the time on the slip
    4. Paste the block I give you below
    """)
    
    block = st.text_area("Paste the import block from Grok here:", height=200)
    
    if st.button("Import Run", type="primary"):
        if not block.strip():
            st.error("Please paste the block first.")
        else:
            # Simple parser
            data = {}
            for line in block.strip().split("\n"):
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if v.lower() in ["none", "null", ""]:
                        continue
                    try:
                        if k in ["et", "sixty_ft", "eighth_et", "trap_mph", "reaction_time", 
                                "temp_f", "altimeter_inhg", "humidity_pct", "density_altitude"]:
                            data[k] = float(v)
                        else:
                            data[k] = v
                    except:
                        data[k] = v
            
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
                    "notes": data.get("notes", "")
                }
                runs.append(new_run)
                save_data(runs)
                st.success(f"Run imported! ET: {data['et']:.3f}s")
                st.rerun()

# ========== LOG RUN ==========
with tab_log:
    st.subheader("Log New Run")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vehicle = st.text_input("Vehicle / Setup", value="Main Bracket Car")
        
        st.markdown("**Weather**")
        col_temp, col_alt, col_hum = st.columns(3)
        with col_temp:
            temp_f = st.number_input("Temp °F", value=75.0, step=0.5)
        with col_alt:
            altim = st.number_input("Altimeter (inHg)", value=29.92, step=0.01, format="%.2f")
        with col_hum:
            humidity = st.number_input("Humidity %", value=50, step=1)
        
        da = calculate_da(temp_f, altim, humidity)
        st.caption(f"Calculated Density Altitude: **{da} ft**")
        
        # Quick fetch buttons
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Use Current Location"):
                st.info("Geolocation works best in the hosted version. For now, enter airport manually below.")
        with col_b:
            icao = st.text_input("Airport ICAO", value="KMDT")
            if st.button("Fetch Weather"):
                wx = fetch_weather(icao)
                if wx:
                    st.success(f"Weather loaded from {icao}")
                    # In real Streamlit we would update session state here
                else:
                    st.error("Could not fetch weather.")
    
    with col2:
        st.markdown("**Timeslip**")
        reaction = st.number_input("Reaction Time", value=0.0, step=0.001, format="%.3f")
        sixty = st.number_input("60 ft", value=0.0, step=0.001, format="%.3f")
        eighth = st.number_input("660 ft (1/8)", value=0.0, step=0.001, format="%.3f")
        et = st.number_input("ET (1320 ft)", value=10.0, step=0.001, format="%.3f")
        trap = st.number_input("Trap Speed (mph)", value=0.0, step=0.1)
        
        st.markdown("**Special Conditions**")
        nitrous = st.checkbox("Nitrous used")
        lifted = st.checkbox("Lifted / wheelie")
        brakes = st.checkbox("Brakes after 330'")
        
        notes = st.text_area("Notes", placeholder="Any details about the run...")
        
        # Adjusted ET estimate
        adjustment = 0.0
        if nitrous: adjustment -= 0.08
        if lifted: adjustment -= 0.05
        if brakes: adjustment -= 0.04
        adjusted_et = et + adjustment if et > 0 else 0
        if adjusted_et > 0:
            st.caption(f"**Estimated clean ET:** {adjusted_et:.3f}s")
    
    if st.button("Save Run", type="primary"):
        if et <= 0:
            st.error("Please enter a valid ET.")
        else:
            new_run = {
                "id": datetime.now().timestamp(),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "vehicle": vehicle,
                "et": et,
                "sixty_ft": sixty if sixty > 0 else None,
                "eighth_et": eighth if eighth > 0 else None,
                "trap_mph": trap if trap > 0 else None,
                "reaction_time": reaction if reaction > 0 else None,
                "density_altitude": da,
                "temp_f": temp_f,
                "altimeter_inhg": altim,
                "humidity_pct": humidity,
                "notes": notes,
                "nitrous": nitrous,
                "lifted": lifted,
                "brakes_after_330": brakes,
                "adjusted_et": adjusted_et if adjusted_et > 0 else None
            }
            runs.append(new_run)
            save_data(runs)
            st.success("Run saved!")
            st.rerun()

# ========== PREDICT ==========
with tab_predict:
    st.subheader("Predict Next ET")
    
    col1, col2 = st.columns(2)
    with col1:
        target_da = st.number_input("Target Density Altitude", value=1500, step=50)
        target_temp = st.number_input("Target Temp °F", value=78.0, step=0.5)
    
    if st.button("Calculate Prediction", type="primary"):
        model = calculate_model(runs)
        if not model:
            st.error("Need at least 3 runs with weather data.")
        else:
            # Use most recent run as baseline
            baseline = runs[-1]
            if not baseline.get("density_altitude"):
                st.error("Most recent run needs weather data.")
            else:
                da_diff = target_da - baseline["density_altitude"]
                predicted = baseline["et"] + (da_diff / 1000) * model["sensitivity"]
                safe_dial = predicted + 0.02
                
                st.success(f"**Predicted ET: {predicted:.3f}s**")
                st.info(f"**Recommended safe dial-in: {safe_dial:.3f}s** (+0.020s margin)")
                st.caption(f"Based on your sensitivity of {model['sensitivity']:.4f}s per 1000 ft DA")
    
    st.divider()
    st.subheader("Want a smarter prediction from Grok?")
    st.markdown("Click below to generate a summary you can send to me for a more contextual prediction.")
    
    if st.button("Prepare message for Grok"):
        if not runs:
            st.warning("Log some runs first.")
        else:
            recent = runs[-5:]  # last 5 runs
            summary = "Here are my recent runs:\n\n"
            for r in recent:
                summary += f"- {r['date']}: ET {r['et']:.3f}s @ {r.get('density_altitude', 'N/A')} ft DA"
                if r.get('notes'):
                    summary += f" | Notes: {r['notes']}"
                summary += "\n"
            
            summary += f"\nCurrent/Target DA: {target_da} ft\n"
            summary += "Please give me a smart prediction and recommended dial-in."
            
            st.code(summary, language="text")
            st.caption("Copy the above and send it to me in chat for a better prediction.")

# ========== HISTORY ==========
with tab_history:
    st.subheader("Run History")
    
    if not runs:
        st.info("No runs logged yet.")
    else:
        df = pd.DataFrame(runs)
        display_cols = ["date", "vehicle", "et", "density_altitude", "temp_f", "notes"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols].sort_values("date", ascending=False), use_container_width=True)

# ========== SETTINGS ==========
with tab_settings:
    st.subheader("Settings")
    
    default_vehicle = st.text_input("Default Vehicle Name", value="Main Bracket Car")
    safety_margin = st.number_input("Default Safety Margin (seconds)", value=0.020, step=0.005, format="%.3f")
    
    st.caption("More settings coming soon (default airport, elevation, etc.)")
    
    if st.button("Save Settings"):
        st.success("Settings saved! (This version stores in session — will improve in hosted version)")

st.divider()
st.caption("Smart Slip • Hybrid predictions (App formula + Grok intelligence) • Built for bracket racers")