Asset IQ Prototype — Demo Data Set v0.1
Controlling reference: AIQ-ARCH-001 v0.5, Section 7
Files: `aiq_demo_data_v0.1.json` (data, about 170 KB) · `gen_aiq_demo_data.py` (generator)
As of: 15 Sep 2026, 18:00 · Period: 18 Jun – 15 Sep 2026 (90 days)
1. Rules this data set follows
Everything is fictitious. The lake, authority, people, contractor, laboratory, tribunal order and notification references are invented. No real water body, authority or person is described.
Coordinates are synthetic. Geometry uses a local metre grid (x east, y north, lake centre at 0,0). It is not latitude and longitude. The prototype map should be schematic, with no real map tiles, so the lake cannot be read as sitting on a real place.
Thresholds are illustrative. DO, pH, turbidity, BOD and level limits are placeholders, to be confirmed against the applicable standard for a real site.
aiQube tags are empty. `aiqube_tags` is `null` on every event until aiQube is issued (AIQ-ARCH-001 OD-08). Screens use zone, evidence source and custody state in plain language instead.
Progress is precomputed for display only. The simple weighted percentage in `restoration_works.precomputed_progress` stands in for the licensed computation, and is labelled as such.
Regenerate, don't hand-edit. Change the generator and re-run `python3 gen_aiq_demo_data.py`. The seed is fixed, so output is repeatable. Event text that quotes numbers is produced from the generated series, so the text and charts stay consistent.
2. What is in the file
Key	Contents
`meta`	Version, as-of date, period, disclaimer
`authority`, `users`	Demo Metro Lakes Authority; seven role-based users
`asset`	Lake L-01 "Sarovara Tank (fictitious)": 41.9 ha at FTL; six zones; current custody state
`custody_history`	Identified 2019 → preliminary notified 2023 → final notified 2025 → baselined 8 Jul 2026 → under restoration 20 Jul 2026
`geometry`	FTL line, 30 m buffer, current water spread, catchment, downstream area, bund, weir, sluice, three inlets, one change polygon
`spatial_baseline`	Accepted baseline SB-L01-v1; bathymetry (1,410 ML at FTL against 1,650 ML design, a 14.5% loss); versioned layers
`departmental_records`, `record_discrepancies`	Revenue, Irrigation and notification areas; RD-001 north-bank dispute awaiting ruling
`sensor_devices`, `sensor_readings`, `sensor_gaps`, `thresholds`	One water quality node and one level node; 877 readings every 3 hours; one 9-hour tamper gap
`rainfall_daily`	90 days of rainfall, including 203 mm over 25–28 Jul
`lab_reports`	Six reports; one BOD exceedance on 16 Aug
`observation_passes`, `satellite_series`	Drone passes on 29 Jun and 11 Aug; monthly water spread and weed cover
`restoration_works`	Work order with 7 quantity-based items; 13 measurement entries, each recorded by one officer and check-measured by another
`events`	The 20 fit-test events, placed on L-01, each with owner, deadline, consequence of inaction, status and evidence
`field_captures`, `field_capture_summary`	24 scheduled captures in the final 30 days; 21 completed (87.5%)
`media_ledger`	53 evidence items, each with timestamp, capturer, location and SHA-256 hash (synthetic)
`compliance_targets`	Tribunal quarterly report (draft ready), pollution board monthly return, funding programme MIS
`officer_view`	Precomputed content for screen 1: overall status, 8 indicators, changes this week, overdue items, decisions needed today
`portfolio`	L-01 plus nine lighter lakes (L-02 to L-10) for the portfolio view
3. Planted scenarios
Scenario	Where in the data	Screen	Proposal criterion
Sewage inflow detected before manual discovery. DO falls below 4 mg/L at 03:00 on 15 Aug; field check later that day finds a new outfall at Inlet 2; lab confirms BOD 18.5 mg/L next day	EV-04, EV-07, EV-05, LAB-0816, SN-WQ1 series	1, 2	3
Encroachment in the buffer zone. 488 m² (0.12 acre) of fresh fill found by the second drone pass; field-verified; notice drafted but unsigned and overdue	EV-01, CHG-001, DP-2, MA-DP1-N / MA-DP2-N	1, 2	3
Record conflict. Revenue and Irrigation disagree by up to 18 m on the north bank; escalated for a ruling due 30 Sep	RD-001, EV-14	6	7
Restoration progress traced to evidence. Reach 2 desilting complete (22,000 m³); fencing at 20% and behind programme; overall 40.5%	restoration_works, EV-12, EV-13, MB-01 to MB-13	4	4
False alarm correctly rejected. Level drop on 25 Aug turns out to be an authorised sluice release	EV-08	2	— (shows human verification, AD-A06)
Sensor tamper. Water quality node offline 03:00–12:00 on 7 Sep	EV-17, sensor_gaps	1	—
Tribunal report due. Draft generated from pilot data; review needed by 23 Sep for filing on 25 Sep; illustrative effort 38 hours manual against 5 hours to review	EV-16, CT-TRIB	5	2, 6
Field adoption. 21 of 24 scheduled captures done in the final 30 days	field_capture_summary	3	5
Officer's day. Amber overall; 4 overdue items (EV-01, EV-06, EV-07, EV-09); 3 decisions today	officer_view	1	1
4. Known simplifications
Sensor series are modelled, not measured. The diurnal oxygen cycle, rain response and anomaly shape are plausible but not calibrated.
Photos are placeholders. The media ledger holds identifiers and hashes, not images; the prototype should show labelled placeholder frames.
Evidence locations are random points around the lake, except where an event names a place.
Portfolio lakes have no series, geometry or events of their own. Their schematic positions are arbitrary.
The effort figures for criterion 6 are illustrative. The proposal requires the real baseline to be recorded by the authority at pilot start.
5. Open points
Confirm the thresholds and the compliance report format to show first (AIQ-ARCH-001 OD-06).
A practitioner, ideally from the survey partner, should review the events and figures for realism before any external demo.
When aiQube is issued, populate `aiqube_tags` and re-run.
