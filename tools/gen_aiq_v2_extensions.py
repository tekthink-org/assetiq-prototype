"""
Asset IQ prototype — demo data, v0.2 extensions.

Reads aiq_demo_data_v0.1.json (produced by gen_aiq_demo_data.py) and adds the
sections introduced for prototype 2.0:

    survey_parcels        revenue survey numbers, with geometry
    perimeter             boundary length, segment by segment, protection state
    encroachment_cases    case file per encroachment, keyed to a survey number
    change_detection      pass-to-pass comparison, including rejected candidates
    lifecycle             custody stages with the gate each one has to pass
    field_forms           the full set of field entry forms, with geo-fences
    beautification        candidate parcels for public amenity, outside FTL only
    public_view           what a public page may and may not show
    roles                 who sees what

Everything here is FICTITIOUS. Coordinates are a synthetic local metre grid.

    python3 gen_aiq_demo_data.py          # writes v0.1
    python3 gen_aiq_v2_extensions.py      # reads v0.1, writes v0.2
"""

import json, math, random, hashlib, os
from datetime import datetime, timedelta

random.seed(20260929)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "aiq_demo_data_v0.1.json")
OUT = os.path.join(HERE, "..", "data", "aiq_demo_data_v0.2.json")

D = json.load(open(SRC))
G = D["geometry"]
AS_OF = D["officer_view"]["as_of"][:10]
VILLAGE = "Sarovaram (fictitious village)"
MANDAL = "Demo Mandal"


# ---------------------------------------------------------------- geometry helpers
def area(poly):
    s = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def centroid(poly):
    return [round(sum(p[0] for p in poly[:-1]) / (len(poly) - 1), 1),
            round(sum(p[1] for p in poly[:-1]) / (len(poly) - 1), 1)]


def perim(poly):
    return sum(math.dist(a, b) for a, b in zip(poly, poly[1:]))


def ac(m2):
    return round(m2 / 4046.86, 2)


def scale(poly, f):
    return [[round(x * f, 1), round(y * f, 1)] for x, y in poly]


def ring_sector(inner, outer, i0, i1):
    """Parcel between two concentric rings, over vertex range i0..i1."""
    a = inner[i0:i1 + 1]
    b = outer[i0:i1 + 1][::-1]
    return [list(p) for p in a] + [list(p) for p in b] + [list(inner[i0])]


ftl = G["ftl_boundary"]
buf = G["buffer_outer_boundary"]
N = len(ftl) - 1
outer2 = scale(buf, 1.30)          # adjoining land, starting beyond the buffer


# ---------------------------------------------------------------- 1. survey parcels
# The lake bed itself is one government parcel. Around it, a ring of parcels:
# some government poramboke, some patta (privately held) land adjoining.
# Only the tank bed is classified as a water body. The ring parcels are either
# unassigned government land (poramboke) or privately held patta land.
GOVT = ("Government — poramboke", "Government of the State", "clear")
PATTA = ("Patta — private holding", None, "adjoining")
GOVT_RING = {0, 1, 3, 5, 6}          # survey 113, 114, 116, 118, 119
PATTA_RING = {2, 4, 7}               # survey 115, 117, 120

survey_parcels = [{
    "id": "SN-112",
    "survey_no": "112",
    "subdivision": None,
    "village": VILLAGE,
    "mandal": MANDAL,
    "classification": "Government — water body (Cheruvu)",
    "holder": "Government of the State",
    "extent_ac": ac(area(ftl)),
    "within_ftl_ac": ac(area(ftl)),
    "within_buffer_ac": 0.0,
    "status": "clear",
    "note": "The tank bed. Classified as water body in the village account; not assignable.",
    "polygon": [list(p) for p in ftl],
}]

# eight ring parcels around the lake
STEP = N // 8
names = ["113", "114", "115", "116", "117", "118", "119", "120"]
subdiv = [None, None, "2", None, "1", "3", None, None]
for k in range(8):
    i0, i1 = k * STEP, min((k + 1) * STEP, N)
    poly = ring_sector(buf, outer2, i0, i1)
    cls, holder, status = GOVT if k in GOVT_RING else PATTA

    survey_parcels.append({
        "id": "SN-" + names[k] + (("-" + subdiv[k]) if subdiv[k] else ""),
        "survey_no": names[k],
        "subdivision": subdiv[k],
        "village": VILLAGE,
        "mandal": MANDAL,
        "classification": cls,
        "holder": holder or f"Private holder {k + 1} (fictitious)",
        "extent_ac": ac(area(poly)),
        "within_ftl_ac": 0.0,
        "within_buffer_ac": 0.0,
        "adjoins_buffer": True,
        "status": status,
        "note": "",
        "polygon": poly,
    })

# Parcel status is derived from the case list further down, not set by hand, so
# the register and the cases cannot drift apart. Notes are set here.
CASE_NOTE = {
    "ENC-2026-001": ("Earth fill observed inside the buffer. No permission traced on the "
                     "departmental record."),
    "ENC-2026-002": "Foundation trench crossing the FTL line, stopped and back-filled 21 Jul 2026.",
    "ENC-2026-003": "Seven trees felled in the buffer. Complaint with the forest officer pending.",
}

survey_summary = {
    "village": VILLAGE,
    "mandal": MANDAL,
    "parcels": len(survey_parcels),
    "government_ac": round(sum(p["extent_ac"] for p in survey_parcels
                               if p["holder"].startswith("Government")), 2),
    "private_ac": round(sum(p["extent_ac"] for p in survey_parcels
                            if not p["holder"].startswith("Government")), 2),
    "parcels_adjoining_buffer": sum(1 for p in survey_parcels if p.get("adjoins_buffer")),
    "buffer_note": ("The 30 m buffer is a protection strip attached to the tank, not part of any "
                    "adjoining holding. Every ring parcel begins beyond it, which is why an "
                    "encroachment is always an extension from a holding into the buffer."),
    "note": ("Survey numbers, subdivisions, extents and holders are invented. "
             "In a live deployment these are read from the village revenue account "
             "and reconciled against the survey baseline."),
}


