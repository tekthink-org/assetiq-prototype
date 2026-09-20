"""
Asset IQ prototype — synthetic demo data generator (Lake L-01 + portfolio).
All names, figures, coordinates and records are FICTITIOUS.
Coordinates are a local metre grid (x east, y north); not latitude/longitude.
Re-run to regenerate: python3 gen_aiq_demo_data.py  (fixed seed, deterministic)
"""
import json, math, random, hashlib
from datetime import datetime, timedelta, date

random.seed(20260916)
AS_OF = datetime(2026, 9, 15, 18, 0)
START = datetime(2026, 6, 18, 0, 0)          # 90 days ending on AS_OF
DAYS = 90

def d(day, hh=10, mm=0):                      # day 1 = START date
    return (START + timedelta(days=day - 1, hours=hh, minutes=mm)).isoformat(timespec="minutes")

def sha(tag):                                 # synthetic evidence hash
    return hashlib.sha256(("AIQ-DEMO|" + tag).encode()).hexdigest()

def ellipse(cx, cy, a, b, n=48, jitter=0.0, seed=0):
    r = random.Random(seed)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        k = 1 + r.uniform(-jitter, jitter)
        pts.append([round(cx + a * k * math.cos(t), 1), round(cy + b * k * math.sin(t), 1)])
    pts.append(pts[0])
    return pts

def area(poly):
    s = 0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2

def scale(poly, f, cx=0, cy=0):
    return [[round(cx + (x - cx) * f, 1), round(cy + (y - cy) * f, 1)] for x, y in poly]

def ha(m2): return round(m2 / 10000, 2)

# ---------------------------------------------------------------- geometry
ftl = ellipse(0, 0, 450, 300, jitter=0.06, seed=1)
buffer_outer = scale(ftl, 1 + 30 / 375)          # ~30 m outside FTL on average
water_spread_now = scale(ftl, 0.965)
catchment = ellipse(-150, 450, 1900, 1400, n=36, jitter=0.12, seed=2)
downstream = [[-250, -330], [250, -330], [420, -1400], [-420, -1400], [-250, -330]]
fill_new = [[40, 318], [70, 318], [71, 334], [40, 334], [40, 318]]          # ~0.12 acre

geometry = {
    "crs": "LOCAL_METRES (synthetic; schematic display only)",
    "ftl_boundary": ftl,
    "buffer_outer_boundary": buffer_outer,
    "water_spread_current": water_spread_now,
    "catchment": catchment,
    "downstream_area": downstream,
    "structures": [
        {"id": "ST-BUND", "type": "bund", "name": "Main bund (south)", "line": [[-260, -290], [260, -290]], "length_m": 520},
        {"id": "ST-WEIR", "type": "surplus_weir", "name": "Surplus weir", "point": [230, -300]},
        {"id": "ST-SLUICE", "type": "sluice", "name": "Irrigation sluice", "point": [-120, -300]},
        {"id": "IN-1", "type": "inlet", "name": "Inlet 1 — storm-water channel (north-west)", "point": [-380, 190]},
        {"id": "IN-2", "type": "inlet", "name": "Inlet 2 — nala from colony (north)", "point": [60, 310]},
        {"id": "IN-3", "type": "inlet", "name": "Inlet 3 — field channel (east)", "point": [455, 40]},
    ],
    "change_polygons": [{"id": "CHG-001", "polygon": fill_new}],
    "record_boundaries_note": ("Illustrative only. These are not survey products: they stand in for the "
                               "differing boundaries that departmental records would show for the same lake."),
    "record_boundaries": {},
}
A_FTL, A_BUF, A_WS = area(ftl), area(buffer_outer) - area(ftl), area(water_spread_now)

def shift_north(poly, dy, cutoff=170):
    """Push the northern part of a boundary out or in, to stand in for a records dispute."""
    out = []
    for x, y in poly:
        out.append([x, round(y + dy, 1)] if y > cutoff else [x, y])
    out[-1] = out[0]
    return out

def to_area(poly, target_m2):
    import math as _m
    f = _m.sqrt(target_m2 / area(poly))
    return scale(poly, f)

geometry["record_boundaries"] = {
    "DR-REV": to_area(shift_north(ftl, 14), 44.1 * 10000),
    "DR-IRR": to_area(shift_north(ftl, -16), 41.6 * 10000),
    "DR-NOT": to_area(ftl, 42.0 * 10000),
}
A_FILL = area(fill_new)

# ---------------------------------------------------------------- reference
authority = {"id": "AUTH-DMLA", "name": "Demo Metro Lakes Authority", "fictitious": True}
jurisdiction = {"zone": "North Zone", "circle": "Circle 3", "ward": "Ward 17"}
users = [
    {"id": "U-NO", "name": "R. Varma", "role": "Nodal Officer"},
    {"id": "U-AE", "name": "K. Prasad", "role": "Assistant Engineer"},
    {"id": "U-EE", "name": "M. Rao", "role": "Executive Engineer (check-measurement)"},
    {"id": "U-FA1", "name": "S. Naidu", "role": "Field Assistant"},
    {"id": "U-FA2", "name": "P. Latha", "role": "Field Assistant"},
    {"id": "U-SV", "name": "Survey partner", "role": "Survey and drone operations"},
    {"id": "U-LAB", "name": "Demo Water Testing Lab", "role": "Accredited laboratory"},
]

