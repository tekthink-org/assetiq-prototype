/* AssetIQ prototype — data loading and shared helpers.
   All data is fictitious. Coordinates are a local metre grid, not lat/long. */

const AIQ_DATA_URL = "data/aiq_demo_data_v0.1.json";

let _cache = null;

async function aiqLoad() {
  if (_cache) return _cache;
  const res = await fetch(AIQ_DATA_URL, { cache: "no-store" });
  if (!res.ok) throw new Error("Could not load " + AIQ_DATA_URL + " (" + res.status + ")");
  _cache = await res.json();
  return _cache;
}

const AIQ = {
  date(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
  },
  dateTime(iso) {
    const d = new Date(iso);
    return d.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  },
  custody(state) {
    return ({
      identified: "Identified",
      preliminary_notified: "Preliminary notification",
      final_notified: "Final notification",
      baselined: "Baseline accepted",
      under_restoration: "Under restoration",
      protected_monitored: "Protected and monitored"
    })[state] || state;
  },
  source(s) {
    return ({
      spatial_survey: "Survey",
      drone: "Drone",
      satellite: "Satellite",
      in_situ_sensor: "Sensor",
      laboratory: "Laboratory",
      field_inspection: "Field inspection",
      citizen_report: "Citizen report",
      departmental_record: "Departmental record"
    })[s] || s;
  },
  zone(data, id) {
    const z = data.asset.zones.find(z => z.id === id);
    return z ? z.name : id;
  },
  /* Draws the lake plan into an <svg>. Local metre grid, y flipped for screen. */
  drawPlan(svg, data, opts = {}) {
    const g = data.geometry;
    /* Fit to the asset, not the catchment: the catchment is drawn as a tint
       that runs beyond the frame. */
    const all = g.buffer_outer_boundary;
    const xs = all.map(p => p[0]), ys = all.map(p => p[1]);
    const pad = 140;
    const minX = Math.min(...xs) - pad, maxX = Math.max(...xs) + pad;
    const minY = Math.min(...ys) - pad, maxY = Math.max(...ys) + pad;
    const W = maxX - minX, H = maxY - minY;
    svg.setAttribute("viewBox", `${minX} ${-maxY} ${W} ${H}`);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label",
      `Schematic plan of ${data.asset.display_name}: catchment, buffer zone, full tank level boundary and current water spread`);

    const ns = "http://www.w3.org/2000/svg";
    const poly = (pts, cls) => {
      const el = document.createElementNS(ns, "polygon");
      el.setAttribute("points", pts.map(p => `${p[0]},${-p[1]}`).join(" "));
      el.setAttribute("class", cls);
      return el;
    };
    const frag = document.createDocumentFragment();
    frag.appendChild(poly(g.catchment, "catchment"));
    frag.appendChild(poly(g.buffer_outer_boundary, "buffer"));
    frag.appendChild(poly(g.ftl_boundary, "ftl"));
    frag.appendChild(poly(g.water_spread_current, "water"));

    g.structures.forEach(s => {
      if (s.line) {
        const el = document.createElementNS(ns, "polyline");
        el.setAttribute("points", s.line.map(p => `${p[0]},${-p[1]}`).join(" "));
        el.setAttribute("class", "bund");
        frag.appendChild(el);
      } else if (s.point) {
        const c = document.createElementNS(ns, "circle");
        c.setAttribute("cx", s.point[0]); c.setAttribute("cy", -s.point[1]);
        c.setAttribute("r", 14); c.setAttribute("class", "node");
        frag.appendChild(c);
        if (opts.labels !== false) {
          const t = document.createElementNS(ns, "text");
          t.setAttribute("x", s.point[0] + 22); t.setAttribute("y", -s.point[1] + 5);
          t.setAttribute("class", "node-label");
          t.textContent = s.id;
          frag.appendChild(t);
        }
      }
    });

    if (opts.changes !== false) {
      (g.change_polygons || []).forEach(cp => {
        const el = poly(cp.polygon, "flag");
        frag.appendChild(el);
        const box = cp.polygon.reduce((a, p) => [Math.max(a[0], p[0]), Math.max(a[1], p[1])], [-1e9, -1e9]);
        const t = document.createElementNS(ns, "text");
        t.setAttribute("x", box[0] + 30); t.setAttribute("y", -box[1] - 14);
        t.setAttribute("class", "flag-label");
        t.textContent = "Fill flagged";
        frag.appendChild(t);
      });
    }
    svg.appendChild(frag);
  }
};