# ---------------------------------------------------------------- 2. perimeter
bund = next(s for s in G["structures"] if s["type"] == "bund")
bund_len = round(math.dist(bund["line"][0], bund["line"][1]))
total_perim = round(perim(ftl))

perimeter = {
    "total_m": total_perim,
    "bund_m": bund_len,
    "natural_bank_m": total_perim - bund_len,
    "fenced_m": 480,
    "fencing_sanctioned_m": 2400,
    "method": "Measured along the accepted FTL line of baseline SB-L01-v1.",
    "segments": [
        {"id": "P-01", "from_m": 0, "to_m": 520, "reach": "South — main bund",
         "type": "Engineered bund", "protection": "Stone pitching, upstream face",
         "condition": "Fair", "fenced": False,
         "issue": "Seepage at the toe, chainage 180–192 m (event EV-09)",
         "work_item": "RW-4"},
        {"id": "P-02", "from_m": 520, "to_m": 1030, "reach": "East bank",
         "type": "Natural bank", "protection": "None",
         "condition": "Fair", "fenced": False,
         "issue": "Foundation trench inside FTL in July, since removed (EV-02)",
         "work_item": "RW-5"},
        {"id": "P-03", "from_m": 1030, "to_m": 1510, "reach": "North bank",
         "type": "Natural bank", "protection": "Chain-link fencing, part complete",
         "condition": "At risk", "fenced": True,
         "issue": "Earth fill inside the buffer (EV-01); fencing 480 m of 2,400 m",
         "work_item": "RW-5"},
        {"id": "P-04", "from_m": 1510, "to_m": 1960, "reach": "North-west bank",
         "type": "Natural bank", "protection": "None",
         "condition": "At risk", "fenced": False,
         "issue": "Inlet 1 storm-water channel enters here; bank scoured",
         "work_item": None},
        {"id": "P-05", "from_m": 1960, "to_m": total_perim, "reach": "West bank",
         "type": "Natural bank", "protection": "None",
         "condition": "Fair", "fenced": False,
         "issue": "Trees felled in the buffer, complaint pending (EV-20)",
         "work_item": None},
    ],
    "gap_m": 0,
    "finding": ("The sanctioned fencing under RW-5 is 2,400 m against a measured perimeter of "
                "{TOTAL} m. On the present sanction the perimeter cannot be closed end to end, "
                "and the shortfall falls on the bund reach where fencing was assumed unnecessary. "
                "Worth settling before the works close."),
    "note": ("Segment boundaries, conditions and protection types are illustrative. "
             "Perimeter protection is what converts a notified boundary into a defended one."),
}
for s in perimeter["segments"]:
    s["length_m"] = s["to_m"] - s["from_m"]
perimeter["gap_m"] = perimeter["total_m"] - perimeter["fencing_sanctioned_m"]
perimeter["finding"] = perimeter["finding"].replace("{TOTAL}", f'{perimeter["total_m"]:,}')


# ---------------------------------------------------------------- position helpers
def bearing_name(pt):
    """Compass sector of a point about the lake centre, in plain words."""
    ang = math.degrees(math.atan2(pt[1], pt[0])) % 360     # 0 = east, anticlockwise
    for lo, hi, name in [(337.5, 360, "east"), (0, 22.5, "east"),
                         (22.5, 67.5, "north-east"), (67.5, 112.5, "north"),
                         (112.5, 157.5, "north-west"), (157.5, 202.5, "west"),
                         (202.5, 247.5, "south-west"), (247.5, 292.5, "south"),
                         (292.5, 337.5, "south-east")]:
        if lo <= ang < hi:
            return name
    return "east"


def inside(poly, pt):
    x, y = pt
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def parcel_at(pt):
    """The ring parcel containing a point; the tank bed is not a ring parcel."""
    for pc in survey_parcels:
        if pc["id"] == "SN-112":
            continue
        if inside(pc["polygon"], pt):
            return pc
    return None


def chainage_of(pt):
    """Distance along the FTL line, from chainage 0 at the west end of the bund."""
    origin = bund["line"][0]
    body = ftl[:-1]
    best = min(range(len(body)), key=lambda i: math.dist(body[i], origin))
    ring = body[best:] + body[:best]
    ring.append(ring[0])
    # nearest vertex to the point, then the distance run to it
    idx = min(range(len(ring) - 1), key=lambda i: math.dist(ring[i], pt))
    run = sum(math.dist(ring[i], ring[i + 1]) for i in range(idx))
    total_ring = sum(math.dist(ring[i], ring[i + 1]) for i in range(len(ring) - 1))
    return run / total_ring * total_perim


def segment_at(pt):
    ch = chainage_of(pt)
    for seg in perimeter["segments"]:
        if seg["from_m"] <= ch < seg["to_m"]:
            return seg["id"]
    return perimeter["segments"][-1]["id"]


# ---------------------------------------------------------------- 3. encroachment cases
def sha(tag):
    return hashlib.sha256(("AIQ-DEMO|" + tag).encode()).hexdigest()