custody_history = [
    {"state": "identified", "date": "2019-03-12", "basis": "Entered on authority water body register"},
    {"state": "preliminary_notified", "date": "2023-11-06", "basis": "Preliminary FTL notification (fictitious ref PN/2023/117)"},
    {"state": "final_notified", "date": "2025-08-21", "basis": "Final FTL notification (fictitious ref FN/2025/042)"},
    {"state": "baselined", "date": "2026-07-08", "basis": "Spatial baseline package accepted by Nodal Officer"},
    {"state": "under_restoration", "date": "2026-07-20", "basis": "Restoration work order WO-DMLA-2026-031 issued"},
]

zones = [
    {"id": "Z-WS", "name": "Water spread", "area_ha": ha(A_WS)},
    {"id": "Z-FTL", "name": "FTL band", "area_ha": ha(A_FTL - A_WS)},
    {"id": "Z-BUF", "name": "Buffer zone", "area_ha": ha(A_BUF), "width_m": 30, "note": "Buffer width illustrative"},
    {"id": "Z-STR", "name": "Inlets, outlets and structures"},
    {"id": "Z-CAT", "name": "Catchment", "area_ha": ha(area(catchment))},
    {"id": "Z-DS", "name": "Downstream area", "area_ha": ha(area(downstream))},
]

asset = {
    "id": "L-01", "name": "Lake L-01", "display_name": "Sarovara Tank (fictitious)",
    "asset_type": "lake", "authority_id": authority["id"], **jurisdiction,
    "ftl_area_ha": ha(A_FTL), "gauge_datum_note": "FTL = 100.00 m on local gauge (synthetic)",
    "ftl_gauge_m": 100.00, "storage_at_ftl_ml": 1410, "custody_state": "under_restoration",
    "zones": zones, "schematic_position": [0, 0],
}

# ---------------------------------------------------------------- spatial baseline + records
spatial_baseline = {
    "id": "SB-L01-v1", "accepted_on": "2026-07-08", "accepted_by": "U-NO", "produced_by": "U-SV",
    "ftl_area_ha": ha(A_FTL), "method": "DGPS survey + drone orthophoto (synthetic)",
    "bathymetry": {"surveyed_on": "2026-07-02", "mean_depth_m": 2.9, "max_depth_m": 5.6,
                   "storage_at_ftl_ml": 1410, "design_storage_ml": 1650,
                   "storage_loss_pct": round((1650 - 1410) / 1650 * 100, 1),
                   "note": "Design storage from departmental tank register (synthetic)"},
    "layers": [
        {"layer": "FTL boundary", "version": 1, "date": "2026-07-08"},
        {"layer": "Buffer boundary", "version": 1, "date": "2026-07-08"},
        {"layer": "Orthophoto", "version": 1, "date": "2026-06-29"},
        {"layer": "Orthophoto", "version": 2, "date": "2026-08-11"},
        {"layer": "Bathymetric surface", "version": 1, "date": "2026-07-02"},
    ],
}
departmental_records = [
    {"id": "DR-REV", "department": "Revenue (village map)", "vintage": "1998", "ftl_area_ha": 44.1},
    {"id": "DR-IRR", "department": "Irrigation (tank register)", "vintage": "2011", "ftl_area_ha": 41.6},
    {"id": "DR-NOT", "department": "Final FTL notification", "vintage": "2025", "ftl_area_ha": 42.0},
]
record_discrepancies = [
    {"id": "RD-001", "records": ["DR-REV", "DR-IRR"], "subject": "FTL line on north bank",
     "difference": "Up to 18 m offset over 240 m of boundary; area differs by 2.5 ha",
     "baseline_position": "Survey baseline follows final notification within 1 m",
     "status": "escalated_for_ruling", "raised_on": "2026-07-06", "owner": "U-NO",
     "ruling": None, "ruling_due": "2026-09-30"},
    {"id": "RD-002", "records": ["DR-IRR", "SB-L01-v1"], "subject": "Design storage capacity",
     "difference": "Register 1,650 ML; bathymetry 1,410 ML at FTL",
     "baseline_position": "Difference attributed to siltation; recorded, not a boundary dispute",
     "status": "recorded", "raised_on": "2026-07-03", "owner": "U-AE", "ruling": "Noted", "ruling_due": None},
]

# ---------------------------------------------------------------- sensors
sensor_devices = [
    {"id": "SN-WQ1", "type": "water_quality", "location": [60, 270], "zone": "Z-WS",
     "parameters": ["do_mg_l", "ph", "turbidity_ntu", "temp_c", "ec_us_cm"], "commissioned_on": "2026-07-24", "interval_h": 3},
    {"id": "SN-LV1", "type": "level", "location": [-110, -280], "zone": "Z-STR",
     "parameters": ["level_m"], "commissioned_on": "2026-07-22", "interval_h": 3},
]
thresholds = {
    "note": "Illustrative thresholds for the prototype; to be confirmed against the applicable standard for the site.",
    "do_mg_l": {"alert_below": 4.0}, "ph": {"alert_below": 6.5, "alert_above": 8.5},
    "turbidity_ntu": {"alert_above": 40}, "level_m": {"watch_above": 99.6, "alert_above": 99.85},
}

def rainfall(day):
    return {38: 42, 39: 88, 40: 61, 41: 12, 63: 35, 64: 20, 80: 18, 85: 22}.get(day, 0 if random.random() < 0.75 else round(random.uniform(1, 9), 1))

