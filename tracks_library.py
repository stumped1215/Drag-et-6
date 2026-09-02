# Temporary stub so Streamlit can import. Replace with the full tracks_library.py.
TRACK_LIBRARY = [("Numidia Dragway", "Numidia", "PA")]
TRACK_POINTS = {"numidia dragway": (40.88906, -76.40027, 890)}
TRACK_ICAO = {"numidia dragway": "KSEG"}

def track_names():
    return [n for n, _, _ in TRACK_LIBRARY]

def track_label(name, city, region):
    return f"{name} — {city}, {region}"

def suggest_tracks(query, limit=6):
    return []

def match_track_from_slip(raw):
    n = (raw or "").strip().lower()
    if "numidia" in n:
        return "Numidia Dragway"
    return None

def find_track(query):
    q = (query or "").strip().lower()
    if not q:
        return None
    for name, city, region in TRACK_LIBRARY:
        if q == name.lower() or q in name.lower() or name.lower() in q:
            rec = {"name": name, "city": city, "region": region, "address": f"{city}, {region}"}
            pt = TRACK_POINTS.get(name.lower())
            if pt:
                rec["lat"], rec["lon"], rec["elev_ft"] = pt
            rec["icao"] = TRACK_ICAO.get(name.lower())
            return rec
    return None

def geocode_track(city, region, cache=None):
    return (None, None)
