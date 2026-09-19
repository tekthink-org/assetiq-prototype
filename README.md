# AssetIQ — prototype

Interactive wireframe for **AssetIQ**, an asset intelligence platform for public assets held in custody by a government body: lakes, tanks, nalas, storm drains and canals.

It answers one question: **is this asset intact, in the condition we believe, and protected — and if not, what needs a decision today?**

> **All data here is fictitious.** The lake, authority, people, contractor, laboratory and order references are invented, and the coordinates are a synthetic local grid, not real locations. Nothing in this repository describes a real water body, authority or person.

## Status

This is an interactive wireframe and executable specification, not a production system. Screens show outcomes only; no detection logic, thresholds or model tags are displayed. aiQube tags stay empty until the model is issued.

## Screens

| Screen | File | Status |
|---|---|---|
| Landing | `index.html` | built |
| Officer lake view | `lake.html` | next |
| Alert → verify → act | `alerts.html` | planned |
| Field capture (mobile) | `field.html` | planned |
| Restoration progress | `works.html` | planned |
| Compliance generator | `compliance.html` | planned |
| Baseline and record register | `baseline.html` | planned |
| Portfolio view | `portfolio.html` | planned |

## Layout

    index.html            landing
    assets/css/aiq.css    design tokens, layout, components
    assets/js/aiq-data.js data loading and shared helpers
    data/                 demo data set (JSON)
    docs/                 data set README
    tools/                data generator (Python)

## Running it locally

The pages fetch a JSON file, so opening `index.html` directly from disk will not work. Serve the folder instead:

    python3 -m http.server 8080

Then open http://localhost:8080.

## Changing the demo data

Edit `tools/gen_aiq_demo_data.py` and re-run it, then replace `data/aiq_demo_data_v0.1.json`. The seed is fixed, so the output is repeatable, and event text that quotes figures is generated from the data. Do not hand-edit the JSON — the text and the charts will drift apart.

## Deployment

Vercel deploys `main` automatically. Keep deployment protection switched on in the Vercel project settings; the repository being private does not protect the URL.

## Governing document

AIQ-ARCH-001 (AssetIQ product architecture) in the Drive controlled library. It governs; this prototype follows it. The architecture document itself is not kept in this repository.

## Ownership

See `NOTICE.md`.