rain_daily = [{"date": (START + timedelta(days=i)).date().isoformat(), "rain_mm": rainfall(i + 1)} for i in range(DAYS)]

readings = []
level = 98.72
for day in range(1, DAYS + 1):
    for h in range(0, 24, 3):
        ts = START + timedelta(days=day - 1, hours=h)
        rain = rain_daily[day - 1]["rain_mm"]
        # level node (from day 35)
        if ts >= datetime(2026, 7, 22):
            level += rain / 8 * 0.0045 - 0.0014 + random.uniform(-0.001, 0.001)
            if ts.date() == date(2026, 8, 25) and 6 <= h <= 18:
                level -= 0.012   # authorised sluice release (EV-08)
            readings.append({"device": "SN-LV1", "ts": ts.isoformat(timespec="minutes"), "level_m": round(level, 3)})
        else:
            level += rain / 8 * 0.0045 - 0.0014
        # water quality node (from day 37)
        if ts < datetime(2026, 7, 24):
            continue
        offline = datetime(2026, 9, 7, 3) <= ts < datetime(2026, 9, 7, 12)
        if offline:
            continue
        diurnal = math.sin((h - 9) / 24 * 2 * math.pi)
        do = 6.1 + 1.3 * diurnal + random.uniform(-0.25, 0.25)
        tur = 14 + random.uniform(-3, 3) + (rain * 0.4 if rain else 0)
        ph = 7.6 + 0.25 * diurnal + random.uniform(-0.08, 0.08)
        ec = 780 + random.uniform(-25, 25)
        # planted anomaly: sewage inflow at Inlet 2, 14–16 Aug (days 58–60)
        t0 = datetime(2026, 8, 14, 21)
        if t0 <= ts < t0 + timedelta(hours=60):
            k = min(1, (ts - t0).total_seconds() / 3600 / 18)
            do -= 3.7 * k
            tur += 38 * k
            ec += 260 * k
            ph -= 0.4 * k
        elif t0 + timedelta(hours=60) <= ts < t0 + timedelta(hours=132):
            k = 1 - (ts - t0 - timedelta(hours=60)).total_seconds() / 3600 / 72
            do -= 2.4 * k
            tur += 14 * k
            ec += 120 * k
        readings.append({"device": "SN-WQ1", "ts": ts.isoformat(timespec="minutes"),
                         "do_mg_l": round(max(do, 0.6), 2), "ph": round(ph, 2),
                         "turbidity_ntu": round(tur, 1), "temp_c": round(27.5 + 1.8 * diurnal + random.uniform(-0.3, 0.3), 1),
                         "ec_us_cm": round(ec)})

sensor_gaps = [{"device": "SN-WQ1", "from": "2026-09-07T03:00", "to": "2026-09-07T12:00",
                "cause": "Tamper alert; enclosure found opened, cable pulled; reconnected by field team", "event_id": "EV-17"}]

lab_reports = [
    {"id": "LAB-0726", "sampled_on": "2026-07-26", "point": "SP-2 (Inlet 2)", "bod_mg_l": 6.2, "cod_mg_l": 31, "fc_mpn_100ml": 2400, "do_mg_l": 5.1},
    {"id": "LAB-0809", "sampled_on": "2026-08-09", "point": "SP-2 (Inlet 2)", "bod_mg_l": 7.0, "cod_mg_l": 34, "fc_mpn_100ml": 2800, "do_mg_l": 4.9},
    {"id": "LAB-0816", "sampled_on": "2026-08-16", "point": "SP-2 (Inlet 2)", "bod_mg_l": 18.5, "cod_mg_l": 78, "fc_mpn_100ml": 16000, "do_mg_l": 1.8, "flag": "above_limit"},
    {"id": "LAB-0830", "sampled_on": "2026-08-30", "point": "SP-2 (Inlet 2)", "bod_mg_l": 8.1, "cod_mg_l": 37, "fc_mpn_100ml": 3500, "do_mg_l": 4.6},
    {"id": "LAB-0913", "sampled_on": "2026-09-13", "point": "SP-2 (Inlet 2)", "bod_mg_l": 6.8, "cod_mg_l": 33, "fc_mpn_100ml": 2600, "do_mg_l": 5.0},
    {"id": "LAB-0816B", "sampled_on": "2026-08-16", "point": "SP-4 (centre)", "bod_mg_l": 5.4, "cod_mg_l": 27, "fc_mpn_100ml": 900, "do_mg_l": 4.4},
]
lab_note = "BOD limit used for flagging is illustrative (above 10 mg/L); to be confirmed against the applicable standard."

# ---------------------------------------------------------------- observation passes
observation_passes = [
    {"id": "DP-1", "type": "drone", "date": "2026-06-29", "gsd_cm": 3, "area_ha": 78, "operator": "Licensed operator engaged by survey partner",
     "outputs": ["orthophoto v1", "surface model v1"], "status": "processed"},
    {"id": "DP-2", "type": "drone", "date": "2026-08-11", "gsd_cm": 3, "area_ha": 78, "operator": "Licensed operator engaged by survey partner",
     "outputs": ["orthophoto v2", "change report CR-02"], "status": "processed", "changes_flagged": 3, "changes_confirmed": 1},
]
satellite_series = [
    {"month": "2026-06", "water_spread_ha": 31.5, "weed_cover_pct": 9},
    {"month": "2026-07", "water_spread_ha": 34.8, "weed_cover_pct": 11},
    {"month": "2026-08", "water_spread_ha": 38.9, "weed_cover_pct": 17},
    {"month": "2026-09", "water_spread_ha": ha(A_WS), "weed_cover_pct": 19},
]
satellite_note = "Synthetic monthly values; resolution coarser than drone."