encroachment_cases = [
    {
        "id": "ENC-2026-001",
        "location_point": centroid(G["change_polygons"][0]["polygon"]),   # the fill the drone found
        "survey_no": None, "parcel_id": None, "perimeter_segment": None,
        "zone": "Z-BUF",
        "type": "Earth fill",
        "area_m2": 488,
        "area_ac": 0.12,
        "inside_ftl": False,
        "inside_buffer": True,
        "detected_by": "Drone pass DP-2",
        "detected_on": "2026-08-11",
        "verified_on": "2026-08-12",
        "verified_by": "U-FA1",
        "event": "EV-01",
        "stage": "Notice drafted",
        "owner": "U-NO",
        "deadline": "2026-08-22",
        "permission_on_record": False,
        "evidence": ["MA-DP1-N", "MA-DP2-N", "MA-EV01"],
        "stages": [
            {"stage": "Detected", "on": "2026-08-11", "by": "Drone pass DP-2", "done": True},
            {"stage": "Verified on the ground", "on": "2026-08-12", "by": "S. Naidu, Field Assistant", "done": True},
            {"stage": "Record checked", "on": "2026-08-12", "by": "{SN} — no permission traced", "done": True},
            {"stage": "Notice drafted", "on": "2026-08-13", "by": "Awaiting Nodal Officer signature", "done": True},
            {"stage": "Notice served", "on": None, "by": None, "done": False},
            {"stage": "Removal", "on": None, "by": None, "done": False},
            {"stage": "Restored and closed", "on": None, "by": None, "done": False},
        ],
    },
    {
        "id": "ENC-2026-002",
        "location_point": [455, 40],               # east bank, at the field-channel inlet
        "survey_no": None, "parcel_id": None, "perimeter_segment": None,
        "zone": "Z-FTL",
        "type": "Foundation trench for a boundary wall, crossing the FTL line",
        "area_m2": 96,
        "area_ac": 0.02,
        "inside_ftl": True,
        "inside_buffer": False,
        "detected_by": "Field inspection",
        "detected_on": "2026-07-17",
        "verified_on": "2026-07-18",
        "verified_by": "U-AE",
        "event": "EV-02",
        "stage": "Closed",
        "owner": "U-NO",
        "deadline": "2026-07-22",
        "permission_on_record": False,
        "evidence": ["MA-EV02"],
        "stages": [
            {"stage": "Detected", "on": "2026-07-17", "by": "Field inspection, P. Latha", "done": True},
            {"stage": "Verified on the ground", "on": "2026-07-18", "by": "K. Prasad, Assistant Engineer", "done": True},
            {"stage": "Record checked", "on": "2026-07-18", "by": "{SN} is patta land adjoining; the trench crossed the FTL line", "done": True},
            {"stage": "Notice served", "on": "2026-07-19", "by": "Work stopped on site", "done": True},
            {"stage": "Removal", "on": "2026-07-21", "by": "Trench back-filled", "done": True},
            {"stage": "Restored and closed", "on": "2026-07-21", "by": "R. Varma, Nodal Officer", "done": True},
        ],
    },
    {
        "id": "ENC-2026-003",
        "location_point": [-300, -200],            # south-west buffer, where the trees stood
        "survey_no": None, "parcel_id": None, "perimeter_segment": None,
        "zone": "Z-BUF",
        "type": "Tree felling in the buffer",
        "area_m2": 0,
        "area_ac": 0.0,
        "trees": 7,
        "inside_ftl": False,
        "inside_buffer": True,
        "detected_by": "Citizen report",
        "detected_on": "2026-09-03",
        "verified_on": "2026-09-04",
        "verified_by": "U-FA2",
        "event": "EV-20",
        "stage": "Verified — complaint pending",
        "owner": "U-NO",
        "deadline": "2026-09-15",
        "permission_on_record": False,
        "evidence": ["MA-EV20"],
        "stages": [
            {"stage": "Detected", "on": "2026-09-03", "by": "Citizen report", "done": True},
            {"stage": "Verified on the ground", "on": "2026-09-04", "by": "P. Latha, Field Assistant", "done": True},
            {"stage": "Record checked", "on": "2026-09-04", "by": "{SN} — {CLASS}", "done": True},
            {"stage": "Complaint filed with the forest officer", "on": None, "by": None, "done": False},
            {"stage": "Replanting", "on": None, "by": None, "done": False},
            {"stage": "Restored and closed", "on": None, "by": None, "done": False},
        ],
    },
]
# The perimeter segment a case sits on, and the compass position of each parcel,
# are read from the geometry rather than typed in, so the map and the words agree.
PARCEL_BY_ID = {p["id"]: p for p in survey_parcels}
for c in encroachment_cases:
    pt = c["location_point"]
    pc = parcel_at(pt)
    if pc is None:                      # inside the FTL: use the nearest ring parcel
        pc = min((x for x in survey_parcels if x["id"] != "SN-112"),
                 key=lambda x: math.dist(centroid(x["polygon"]), pt))
    c["parcel_id"] = pc["id"]
    c["survey_no"] = pc["survey_no"] + ("/" + pc["subdivision"] if pc["subdivision"] else "")
    c["perimeter_segment"] = segment_at(pt)
    c["bank"] = bearing_name(pt) + " bank"
    govt = pc["holder"].startswith("Government")
    for st in c["stages"]:
        if st.get("by"):
            st["by"] = (st["by"].replace("{SN}", "Survey number " + c["survey_no"])
                                .replace("{CLASS}", "government poramboke" if govt else "patta land"))
for _p in survey_parcels:
    _p["position"] = bearing_name(centroid(_p["polygon"])) if _p["id"] != "SN-112" else "the tank bed"
for _c in encroachment_cases:
    _p = PARCEL_BY_ID[_c["parcel_id"]]
    _p["note"] = (_p["note"] + " " if _p["note"] else "") + CASE_NOTE[_c["id"]]
# state follows the cases: any open case marks the parcel, closed cases clear it
for _p in survey_parcels:
    _cs = [c for c in encroachment_cases if c["parcel_id"] == _p["id"]]
    if _cs:
        _p["status"] = ("encroachment recorded" if any(c["stage"] != "Closed" for c in _cs)
                        else "cleared — encroachment removed")

encroachment_summary = {
    "open": sum(1 for c in encroachment_cases if c["stage"] != "Closed"),
    "closed": sum(1 for c in encroachment_cases if c["stage"] == "Closed"),
    "area_open_ac": round(sum(c["area_ac"] for c in encroachment_cases if c["stage"] != "Closed"), 2),
    "area_recovered_ac": round(sum(c["area_ac"] for c in encroachment_cases if c["stage"] == "Closed"), 2),
    "inside_ftl_open": sum(1 for c in encroachment_cases if c["inside_ftl"] and c["stage"] != "Closed"),
    "note": "A case is opened only after a human has confirmed it on the ground.",
}


