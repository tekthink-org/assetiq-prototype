# AssetIQ — prototype 2.0

Interactive wireframe for **AssetIQ**, an asset intelligence platform for public assets held in custody
by a government body: lakes, tanks, nalas, storm drains and canals.

It answers one question: **is this asset intact, in the condition we believe, and protected — and if not,
what needs a decision today?**

> **All data here is fictitious.** The lake, authority, people, contractor, laboratory, survey numbers,
> village and order references are invented, and the coordinates are a synthetic local grid, not real
> locations. Nothing in this repository describes a real water body, authority, parcel or person.

## What changed in 2.0

Built against the consortium review of prototype 1.0.

| # | Point raised | What was done |
|---|---|---|
| 1 | It looks like a website, not an application | Application shell: fixed left navigation grouped by task, a top bar carrying the asset and the date, and a role switcher. No page is a dead end. |
| 2 | Hyperlinked options should be tiles | The home screen is tiles, one per monitoring parameter and one per area of work, each carrying its own count and state. |
| 3 | Split alerts by monitoring parameter; make labels self-explanatory | `alerts.html` is parameter-first: nine parameters, each with what it measures, where the readings come from, its own thresholds or figures, and the events beneath it. Labels read "How it was found", "Who has to act", "Action due". |
| 4 | Show the other field forms | Six forms, each runnable on the handset, with its own question set, photograph rule, frequency and role. |
| 5 | Geo-tag → geo-fence | Every form declares a fence. Step outside it in the prototype and the recorded position moves, the entry is held for the officer rather than filed, and the fence log shows three real outcomes. |
| 6 | Boundary — perimeter and bund protection | `perimeter.html`: 2,526 m measured along the FTL line, five segments, protection and condition for each, and a finding that the sanctioned fencing is 126 m short of the perimeter. |
| 7 | Survey numbers | `survey.html`: nine revenue parcels with classification, extent, holder and position, drawn on the map and reconciled against the baseline. Every case and every amenity verdict keys off a survey number. |
| 8 | Change detection analysis | `change.html`: each pass against the baseline, three candidates, one confirmed and two rejected, with the reason for each rejection kept on record. |
| 9 | Lake lifecycle | `lifecycle.html`: six custody stages, the gate each one has to pass, and what is blocking the next. Kept separate from the works project's own stages. |
| 10 | Lake encroachment | `encroachment.html`: a case file per encroachment, seven stages from detection to closure, tied to a survey number and a perimeter segment. |
| 11 | Lake restoration | `works.html`, carried over: measured quantity against sanctioned quantity, check-measured by a second officer. |
| 12 | Beautification / tourism — identify suitable land | `amenity.html`, deliberately constrained. Every parcel is put through six checks; anything inside the FTL or the notified buffer is never a candidate. Exclusions stay on the table rather than being filtered away. |
| 13 | Department view | `department.html` and a Department role: what each of five departments holds, what is asked of it and by when. Internal alerts and draft notices are not in that view. |
| 14 | Public view | `public.html` and a Public role: a published page, plus an explicit list of what is withheld and why. |

## Screens

| Screen | File | What it is for |
|---|---|---|
| Lake command | `index.html` | Tiles: every parameter and every area of work, worst first |
| Lake overview | `lake.html` | Status, decisions today, overdue, what changed this week |
| Alerts by parameter | `alerts.html` | Nine monitoring parameters, drilling to a single event |
| Change detection | `change.html` | Pass against baseline, candidates confirmed and rejected |
| Boundary and records | `baseline.html` | Accepted FTL line and where departmental records disagree |
| Survey numbers | `survey.html` | Revenue parcels, classification, extent, holder |
| Perimeter and bund | `perimeter.html` | Protection segment by segment |
| Lake lifecycle | `lifecycle.html` | Custody stages and the gate on each |
| Encroachment cases | `encroachment.html` | Detection through verification to removal |
| Restoration progress | `works.html` | Measurement book behind every percentage |
| Field capture | `field.html` | Six forms, geo-fence, offline queue |
| Compliance submissions | `compliance.html` | One dataset, one draft per authority |
| Department view | `department.html` | What each department holds and owes |
| Public view | `public.html` | Published and withheld, with reasons |
| Amenity suitability | `amenity.html` | Candidate land, outside FTL and buffer only |

## Roles

The switcher at the top right changes what the navigation shows and where a role lands.

| Role | Sees |
|---|---|
| Officer | Everything, including enforcement detail |
| Field | Assigned captures and the forms, plus the lake overview |
| Department | Boundary, survey position, lifecycle, compliance and what is asked of them |
| Public | The published page only |

A screen a role cannot see says so and offers the way back, rather than failing silently.

## Layout

    index.html                 tiles home
    lake.html …                one file per screen
    assets/css/aiq.css         tokens, app shell, components
    assets/js/aiq-shell.js     navigation, role switch, page boot
    assets/js/aiq-data.js      data loading, formatting, demo decisions
    assets/js/aiq-map.js       cartographic map: frame, grid, legend, title block
    data/                      demo data (v0.1 base, v0.2 in use)
    docs/                      data set notes
    tools/                     the two generators

## Running it locally

The pages fetch a JSON file, so opening `index.html` from disk will not work. Serve the folder:

    python3 -m http.server 8080

Then open http://localhost:8080.

## Changing the demo data

    cd tools
    python3 gen_aiq_demo_data.py        # writes data/aiq_demo_data_v0.1.json
    python3 gen_aiq_v2_extensions.py    # reads v0.1, writes data/aiq_demo_data_v0.2.json

Both seeds are fixed, so output is repeatable. **Do not hand-edit the JSON.** Much of v0.2 is derived
rather than typed: a case's survey number comes from a point-in-polygon test against the parcel ring, its
perimeter segment from the chainage of that point, a parcel's state from the cases on it, and every
amenity verdict from the six checks. Editing the JSON breaks those relationships silently.

## Deployment

Vercel deploys `main` automatically. Keep deployment protection on in the Vercel project settings; the
repository being private does not protect the URL.

## Governing document

AIQ-ARCH-001 in the Drive controlled library. It governs; this prototype follows it. The architecture
document is not kept in this repository.

## Ownership

See `NOTICE.md`.