# ---------------------------------------------------------------- restoration works (quantity-based)
works = {
    "id": "WO-DMLA-2026-031", "name": "Restoration of Lake L-01 — Phase 1", "issued_on": "2026-07-20",
    "planned_completion": "2027-03-31", "contractor": "Demo Civil Works (fictitious)", "stage": "execution",
    "weight_basis": "Share of sanctioned value (illustrative)",
    "items": [
        {"id": "RW-1", "name": "Desilting — reach 1 (north)", "unit": "m3", "sanctioned_qty": 18000, "planned_by": "2026-09-30", "weight_pct": 18},
        {"id": "RW-2", "name": "Desilting — reach 2 (centre)", "unit": "m3", "sanctioned_qty": 22000, "planned_by": "2026-09-15", "weight_pct": 22},
        {"id": "RW-3", "name": "Desilting — reach 3 (south)", "unit": "m3", "sanctioned_qty": 16000, "planned_by": "2026-12-31", "weight_pct": 16},
        {"id": "RW-4", "name": "Bund strengthening and pitching", "unit": "m", "sanctioned_qty": 520, "planned_by": "2027-01-31", "weight_pct": 14},
        {"id": "RW-5", "name": "Chain-link fencing along FTL", "unit": "m", "sanctioned_qty": 2400, "planned_by": "2026-10-31", "weight_pct": 12},
        {"id": "RW-6", "name": "Sewage diversion channel at Inlet 2", "unit": "m", "sanctioned_qty": 380, "planned_by": "2026-11-30", "weight_pct": 13},
        {"id": "RW-7", "name": "Weed and hyacinth removal", "unit": "ha", "sanctioned_qty": 8, "planned_by": "2027-03-31", "weight_pct": 5},
    ],
}
measurements = [
    # id, item, day, qty, recorded_by, checked_by
    ("MB-01", "RW-1", 40, 3200), ("MB-02", "RW-2", 42, 5400), ("MB-03", "RW-1", 52, 3900),
    ("MB-04", "RW-2", 55, 6800), ("MB-05", "RW-5", 57, 180), ("MB-06", "RW-7", 60, 1.2),
    ("MB-07", "RW-1", 67, 4100), ("MB-08", "RW-2", 70, 6300), ("MB-09", "RW-5", 72, 160),
    ("MB-10", "RW-1", 81, 3600), ("MB-11", "RW-2", 84, 3500), ("MB-12", "RW-5", 86, 140),
    ("MB-13", "RW-7", 87, 0.9),
]
mb = []
for mid, item, day, qty in measurements:
    mb.append({"id": mid, "item": item, "date": d(day)[:10], "qty": qty,
               "recorded_by": "U-AE", "check_measured_by": "U-EE", "check_measured_on": d(day + 2)[:10],
               "evidence": [f"MA-{mid}"], "status": "checked"})
# progress (precomputed for display only)
done = {}
for m in mb:
    done[m["item"]] = done.get(m["item"], 0) + m["qty"]
prog_items = []
total = 0
for it in works["items"]:
    q = done.get(it["id"], 0)
    pct = min(100, q / it["sanctioned_qty"] * 100)
    total += pct * it["weight_pct"] / 100
    prog_items.append({"item": it["id"], "executed_qty": q, "pct": round(pct, 1)})
works["precomputed_progress"] = {"note": "Precomputed for prototype display only; not the platform computation.",
                                 "as_of": AS_OF.date().isoformat(), "items": prog_items, "overall_pct": round(total, 1)}
works["measurements"] = mb

# ---------------------------------------------------------------- events (20 fit-test events on L-01)
def ev(i, day, title, condition, zone, source, status, owner, deadline_day, consequence, detail, evidence=None, custody="under_restoration", **kw):
    e = {"id": f"EV-{i:02d}", "raised_at": d(day, 9 + i % 8), "title": title, "condition": condition,
         "zone": zone, "evidence_source": source, "custody_state": custody, "aiqube_tags": None,
         "status": status, "owner": owner, "deadline": d(deadline_day, 17)[:10] if deadline_day else None,
         "consequence_if_not_acted": consequence, "detail": detail, "evidence": evidence or [f"MA-EV{i:02d}"]}
    e.update(kw)
    return e