# ---------------------------------------------------------------- 4. change detection
change_detection = {
    "method": ("Each drone pass is compared against the accepted baseline and against the "
               "previous pass. Candidate areas of material deviation are raised for human "
               "review. No candidate becomes a case until a person confirms it in the field."),
    "not_built": ("A trained image classifier is not part of the pilot. Candidates here come "
                  "from geometric comparison and are reviewed by a person."),
    "passes": [
        {"id": "DP-1", "date": "2026-06-29", "role": "Baseline pass", "gsd_cm": 3, "area_ha": 78,
         "candidates": 0, "confirmed": 0, "rejected": 0},
        {"id": "DP-2", "date": "2026-08-11", "role": "Mid-pilot pass", "gsd_cm": 3, "area_ha": 78,
         "candidates": 3, "confirmed": 1, "rejected": 2},
    ],
    "candidates": [
        {"id": "CD-001", "pass": "DP-2", "zone": "Z-BUF", "survey_no": "115/2",
         "type": "New fill", "area_m2": 488, "elevation_change_m": 0.9,
         "raised_on": "2026-08-11", "review": "Confirmed on the ground 12 Aug",
         "outcome": "confirmed", "case": "ENC-2026-001", "event": "EV-01",
         "polygon_id": "CHG-001"},
        {"id": "CD-002", "pass": "DP-2", "zone": "Z-WS",
         "type": "Water edge moved", "area_m2": 14200, "elevation_change_m": None,
         "raised_on": "2026-08-11", "review": "Water spread rose after 203 mm rain, 25–28 Jul. Seasonal.",
         "outcome": "rejected", "case": None, "event": None, "polygon_id": None},
        {"id": "CD-003", "pass": "DP-2", "zone": "Z-CAT",
         "type": "Bare ground in the catchment", "area_m2": 3100, "elevation_change_m": None,
         "raised_on": "2026-08-11", "review": "Ploughed field outside the buffer. Not a boundary matter.",
         "outcome": "rejected", "case": None, "event": None, "polygon_id": None},
    ],
    "water_spread_series": D["satellite_series"],
    "next_pass_due": "2026-10-15",
}


# ---------------------------------------------------------------- 5. lifecycle
lifecycle = {
    "note": ("The custody state of a water body, and what has to be true before it can move "
             "to the next one. The state is a property of the asset; a restoration works "
             "project has its own separate stages."),
    "current": D["asset"]["custody_state"],
    "stages": [
        {"key": "identified", "name": "Identified",
         "meaning": "The water body is on a register. No settled boundary.",
         "gate": "An entry in the authority's water body register",
         "reached_on": "2019-03-12",
         "evidence": "Register entry (fictitious)"},
        {"key": "preliminary_notified", "name": "Preliminary notification",
         "meaning": "A draft FTL and buffer have been notified and objections invited.",
         "gate": "Preliminary notification issued and published",
         "reached_on": "2023-11-06",
         "evidence": "Notification PN/2023/117 (fictitious)"},
        {"key": "final_notified", "name": "Final notification",
         "meaning": "FTL and buffer are settled in law. Enforcement is possible.",
         "gate": "Objections disposed and final notification issued",
         "reached_on": "2025-08-21",
         "evidence": "Notification FN/2025/042 (fictitious)"},
        {"key": "baselined", "name": "Baseline accepted",
         "meaning": "A surveyed spatial baseline exists and the authority has accepted it.",
         "gate": "Survey package accepted by the nodal officer",
         "reached_on": "2026-07-08",
         "evidence": "Baseline SB-L01-v1"},
        {"key": "under_restoration", "name": "Under restoration",
         "meaning": "Sanctioned works are in progress against the baseline.",
         "gate": "Work order issued and first measurement recorded",
         "reached_on": "2026-07-20",
         "evidence": "Work order WO-DMLA-2026-031"},
        {"key": "protected_monitored", "name": "Protected and monitored",
         "meaning": "Works complete, perimeter defended, continuous observation in place.",
         "gate": "Works closed, perimeter protected end to end, no open encroachment case",
         "reached_on": None,
         "evidence": None,
         "blockers": [
             "Restoration works at 40.5%; three items not started",
             "Perimeter fenced for 480 m of 2,400 m sanctioned",
             "One encroachment case open (ENC-2026-001)",
             "One boundary record dispute awaiting a ruling (RD-001)",
         ]},
    ],
}


