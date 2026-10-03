# Asset IQ Prototype — Demo Data Set v0.2

**Controlling reference:** AIQ-ARCH-001, prototype scope
**Files:** `data/aiq_demo_data_v0.2.json` (in use) · `data/aiq_demo_data_v0.1.json` (base) ·
`tools/gen_aiq_demo_data.py` · `tools/gen_aiq_v2_extensions.py`
**As of:** 15 Sep 2026, 18:00 · **Period:** 18 Jun – 15 Sep 2026 (90 days)

## 1. Rules this data set follows

- **Everything is fictitious.** The lake, authority, village, survey numbers, people, contractor,
  laboratory, tribunal order and notification references are invented. No real water body, parcel,
  authority or person is described.
- **Coordinates are synthetic.** A local metre grid with a false origin at 10,000 E / 20,000 N. Not
  latitude and longitude. The prototype map is schematic, so the lake cannot be read as sitting on a
  real place.
- **Thresholds are illustrative.** Dissolved oxygen, pH, turbidity, BOD and level limits are
  placeholders, to be confirmed against the applicable standard for a real site.
- **Derive, do not assert.** Where one fact follows from another, v0.2 computes it. See section 4.
- **Regenerate, do not hand-edit.** Run the two generators in order. The seeds are fixed.

## 2. What v0.2 adds to v0.1

| Key | Contents |
|---|---|
| `survey_parcels` | Nine revenue parcels with geometry: the tank bed (survey 112) plus eight ring parcels beginning **beyond** the notified buffer. Classification, holder, extent, position and state. |
| `survey_summary` | Village totals, government against private, parcels adjoining the buffer |
| `perimeter` | 2,526 m along the FTL line in five segments, each with type, protection, condition and the sanctioned work covering it. Includes the fencing shortfall finding. |
| `encroachment_cases` | Three cases, each with a real location point, seven stages, evidence and the alert it came from |
| `change_detection` | Two passes, three candidates from the second, one confirmed and two rejected with reasons |
| `lifecycle` | Six custody stages with the gate on each, and the blockers on the one not reached |
| `field_forms` | Six forms with question sets, answer types, photograph rules, frequency, role and geo-fence |
| `geofence_log` | Accepted, held and no-fix outcomes over the final 30 days, with what happened next |
| `beautification` | Six checks applied to all nine parcels, with a verdict computed for each |
| `roles`, `public_view`, `department_view` | Who sees what; published against withheld; what each department holds and owes |
| `parameters` | Nine monitoring parameters, each with what it measures and its sources. Every event is tagged to one. |

## 3. The scenarios

| Scenario | Where | Screen |
|---|---|---|
| Sewage inflow detected before manual discovery | Dissolved oxygen falls below 4 mg/L at 03:00 on 15 Aug; field check that day finds a new outfall at Inlet 2; lab confirms BOD 18.5 mg/L next day | Alerts → water quality |
| Encroachment from detection to notice | Drone pass DP-2 flags 488 m² of fill; verified next day; survey number checked; notice drafted but unsigned and overdue | Encroachment, change detection |
| A rejected change candidate | Water edge moved 14,200 m² after 203 mm of rain — seasonal, rejected, kept on record | Change detection |
| A dismissed alert | Level drop on 25 Aug turns out to be an authorised sluice release | Alerts → flood function |
| A boundary record dispute | Revenue 44.1 ha, Irrigation 41.6 ha, notification 42.0 ha, survey 41.93 ha; north-bank difference referred for a ruling | Boundary, department view |
| A perimeter that cannot be closed | Sanctioned fencing 2,400 m against a measured perimeter of 2,526 m | Perimeter |
| A capture from the wrong place | Two entries held for being outside the fence; one with no satellite fix | Field capture |
| Amenity land, and what is excluded | One parcel clear on all six checks; the tank bed, two parcels with open cases and three private parcels all excluded, visibly | Amenity |

## 4. What is derived rather than typed

This is the main change from v0.1, and the reason not to edit the JSON by hand.

- **A case's survey number** comes from a point-in-polygon test of its location against the parcel ring.
- **A case's perimeter segment** comes from the chainage of that same point, measured from chainage 0 at
  the western end of the bund.
- **A case's bank** ("north bank") is the compass bearing of the point about the lake centre.
- **A parcel's state** follows the cases on it: any open case marks it, only closed cases clear it.
- **A parcel's position** is the bearing of its centroid.
- **Every amenity check and verdict** is computed from parcel classification, holder, open cases, the
  works covering that perimeter segment and the approach route.
- **Evidence locations** are anchored to the place the event describes.
- **Event text quoting a figure** is written from the generated series, so the words and the charts agree.
- **The decision items on the lake view** (`officer_view.needs_decision_today`) carry an editorial verb
  only. The subject, the extent, the land classification, what is holding the decision, the due date and
  the days overdue are read off the encroachment case, the record dispute or the compliance target behind
  the event, so a decision item cannot say something the case file contradicts.

Three inconsistencies were found and fixed this way during the build: a parcel carrying an open case that
still read "clear", two cases citing a perimeter segment on the wrong side of the lake, and an amenity
test that no parcel could pass because the parcel ring overlapped the buffer.

## 5. Known simplifications

- Sensor series are modelled, not measured. The diurnal cycle, rain response and anomaly shape are
  plausible but not calibrated.
- Photographs are placeholders. The ledger holds identifiers, hashes, capturers, times and places; there
  are no images.
- Parcel geometry is a regular ring. Real survey parcels are irregular and rarely concentric.
- The check-measurement interval is a uniform two days. Real measurement books contain queried
  quantities, reductions and re-measurements; none are modelled.
- Portfolio lakes have no geometry, series or events of their own.

## 6. Open points

- Confirm thresholds and the compliance report format to build against first.
- A practitioner should review the events, parcels and figures for realism before any external demo —
  particularly the survey classification vocabulary and the perimeter condition language.
- When a spatial partner supplies its own symbology, restyle the map to match.