events = [
    ev(1, 55, "New fill in buffer zone, north bank", "boundary_integrity", "Z-BUF", "drone", "verified_action_open", "U-NO", 66,
       "Fill consolidates and a structure follows; removal becomes costlier and contested",
       f"Change report CR-02: {round(A_FILL)} m² ({round(A_FILL/4046.86,2)} acre) of fresh earth fill against orthophoto v1. Field verified on 12 Aug by S. Naidu; no permission on departmental record. Notice drafted, awaiting Nodal Officer signature.",
       evidence=["MA-DP1-N", "MA-DP2-N", "MA-EV01"], change_polygon="CHG-001", verified_by="U-FA1", verified_on="2026-08-12", raised_by="U-SV",
       action="Sign and serve notice; schedule removal"),
    ev(2, 30, "Foundation inside FTL, east bank", "boundary_integrity", "Z-FTL", "field_inspection", "closed", "U-NO", 35,
       "Structure completed inside FTL", "Foundation trench for boundary wall found; work stopped and trench back-filled on 21 Jul.", custody="baselined",
       verified_by="U-AE", raised_by="U-FA2", closed_on="2026-07-21"),
    ev(3, 47, "Construction debris dumped on west bank", "pollution_load", "Z-BUF", "citizen_report", "closed", "U-AE", 50,
       "Debris washes into water spread with the next rain", "Citizen photo via grievance channel; verified, 6 truckloads removed.", verified_by="U-FA2", raised_by="Citizen", closed_on="2026-08-06"),
    ev(4, 58, "Dissolved oxygen below alert threshold", "water_quality", "Z-WS", "in_situ_sensor", "closed", "U-AE", 59,
       "Fish kill risk and odour complaints within 48 hours",
       "SN-WQ1 DO fell below 4.0 mg/L from 14 Aug 23:00, lowest near 1.5 mg/L, with turbidity and conductivity rising together. Raised ahead of routine inspection; field check traced it to Inlet 2 (EV-07).",
       evidence=["MA-SN-WQ1-0815"], raised_by="System", verified_by="U-FA1", verified_on="2026-08-15", closed_on="2026-08-20",
       detected_before_manual=True),
    ev(5, 61, "BOD above limit in lab report", "water_quality", "Z-STR", "laboratory", "closed", "U-AE", 62,
       "Compliance return shows unexplained exceedance", "LAB-0816 at Inlet 2: BOD 18.5 mg/L. Linked to EV-04 and EV-07.", evidence=["LAB-0816"], raised_by="U-LAB", closed_on="2026-08-30"),
    ev(6, 76, "Algal bloom visible, north-east bay", "ecology", "Z-WS", "drone", "open", "U-AE", 80,
       "Bloom spreads and oxygen falls further at night", "Green scum visible over about 0.4 ha in inspection photos; lab sample requested.", raised_by="U-FA2", action="Collect lab sample; check Inlet 2 diversion"),
    ev(7, 59, "Untreated sewage inlet found at Inlet 2", "pollution_load", "Z-STR", "field_inspection", "verified_action_open", "U-EE", 74,
       "Water quality stays degraded; compliance deadline missed",
       "New colony outfall connected into Inlet 2 nala. Interim bund placed on 17 Aug. Diversion channel RW-6 not yet started — overdue for mobilisation.",
       raised_by="U-FA1", verified_by="U-AE", verified_on="2026-08-15", action="Mobilise RW-6 diversion channel"),
    ev(8, 69, "Abnormal fall in water level", "water_spread_storage", "Z-STR", "in_situ_sensor", "rejected", "U-AE", 70,
       "Undetected leakage through sluice", "Level fell 6 cm in 12 hours; field check found sluice opened for authorised irrigation release. No fault.", raised_by="System", verified_by="U-FA2", closed_on="2026-08-26"),
    ev(9, 42, "Seepage through main bund", "structures", "Z-STR", "field_inspection", "verified_action_open", "U-EE", 88,
       "Seepage worsens at high level; bund safety at risk", "Wet patch 12 m long at toe of bund, chainage 180–192 m, after the 25–28 Jul rain. Covered under RW-4; monitoring weekly.", raised_by="U-FA1", verified_by="U-AE", action="Include in RW-4 first stretch"),
    ev(10, 50, "Sluice gate damaged", "structures", "Z-STR", "field_inspection", "closed", "U-EE", 60, "Uncontrolled release during rain",
       "Gate spindle bent; repaired under maintenance.", raised_by="U-FA2", closed_on="2026-08-14"),
    ev(11, 15, "Storage loss from siltation", "siltation", "Z-WS", "spatial_survey", "recorded", "U-AE", None, "Flood cushion and storage stay reduced",
       "Bathymetry: 1,410 ML at FTL against 1,650 ML design — 14.5% loss. Basis for desilting quantities.", custody="final_notified", raised_by="U-SV"),
    ev(12, 88, "Desilting reach 2 measured complete", "works_progress", "Z-WS", "field_inspection", "closed", "U-AE", None, "—",
       "Cumulative 22,000 m³ against 22,000 m³ sanctioned; check-measured by M. Rao.", evidence=["MA-MB-11"], raised_by="U-AE", closed_on="2026-09-15"),
    ev(13, 86, "Fencing behind programme", "works_progress", "Z-FTL", "field_inspection", "open", "U-EE", 92,
       "Fencing not complete before planned date; encroachment exposure on north bank continues",
       "480 m executed of 2,400 m (20%); planned 70% by mid-September. Contractor cites material delay.", raised_by="System", action="Review contractor programme; prioritise north bank"),
    ev(14, 19, "FTL records disagree on north bank", "boundary_integrity", "Z-BUF", "departmental_record", "escalated", "U-NO", 105,
       "Removal action on north bank remains contestable", "See RD-001. Ruling pending.", evidence=["DR-REV", "DR-IRR"], custody="final_notified", raised_by="U-SV"),
    ev(15, 21, "Spatial baseline accepted", "legal_status", "Z-FTL", "spatial_survey", "closed", "U-NO", None, "—",
       "Baseline SB-L01-v1 accepted; custody state moves to baselined.", custody="baselined", raised_by="U-SV", closed_on="2026-07-08"),
    ev(16, 84, "Tribunal compliance report due in 14 days", "obligation", "Z-WS", "departmental_record", "open", "U-NO", 98,
       "Late filing before the tribunal; adverse remark on record", "Quarterly compliance report under fictitious order OA-000/2026 due 25 Sep. Draft generated from pilot data; awaiting review.", raised_by="System", compliance_target="CT-TRIB"),
    ev(17, 82, "Water quality sensor offline — tamper alert", "monitoring_equipment", "Z-WS", "in_situ_sensor", "closed", "U-AE", 82,
       "Blind period on water quality", "SN-WQ1 offline 03:00–12:00 on 7 Sep; enclosure opened. Reconnected; lock replaced.", raised_by="System", closed_on="2026-09-07"),
    ev(18, 83, "Weed cover increasing", "ecology", "Z-WS", "satellite", "open", "U-AE", 95,
       "Weed mat blocks light and inlet flow", "Satellite estimate 19% cover in September against 9% in June.", raised_by="System", action="Advance RW-7 schedule"),
    ev(19, 39, "Heavy rain; level approaching FTL", "flood_function", "Z-STR", "in_situ_sensor", "closed", "U-EE", 40,
       "Overtopping risk at low point of bund", "Level peaked about 0.3 m below FTL after 88 mm rain on 26 Jul. Weir operating; no overtopping.", raised_by="System", closed_on="2026-07-28"),
    ev(20, 78, "Trees felled in buffer zone", "ecology", "Z-BUF", "citizen_report", "verified_action_open", "U-NO", 90,
       "Loss of green cover precedes encroachment", "Seven trees felled on south-west buffer; verified. Complaint to be filed with forest officer.", raised_by="Citizen", verified_by="U-FA2", action="File complaint; replant"),
]