# ---------------------------------------------------------------- 6. field forms
field_forms = [
    {
        "id": "F-BANK", "name": "Weekly bank walk", "short": "Bank walk",
        "purpose": "Standing check of the boundary, banks and inlets.",
        "frequency": "Weekly", "role": "Field Assistant", "minutes": 2,
        "geofence": {"zone": "Z-BUF", "label": "Within the buffer zone", "tolerance_m": 25},
        "questions": [
            {"k": "new_construction_seen", "q": "Any new construction or fill inside the boundary?",
             "type": "yes_no", "photo_on": "yes", "raises": "Boundary integrity"},
            {"k": "debris_seen", "q": "Any debris or waste dumped on the bank?",
             "type": "yes_no", "photo_on": "yes", "raises": "Pollution load"},
            {"k": "inlet_flow_normal", "q": "Is the flow at Inlet 2 normal?",
             "type": "yes_no", "photo_on": "no", "raises": "Pollution load"},
            {"k": "bund_wet_patch", "q": "Any wet patch or seepage at the bund?",
             "type": "yes_no", "photo_on": "yes", "raises": "Structures"},
        ],
    },
    {
        "id": "F-INLET", "name": "Inlet and outlet inspection", "short": "Inlet check",
        "purpose": "Condition and flow at each inlet, outlet and structure.",
        "frequency": "Fortnightly", "role": "Field Assistant", "minutes": 4,
        "geofence": {"zone": "Z-STR", "label": "At the structure, within 30 m", "tolerance_m": 30},
        "questions": [
            {"k": "structure", "q": "Which structure?", "type": "choice",
             "options": ["Inlet 1", "Inlet 2", "Inlet 3", "Sluice", "Surplus weir"], "photo_on": "always"},
            {"k": "flowing", "q": "Is it flowing?", "type": "yes_no", "photo_on": "yes", "raises": "Water spread and storage"},
            {"k": "colour_odour", "q": "Any unusual colour or odour?", "type": "yes_no", "photo_on": "yes", "raises": "Pollution load"},
            {"k": "blocked", "q": "Is the mouth blocked by weed or waste?", "type": "yes_no", "photo_on": "yes", "raises": "Flood function"},
            {"k": "gate_works", "q": "Does the gate operate?", "type": "yes_no", "photo_on": "no", "raises": "Structures"},
        ],
    },
    {
        "id": "F-ENC", "name": "Encroachment report", "short": "Encroachment",
        "purpose": "Raise a suspected encroachment with the evidence an officer needs to act.",
        "frequency": "On sighting", "role": "Field Assistant or officer", "minutes": 3,
        "geofence": {"zone": "Z-BUF", "label": "At the location, inside FTL or buffer", "tolerance_m": 10},
        "questions": [
            {"k": "what", "q": "What has been put up?", "type": "choice",
             "options": ["Earth fill", "Boundary wall or fence", "Structure or shed",
                         "Road or approach", "Plantation", "Other"], "photo_on": "always"},
            {"k": "inside", "q": "Is it inside the FTL line?", "type": "yes_no", "photo_on": "always", "raises": "Boundary integrity"},
            {"k": "extent", "q": "Roughly how large?", "type": "choice",
             "options": ["Under 100 m²", "100–500 m²", "500–2,000 m²", "Over 2,000 m²"], "photo_on": "no"},
            {"k": "active", "q": "Is work going on now?", "type": "yes_no", "photo_on": "yes", "raises": "Boundary integrity"},
            {"k": "survey_known", "q": "Is the survey number known on site?", "type": "yes_no", "photo_on": "no"},
        ],
    },
    {
        "id": "F-MB", "name": "Measurement entry", "short": "Measurement",
        "purpose": "Record an executed quantity against a sanctioned work item.",
        "frequency": "On execution", "role": "Assistant Engineer", "minutes": 5,
        "geofence": {"zone": "Z-WS", "label": "At the reach being measured", "tolerance_m": 50},
        "second_identity": True,
        "questions": [
            {"k": "item", "q": "Which work item?", "type": "choice",
             "options": ["RW-1 Desilting reach 1", "RW-2 Desilting reach 2", "RW-3 Desilting reach 3",
                         "RW-4 Bund strengthening", "RW-5 Fencing", "RW-6 Sewage diversion",
                         "RW-7 Weed removal"], "photo_on": "always"},
            {"k": "qty", "q": "Quantity executed since the last entry", "type": "number", "photo_on": "always"},
            {"k": "method", "q": "How was it measured?", "type": "choice",
             "options": ["Tape and level", "Truck count", "Chainage", "Area marked"], "photo_on": "no"},
            {"k": "check_officer", "q": "Who will check-measure?", "type": "choice",
             "options": ["M. Rao, Executive Engineer"], "photo_on": "no"},
        ],
    },
    {
        "id": "F-WQ", "name": "Water sample collection", "short": "Water sample",
        "purpose": "Record a sample drawn for laboratory testing, tied to its point.",
        "frequency": "Fortnightly", "role": "Field Assistant", "minutes": 3,
        "geofence": {"zone": "Z-WS", "label": "At the sampling point, within 15 m", "tolerance_m": 15},
        "questions": [
            {"k": "point", "q": "Which sampling point?", "type": "choice",
             "options": ["SP-1 Inlet 1", "SP-2 Inlet 2", "SP-3 Outlet", "SP-4 Centre"], "photo_on": "always"},
            {"k": "appearance", "q": "Is the water clear?", "type": "yes_no", "photo_on": "no", "raises": "Water quality"},
            {"k": "scum", "q": "Any scum, froth or bloom at the point?", "type": "yes_no", "photo_on": "yes", "raises": "Ecology"},
            {"k": "bottles", "q": "How many bottles drawn?", "type": "number", "photo_on": "no"},
        ],
    },
    {
        "id": "F-BUND", "name": "Bund and perimeter check", "short": "Bund check",
        "purpose": "Condition of the perimeter, segment by segment.",
        "frequency": "Monthly, and after heavy rain", "role": "Assistant Engineer", "minutes": 6,
        "geofence": {"zone": "Z-STR", "label": "Along the segment being walked", "tolerance_m": 40},
        "questions": [
            {"k": "segment", "q": "Which segment?", "type": "choice",
             "options": ["P-01 South bund", "P-02 East bank", "P-03 North bank",
                         "P-04 North-west bank", "P-05 West bank"], "photo_on": "always"},
            {"k": "seepage", "q": "Any seepage at the toe?", "type": "yes_no", "photo_on": "yes", "raises": "Structures"},
            {"k": "erosion", "q": "Any erosion or slip on the face?", "type": "yes_no", "photo_on": "yes", "raises": "Structures"},
            {"k": "fence_intact", "q": "Is the fencing intact along this segment?", "type": "yes_no", "photo_on": "no", "raises": "Boundary integrity"},
            {"k": "access_blocked", "q": "Is any unauthorised access track visible?", "type": "yes_no", "photo_on": "yes", "raises": "Boundary integrity"},
        ],
    },
]

geofence_note = ("Every entry is accepted only when the device reports a position inside the "
                 "fence for that form. An entry from outside is held and flagged for the "
                 "officer rather than silently discarded, because a genuine reason may exist.")

# a small record of fence outcomes over the pilot, for the adoption panel
geofence_log = {
    "window": "final 30 days",
    "accepted": 21,
    "held_outside_fence": 2,
    "no_fix": 1,
    "examples": [
        {"id": "FC-014", "form": "F-BANK", "at": "2026-09-05T10:20",
         "distance_m": 310, "outcome": "held", "reason": "Recorded from the approach road, outside the buffer fence",
         "resolution": "Officer accepted after the assistant re-walked the bank"},
        {"id": "FC-019", "form": "F-INLET", "at": "2026-09-10T15:05",
         "distance_m": 64, "outcome": "held", "reason": "34 m beyond the structure fence",
         "resolution": "Rejected; re-captured at the inlet the same day"},
        {"id": "FC-022", "form": "F-BANK", "at": "2026-09-12T10:15",
         "distance_m": None, "outcome": "no fix", "reason": "No satellite fix under tree cover",
         "resolution": "Queued with last known position; officer notified"},
    ],
}


# ---------------------------------------------------------------- 7. beautification
# Deliberately restricted to land OUTSIDE the FTL and outside the notified buffer.
beautification = {
    "scope": ("Amenity planning is considered only on land outside the FTL line and outside the "
              "notified buffer. Nothing inside either is a candidate, whatever its condition or "
              "ownership."),
    "rule": "Outside FTL, outside buffer, government-held, no open encroachment case, no works conflict, access without crossing the buffer.",
    "decision": "Suitability shown here is an input to a decision the authority takes; it is not a sanction.",
    "criteria": [
        {"k": "outside_ftl", "label": "Outside the FTL line", "short": "Outside FTL",
         "why": "Nothing may be built inside the water spread"},
        {"k": "outside_buffer", "label": "Outside the notified buffer", "short": "Outside buffer",
         "why": "The buffer is a protection strip, not a development zone"},
        {"k": "government_held", "label": "Government-held", "short": "Government",
         "why": "Private land would need acquisition before anything else"},
        {"k": "no_case", "label": "No open encroachment case", "short": "No open case",
         "why": "Enforcement is settled first, amenity after"},
        {"k": "no_works_conflict", "label": "No conflict with sanctioned works", "short": "No works clash",
         "why": "Bund, fencing and diversion take precedence"},
        {"k": "access", "label": "Access without crossing the buffer", "short": "Access",
         "why": "Footfall must not be routed through the protection zone"},
    ],
    "candidates": [],
    "caution": ("A screen that identifies land near a lake as suitable for development sits close to "
                "the thing this platform exists to prevent. The rule above is the safeguard: the FTL "
                "and the buffer are never candidates, and every exclusion stays visible rather than "
                "being filtered out of sight."),
}

# Parcels along the fencing reaches conflict with sanctioned works (RW-5).
WORKS_CONFLICT_SEGMENTS = {seg["id"] for seg in perimeter["segments"] if seg.get("work_item") == "RW-5"}
# Reaching a parcel without crossing the buffer needs an existing road; the bund
# road serves the southern reaches only.
ACCESS_OK = {"south", "south-west", "south-east", "east"}

def assess(pc):
    open_case = any(c["parcel_id"] == pc["id"] and c["stage"] != "Closed" for c in encroachment_cases)
    govt = pc["holder"].startswith("Government")
    is_bed = pc["id"] == "SN-112"
    seg = segment_at(centroid(pc["polygon"]))
    checks = {
        "outside_ftl": not is_bed,
        "outside_buffer": not is_bed,
        "government_held": govt,
        "no_case": not open_case,
        "no_works_conflict": seg not in WORKS_CONFLICT_SEGMENTS,
        "access": pc.get("position") in ACCESS_OK or is_bed is False and pc.get("position") in ACCESS_OK,
    }
    if not checks["outside_ftl"] or not checks["outside_buffer"]:
        verdict = "Not a candidate"
    elif not checks["no_case"]:
        verdict = "Blocked until the case closes"
    elif not checks["government_held"]:
        verdict = "Would need acquisition"
    elif not checks["no_works_conflict"] or not checks["access"]:
        verdict = "Blocked for now"
    else:
        verdict = "Meets every check"
    return checks, verdict, seg

# ---------------------------------------------------------------- 8. roles and public view
roles = [
    {"key": "officer", "name": "Officer", "who": "Nodal officer, HYDRA",
     "sees": "Everything for the sites in their charge, including enforcement detail.",
     "nav": ["overview", "alerts", "change", "boundary", "survey", "perimeter", "lifecycle",
             "encroachment", "works", "field", "compliance", "amenity"]},
    {"key": "field", "name": "Field", "who": "Field assistant on a phone",
     "sees": "Assigned captures and the forms. No enforcement decisions, no compliance drafts.",
     "nav": ["field", "overview"]},
    {"key": "department", "name": "Department", "who": "Revenue, Irrigation, HMDA, GHMC, Forest",
     "sees": "The agreed boundary, survey position, record differences and what is asked of them. "
             "No internal alerts and no draft notices.",
     "nav": ["department", "boundary", "survey", "lifecycle", "compliance"]},
    {"key": "public", "name": "Public", "who": "Citizen or petitioner",
     "sees": "Published status, restoration progress and how to report a problem. Nothing that "
             "would identify a person or prejudice a pending case.",
     "nav": ["public"]},
]