# ---------------------------------------------------------------- make event text match the generated series
wq = [r for r in readings if r["device"] == "SN-WQ1"]
first_low = next(r for r in wq if r["do_mg_l"] < thresholds["do_mg_l"]["alert_below"])
lowest = min(wq, key=lambda r: r["do_mg_l"])
fmt = lambda iso: datetime.fromisoformat(iso).strftime("%d %b %H:%M")
E = {e["id"]: e for e in events}
E["EV-04"]["raised_at"] = first_low["ts"]
E["EV-04"]["detail"] = (f"SN-WQ1 DO fell below {thresholds['do_mg_l']['alert_below']} mg/L at {fmt(first_low['ts'])}; lowest "
    f"{lowest['do_mg_l']} mg/L at {fmt(lowest['ts'])}, with turbidity and conductivity rising together. Raised ahead of routine "
    "inspection; field check traced it to Inlet 2 (EV-07).")
lv = [r for r in readings if r["device"] == "SN-LV1"]
jul = [r for r in lv if r["ts"] < "2026-08-01"]
pk = max(jul, key=lambda r: r["level_m"])
base = min((r for r in jul if r["ts"] < "2026-07-25"), key=lambda r: r["level_m"])
E["EV-19"]["title"] = "Rapid rise in water level after heavy rain"
E["EV-19"]["detail"] = (f"Level rose {round(pk['level_m'] - base['level_m'], 2)} m after 203 mm rain over 25–28 Jul, peaking at "
    f"{pk['level_m']} m on {fmt(pk['ts'])} — {round(asset['ftl_gauge_m'] - pk['level_m'], 2)} m below FTL. Weir and bund inspected; no overtopping.")
aug = [r for r in lv if r["ts"].startswith("2026-08-25")]
drop = round(max(r["level_m"] for r in aug) - min(r["level_m"] for r in aug), 2)
E["EV-08"]["detail"] = (f"Level fell {drop} m within the day on 25 Aug; field check found the sluice opened for an authorised "
    "irrigation release. No fault.")
cur = lv[-1]["level_m"]
level_status = ("green" if cur < thresholds["level_m"]["watch_above"] else "amber")

# ---------------------------------------------------------------- field capture (criterion 5)
captures = []
cap_id = 0
for day in range(61, 91):
    for who, slot in (("U-FA1", 10), ("U-FA2", 15)):
        if day % 5 not in (0, 2):
            continue
        cap_id += 1
        done_flag = cap_id not in (5, 14, 21)
        captures.append({"id": f"FC-{cap_id:03d}", "scheduled_for": d(day, slot)[:10], "assigned_to": who,
                         "checklist": "Weekly bank walk — boundary, inlets, bund, debris",
                         "status": "completed" if done_flag else "missed",
                         "captured_at": d(day, slot, random.randint(0, 50)) if done_flag else None,
                         "answers": ({"new_construction_seen": "no", "debris_seen": random.choice(["no", "no", "yes"]),
                                      "inlet_flow_normal": random.choice(["yes", "yes", "no"]), "bund_wet_patch": "yes"} if done_flag else None),
                         "photos": ([f"MA-FC{cap_id:03d}-1"] if done_flag else []),
                         "synced": (random.random() > 0.05) if done_flag else None})
comp = sum(c["status"] == "completed" for c in captures)