public_view = {
    "published": [
        {"field": "Lake name, area at FTL and custody state", "why": "Already a matter of public notification"},
        {"field": "Water spread this month and the trend", "why": "Observable from any bank"},
        {"field": "Restoration progress, overall percentage", "why": "Public money, public work"},
        {"field": "Water quality band — good, fair or poor", "why": "A band, not a raw reading, avoids misreading a single value"},
        {"field": "Count of encroachment cases open and closed", "why": "Aggregate accountability"},
        {"field": "How to report a problem", "why": "The public are an observation channel"},
    ],
    "withheld": [
        {"field": "Location or survey number of any encroachment", "why": "Identifies a private party in a pending matter"},
        {"field": "Names of holders, complainants or field staff", "why": "Personal information"},
        {"field": "Draft notices and internal correspondence", "why": "Pre-decisional"},
        {"field": "Unverified alerts", "why": "An unconfirmed reading is not a finding"},
        {"field": "Raw sensor and evidence files", "why": "Belongs with the custodian, not the public page"},
    ],
    "decision_note": ("What a public page shows is the authority's decision, not the "
                      "platform's. This screen shows one defensible default so that the "
                      "conversation starts from something concrete."),
    "citizen_reports": {"received": 14, "verified": 6, "acted_on": 4, "window": "pilot period"},
    "band": "Fair",
    "band_basis": "Median dissolved oxygen over the last 30 days, against the working threshold.",
}


# ---------------------------------------------------------------- 9. department asks
department_view = {
    "note": "What each department holds, what it is being asked for, and by when.",
    "departments": [
        {"name": "Revenue", "holds": "Village map and survey records, 1998 vintage",
         "record": "DR-REV", "area_ha": 44.1,
         "asked": "Ruling on the north-bank FTL line, discrepancy RD-001",
         "due": "2026-09-30", "status": "Awaiting ruling", "contact": "Tahsildar (fictitious)"},
        {"name": "Irrigation", "holds": "Tank register and design storage, 2011 vintage",
         "record": "DR-IRR", "area_ha": 41.6,
         "asked": "Confirmation of design storage against the bathymetric survey",
         "due": "2026-10-10", "status": "Noted", "contact": "Executive Engineer (fictitious)"},
        {"name": "Urban development authority", "holds": "Final FTL notification, 2025",
         "record": "DR-NOT", "area_ha": 42.0,
         "asked": "Confirmation that the accepted baseline follows the final notification",
         "due": "2026-10-05", "status": "Confirmed 12 Sept", "contact": "Planning Officer (fictitious)"},
        {"name": "Municipal body", "holds": "Storm-water and sewerage network records",
         "record": None, "area_ha": None,
         "asked": "Source of the untreated inflow at Inlet 2, and the diversion approval",
         "due": "2026-09-25", "status": "Overdue", "contact": "Superintending Engineer (fictitious)"},
        {"name": "Forest", "holds": "Tree cover and felling permissions",
         "record": None, "area_ha": None,
         "asked": "Action on seven trees felled in the buffer on survey 119",
         "due": "2026-09-15", "status": "Overdue", "contact": "Range Officer (fictitious)"},
    ],
}


# ---------------------------------------------------------------- amenity candidates
AMEN_NOTE = {
    "Meets every check": "Reachable from the bund road without routing footfall through the buffer.",
    "Blocked until the case closes": "An open encroachment case runs on this parcel. Enforcement is settled first.",
    "Blocked for now": "Sanctioned fencing runs along this reach, or the only approach crosses the buffer.",
    "Would need acquisition": "Privately held. Listed so the authority can consider acquisition on its merits.",
    "Not a candidate": "Inside the FTL line. Listed so the exclusion is on the record rather than invisible.",
}
_n = 0
for _p in survey_parcels:
    _checks, _verdict, _seg = assess(_p)
    _n += 1
    beautification["candidates"].append({
        "id": "AM-%02d" % _n,
        "survey_no": _p["survey_no"] + ("/" + _p["subdivision"] if _p["subdivision"] else ""),
        "parcel_id": _p["id"],
        "extent_ac": _p["extent_ac"],
        "location": ("The tank bed itself" if _p["id"] == "SN-112"
                     else _p["position"].capitalize() + " of the lake, beyond the buffer"),
        "perimeter_segment": _seg,
        "checks": _checks,
        "verdict": _verdict,
        "note": AMEN_NOTE[_verdict],
    })
beautification["summary"] = {
    v: sum(1 for c in beautification["candidates"] if c["verdict"] == v)
    for v in ["Meets every check", "Blocked for now", "Blocked until the case closes",
              "Would need acquisition", "Not a candidate"]
}

# ---------------------------------------------------------------- assemble
D["meta"]["version"] = "0.2"
D["meta"]["v2_note"] = ("v0.2 adds survey parcels, perimeter, encroachment cases, change "
                        "detection, lifecycle gates, the full field form set with geo-fences, "
                        "amenity candidates, roles and the public view. Still entirely fictitious.")
D["survey_parcels"] = survey_parcels
D["survey_summary"] = survey_summary
D["perimeter"] = perimeter
D["encroachment_cases"] = encroachment_cases
D["encroachment_summary"] = encroachment_summary
D["change_detection"] = change_detection
D["lifecycle"] = lifecycle
D["field_forms"] = field_forms
D["geofence_note"] = geofence_note
D["geofence_log"] = geofence_log
D["beautification"] = beautification
D["roles"] = roles
D["public_view"] = public_view
D["department_view"] = department_view


# ---------------------------------------------------------------- decisions waiting on the officer
# The lake view prints these as they stand, so each one has to say what the act
# is, what it is about, and what is holding. Only the verb is editorial; the
# particulars are read off the case, the record dispute or the compliance target
# behind the event, so they cannot drift from the screens that show the same
# thing in full. Dates stay as ISO strings — the view formats them.
DECISION_ACT = {
    "EV-01": "Sign and serve the encroachment notice",
    "EV-16": "Approve the tribunal compliance draft for filing",
    "EV-14": "Rule on which FTL record governs the north bank",
}


def _late_days(due):
    if not due:
        return 0
    d = (datetime.fromisoformat(AS_OF) - datetime.fromisoformat(due)).days
    return d if d > 0 else 0


def _decision(item):
    ev_id = item["event"]
    e = next(x for x in D["events"] if x["id"] == ev_id)
    out = {"event": ev_id, "owner": item["owner"],
           "decision": DECISION_ACT.get(ev_id, item["decision"]),
           "due": e.get("deadline"), "link": None, "link_label": None,
           "about": None, "holding_label": None, "holding_on": None, "holding_note": None}

    case = next((c for c in encroachment_cases if c.get("event") == ev_id), None)
    disc = next((r for r in D["record_discrepancies"]
                 if r["id"] in (e.get("detail") or "") and r["status"] == "escalated_for_ruling"), None)
    tgt = next((c for c in D["compliance_targets"] if c["id"] == e.get("compliance_target")), None)

    if case:
        parcel = next((p for p in survey_parcels if p["id"] == case["parcel_id"]), None)
        held = "government land" if (parcel or {}).get("holder", "").startswith("Government") \
            else "privately held land"
        drafted = next((s for s in case["stages"] if s["done"] and s["stage"].endswith("drafted")), None)
        out["about"] = (f"Survey {case['survey_no']} — {case['area_ac']} ac of {case['type'].lower()} "
                        f"{'inside the FTL line' if case['inside_ftl'] else 'inside the buffer'}, "
                        f"{case['bank']}, on {held}")
        out["holding_label"] = "Notice drafted"
        out["holding_on"] = (drafted or {}).get("on")
        out["holding_note"] = "it has no effect until a person with authority signs it"
        out["link"] = f"encroachment.html#{case['id']}"
        out["link_label"] = f"open case {case['id']}"
    elif tgt:
        authority = tgt["authority"].split(" (")[0]
        out["about"] = (f"{tgt['report']} to the {authority} — {len(tgt['sections'])} sections "
                        f"assembled from the pilot record")
        out["holding_label"] = "Draft generated"
        out["holding_on"] = e["raised_at"][:10]
        out["holding_note"] = "nothing is filed until it is approved"
        out["link"] = "compliance.html"
        out["link_label"] = "open the draft"
    elif disc:
        out["about"] = f"{disc['id']}: {disc['subject']} — {disc['difference'].lower()}"
        out["holding_label"] = "Referred for a ruling"
        out["holding_on"] = disc["raised_on"]
        out["holding_note"] = "the authority decides which record governs; the platform does not resolve it"
        out["due"] = disc.get("ruling_due") or out["due"]
        out["link"] = "baseline.html"
        out["link_label"] = f"open {disc['id']}"

    out["days_late"] = _late_days(out["due"])
    return out


D["officer_view"]["needs_decision_today"] = [
    _decision(x) for x in D["officer_view"]["needs_decision_today"]
]

# link each event to its monitoring parameter group, for the alerts screen
PARAM_GROUP = {
    "boundary_integrity": "boundary",
    "legal_status": "boundary",
    "water_quality": "water_quality",
    "pollution_load": "water_quality",
    "ecology": "ecology",
    "siltation": "storage",
    "water_spread_storage": "storage",
    "flood_function": "flood",
    "structures": "structures",
    "monitoring_equipment": "monitoring",
    "works_progress": "works",
    "obligation": "compliance",
}
for e in D["events"]:
    e["parameter"] = PARAM_GROUP.get(e["condition"], "other")

D["parameters"] = [
    {"key": "boundary", "name": "Boundary and encroachment",
     "what": "Fill, construction, fencing or record disputes affecting the FTL line or the buffer",
     "sources": ["Drone", "Field inspection", "Citizen report", "Departmental record"],
     "screen": "encroachment.html"},
    {"key": "water_quality", "name": "Water quality and inflow",
     "what": "Dissolved oxygen, pH, turbidity, conductivity, laboratory BOD, and the inflows that drive them",
     "sources": ["In-situ sensor", "Laboratory", "Field inspection"], "screen": None},
    {"key": "ecology", "name": "Ecology and weed cover",
     "what": "Bloom, weed and hyacinth spread, tree cover in the buffer",
     "sources": ["Satellite", "Drone", "Field inspection"], "screen": None},
    {"key": "storage", "name": "Water spread and storage",
     "what": "Level, water spread area, storage against design, siltation",
     "sources": ["In-situ sensor", "Satellite", "Spatial survey"], "screen": None},
    {"key": "flood", "name": "Flood function",
     "what": "Available cushion, outlet capacity, behaviour under rainfall",
     "sources": ["In-situ sensor", "Field inspection"], "screen": None},
    {"key": "structures", "name": "Bund and structures",
     "what": "Bund condition, seepage, sluice and weir operation, perimeter protection",
     "sources": ["Field inspection"], "screen": "perimeter.html"},
    {"key": "monitoring", "name": "Monitoring equipment",
     "what": "Sensor health, tamper, gaps in the record",
     "sources": ["In-situ sensor"], "screen": None},
    {"key": "works", "name": "Restoration works",
     "what": "Measured progress against sanctioned quantity, programme slippage",
     "sources": ["Field inspection"], "screen": "works.html"},
    {"key": "compliance", "name": "Statutory obligations",
     "what": "Submissions due, orders and directions with a deadline",
     "sources": ["Departmental record"], "screen": "compliance.html"},
]

with open(OUT, "w") as f:
    json.dump(D, f, indent=1)

# ---------------------------------------------------------------- checks
print("parcels", len(survey_parcels), "| gov ac", survey_summary["government_ac"],
      "| private ac", survey_summary["private_ac"])
print("perimeter", perimeter["total_m"], "m | bund", perimeter["bund_m"],
      "| segments", len(perimeter["segments"]),
      "| sum", sum(s["length_m"] for s in perimeter["segments"]))
print("encroachment", encroachment_summary)
print("change candidates", len(change_detection["candidates"]),
      "confirmed", sum(1 for c in change_detection["candidates"] if c["outcome"] == "confirmed"))
print("forms", [f["id"] for f in field_forms])
print("params", {p: sum(1 for e in D["events"] if e["parameter"] == p)
                 for p in sorted(set(e["parameter"] for e in D["events"]))})
print("amenity", beautification["summary"])
print("wrote", os.path.relpath(OUT, HERE), os.path.getsize(OUT), "bytes")