# ---------------------------------------------------------------- evidence ledger
media = []
# Every piece of evidence sits where the event says it happened, not at a random point.
EVENT_PLACE = {
    "EV-01": [55, 326], "EV-02": [455, 40], "EV-03": [-420, 60], "EV-04": [60, 270],
    "EV-05": [60, 310], "EV-06": [280, 230], "EV-07": [60, 310], "EV-08": [-120, -300],
    "EV-09": [-80, -292], "EV-10": [-120, -300], "EV-11": [0, 0], "EV-12": [0, 20],
    "EV-13": [-100, 300], "EV-14": [0, 330], "EV-15": [0, 0], "EV-16": [-120, -300],
    "EV-17": [60, 270], "EV-18": [150, 120], "EV-19": [230, -300], "EV-20": [-300, -200],
}
ITEM_PLACE = {"RW-1": [-150, 200], "RW-2": [0, 0], "RW-3": [0, -200],
              "RW-4": [-80, -292], "RW-5": [-200, 290], "RW-6": [60, 310], "RW-7": [200, 150]}

def add_media(mid, kind, day, by, loc, links, **extra):
    m = {"id": mid, "kind": kind, "captured_at": d(day, 11), "captured_by": by,
         "location": loc, "sha256": sha(mid), "linked_to": links}
    m.update(extra)
    media.append(m)

add_media("MA-DP1-N", "orthophoto_tile", 12, "U-SV", EVENT_PLACE["EV-01"], ["DP-1", "EV-01"],
          role="before", role_note="Before — first drone pass")
add_media("MA-DP2-N", "orthophoto_tile", 55, "U-SV", EVENT_PLACE["EV-01"], ["DP-2", "EV-01"],
          role="after", role_note="After — second drone pass")
for e in events:
    for m in e["evidence"]:
        if m.startswith("MA-EV"):
            add_media(m, "photo", int((datetime.fromisoformat(e["raised_at"]) - START).days) + 1,
                      e.get("verified_by") or e.get("owner") or "U-FA1",
                      EVENT_PLACE.get(e["id"], [0, 0]), [e["id"]])
add_media("MA-SN-WQ1-0815", "sensor_trace", 58, "SN-WQ1", EVENT_PLACE["EV-04"], ["EV-04"])
for m in mb:
    add_media(f"MA-{m['id']}", "photo", int((datetime.fromisoformat(m["date"]) - START).days) + 1, "U-AE",
              ITEM_PLACE.get(m["item"], [0, 0]), [m["id"], m["item"]])
perimeter = ftl[::4]
for n, c in enumerate(captures):
    for p in c["photos"]:
        add_media(p, "photo", int((datetime.fromisoformat(c["captured_at"]) - START).days) + 1,
                  c["assigned_to"], [round(x) for x in perimeter[n % len(perimeter)]], [c["id"]])

# ---------------------------------------------------------------- compliance
compliance_targets = [
    {"id": "CT-TRIB", "authority": "Environmental Tribunal (fictitious order OA-000/2026)", "report": "Quarterly compliance report",
     "frequency": "quarterly", "next_due": "2026-09-25", "draft_status": "generated_awaiting_review",
     "sections": [
         {"section": "1. Boundary protection", "sources": ["SB-L01-v1", "EV-01", "EV-02", "EV-14", "RD-001"]},
         {"section": "2. Water quality", "sources": ["SN-WQ1", "LAB-0726", "LAB-0809", "LAB-0816", "LAB-0830", "LAB-0913", "EV-04", "EV-05", "EV-07"]},
         {"section": "3. Restoration progress", "sources": ["WO-DMLA-2026-031", "MB-01..MB-13"]},
         {"section": "4. Actions taken and pending", "sources": ["EV-01", "EV-07", "EV-09", "EV-13", "EV-20"]},
         {"section": "Annexure — evidence register", "sources": ["media ledger"]}],
     "effort_baseline": {"note": "Illustrative. The real baseline is to be recorded by the authority at pilot start (proposal criterion 6).",
                         "manual_person_hours": 38, "generated_draft_review_person_hours": 5}},
    {"id": "CT-SPCB", "authority": "State Pollution Control Board (fictitious format)", "report": "Monthly water quality return",
     "frequency": "monthly", "next_due": "2026-10-05", "draft_status": "not_started"},
    {"id": "CT-FUND", "authority": "Funding programme (fictitious)", "report": "Physical and financial progress MIS",
     "frequency": "monthly", "next_due": "2026-10-10", "draft_status": "not_started"},
]

# ---------------------------------------------------------------- officer view summary (screen 1)
open_events = [e for e in events if e["status"] in ("open", "verified_action_open", "escalated")]
as_of_d = AS_OF.date().isoformat()
week_start = (AS_OF.date() - timedelta(days=6)).isoformat()
overdue = [e["id"] for e in open_events if e["deadline"] and e["deadline"] < as_of_d]
for e in events:
    e["overdue"] = e["id"] in overdue
changed = [e["id"] for e in events if e["raised_at"][:10] >= week_start or (e.get("closed_on") or "") >= week_start]
officer_view = {
    "as_of": AS_OF.isoformat(timespec="minutes"),
    "overall_status": "amber",
    "status_reason": "Encroachment notice unsigned; sewage diversion not mobilised; fencing behind programme",
    "indicators": [
        {"label": "Boundary", "status": "amber", "text": "1 open encroachment; 1 record dispute awaiting ruling"},
        {"label": "Water quality", "status": "amber", "text": "Recovered after August sewage event; source not yet diverted"},
        {"label": "Water level", "status": level_status, "text": f"{cur:.2f} m on gauge; {round(asset['ftl_gauge_m'] - cur, 2)} m below FTL"},
        {"label": "Restoration", "status": "amber", "text": f"{works['precomputed_progress']['overall_pct']}% overall; fencing behind"},
        {"label": "Structures", "status": "amber", "text": "Bund seepage under watch"},
        {"label": "Ecology", "status": "amber", "text": "Weed cover rising; bloom reported"},
        {"label": "Monitoring", "status": "green", "text": "Both sensors online"},
        {"label": "Compliance", "status": "amber", "text": "Tribunal report due 25 Sep; draft ready for review"},
    ],
    "what_changed_this_week": changed,
    "overdue": overdue,
    "needs_decision_today": [
        {"event": "EV-01", "decision": "Sign encroachment notice", "owner": "U-NO"},
        {"event": "EV-16", "decision": "Review and approve tribunal report draft", "owner": "U-NO"},
        {"event": "EV-14", "decision": "Rule on north-bank FTL record (RD-001)", "owner": "U-NO"},
    ],
    "open_event_count": len(open_events),
}

# ---------------------------------------------------------------- portfolio (light lakes)
names = ["Kamala Kunta", "Pedda Tank", "Neeli Cheruvu", "Chinna Kunta", "Rama Tank", "Gowri Cheruvu", "Surya Kunta", "Mallika Tank", "Tulasi Cheruvu"]
states = ["final_notified", "baselined", "preliminary_notified", "final_notified", "identified", "final_notified", "preliminary_notified", "baselined", "final_notified"]
portfolio = [{"id": "L-01", "display_name": asset["display_name"], "ftl_area_ha": asset["ftl_area_ha"], "zone": "North Zone",
              "custody_state": "under_restoration", "overall_status": "amber", "open_events": len(open_events),
              "last_observation": AS_OF.date().isoformat(), "instrumented": True, "schematic_position": [0, 0]}]
rr = random.Random(7)
for i, (n, st) in enumerate(zip(names, states), start=2):
    portfolio.append({"id": f"L-{i:02d}", "display_name": f"{n} (fictitious)", "ftl_area_ha": round(rr.uniform(4, 60), 1),
                      "zone": rr.choice(["North Zone", "North Zone", "East Zone", "West Zone"]), "custody_state": st,
                      "overall_status": rr.choice(["green", "green", "amber", "red", "grey"]),
                      "open_events": rr.randint(0, 6),
                      "last_observation": (AS_OF.date() - timedelta(days=rr.randint(3, 120))).isoformat(),
                      "instrumented": False,
                      "schematic_position": [rr.randint(-4000, 4000), rr.randint(-3000, 3000)]})
portfolio_note = "Light records only. 'grey' = no observation in the last 90 days. Not instrumented."

# ---------------------------------------------------------------- write
out = {
    "meta": {
        "dataset": "Asset IQ prototype demo data", "version": "0.1", "generated_for": "AIQ-ARCH-001 v0.5 §7",
        "as_of": AS_OF.isoformat(timespec="minutes"), "period": [START.date().isoformat(), AS_OF.date().isoformat()],
        "fictitious": True,
        "disclaimer": "All names, places, records, figures and coordinates are synthetic and do not describe any real water body, authority or person.",
        "aiqube_tags": "Not populated. aiQube is not yet issued (AIQ-ARCH-001 OD-08).",
    },
    "authority": authority, "users": users, "asset": asset, "custody_history": custody_history,
    "geometry": geometry, "spatial_baseline": spatial_baseline,
    "departmental_records": departmental_records, "record_discrepancies": record_discrepancies,
    "sensor_devices": sensor_devices, "thresholds": thresholds, "sensor_gaps": sensor_gaps,
    "rainfall_daily": rain_daily, "sensor_readings": readings,
    "lab_reports": lab_reports, "lab_note": lab_note,
    "observation_passes": observation_passes, "satellite_series": satellite_series, "satellite_note": satellite_note,
    "restoration_works": works, "events": events,
    "field_captures": captures,
    "field_capture_summary": {"window": "final 30 days", "scheduled": len(captures), "completed": comp,
                              "completion_pct": round(comp / len(captures) * 100, 1)},
    "media_ledger": media, "compliance_targets": compliance_targets,
    "officer_view": officer_view, "portfolio": portfolio, "portfolio_note": portfolio_note,
}
with open("aiq_demo_data_v0.1.json", "w") as f:
    json.dump(out, f, indent=1)

# quick checks
print("FTL ha", ha(A_FTL), "| buffer ha", ha(A_BUF), "| water spread ha", ha(A_WS), "| fill m2", round(A_FILL))
print("readings", len(readings), "| events", len(events), "| captures", len(captures), comp, "| media", len(media))
print("progress", works["precomputed_progress"])
wq = [r for r in readings if r["device"] == "SN-WQ1"]
print("overdue", overdue, "| changed", changed, "| level now", cur)
for k in ("EV-04","EV-08","EV-19"): print(k, E[k]["detail"])
print("DO min", min(r["do_mg_l"] for r in wq), "at", min(wq, key=lambda r: r["do_mg_l"])["ts"],
      "| first <4:", next(r["ts"] for r in wq if r["do_mg_l"] < 4))
lv = [r["level_m"] for r in readings if r["device"] == "SN-LV1"]
print("level min/max", min(lv), max(lv))
