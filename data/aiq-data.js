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

  /* Daily summary of a sensor parameter: {day, v} per calendar day. */
  daily(data, device, key, how = "min") {
    const by = new Map();
    data.sensor_readings.forEach(r => {
      if (r.device !== device || r[key] === undefined) return;
      const d = r.ts.slice(0, 10);
      const cur = by.get(d);
      if (cur === undefined) by.set(d, r[key]);
      else if (how === "min") by.set(d, Math.min(cur, r[key]));
      else if (how === "max") by.set(d, Math.max(cur, r[key]));
      else by.set(d, r[key]);
    });
    return [...by.entries()].sort().map(([day, v]) => ({ day, v }));
  },

  /* Simple line chart into an <svg>. opts: {limit, limitLabel, markLowest, unit} */
  drawChart(svg, points, opts = {}) {
    const W = 560, H = 170, L = 38, R = 10, T = 12, B = 22;
    const ns = "http://www.w3.org/2000/svg";
    const ys = points.map(p => p.v);
    let lo = Math.min(...ys, opts.limit ?? Infinity), hi = Math.max(...ys, opts.limit ?? -Infinity);
    const padY = (hi - lo) * 0.15 || 1;
    lo = Math.floor((lo - padY) * 10) / 10; hi = Math.ceil((hi + padY) * 10) / 10;
    const x = i => L + i * (W - L - R) / (points.length - 1);
    const y = v => T + (hi - v) * (H - T - B) / (hi - lo);

    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("class", "chart");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", opts.label || "Time series");
    const el = (name, attrs, text) => {
      const n = document.createElementNS(ns, name);
      Object.entries(attrs).forEach(([k, v]) => n.setAttribute(k, v));
      if (text !== undefined) n.textContent = text;
      return n;
    };
    const frag = document.createDocumentFragment();

    [lo, hi].forEach(v => {
      frag.appendChild(el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), class: "grid-line" }));
      frag.appendChild(el("text", { x: 2, y: y(v) + 3 }, v.toFixed(1)));
    });
    if (opts.limit !== undefined) {
      frag.appendChild(el("line", { x1: L, x2: W - R, y1: y(opts.limit), y2: y(opts.limit), class: "limit" }));
      frag.appendChild(el("text", { x: W - R, y: y(opts.limit) - 4, "text-anchor": "end", fill: "#94261f" },
        opts.limitLabel || String(opts.limit)));
    }
    frag.appendChild(el("path", {
      class: "plot",
      d: points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ")
    }));
    if (opts.markLowest) {
      const i = ys.indexOf(Math.min(...ys));
      frag.appendChild(el("circle", { cx: x(i), cy: y(points[i].v), r: 3.5, class: "mark" }));
      frag.appendChild(el("text", {
        x: Math.min(x(i) + 8, W - 120), y: y(points[i].v) + 4, fill: "#94261f"
      }, `${points[i].v}${opts.unit || ""} on ${AIQ.date(points[i].day)}`));
    }
    [0, points.length - 1].forEach((i, n) => frag.appendChild(el("text", {
      x: x(i), y: H - 6, "text-anchor": n ? "end" : "start"
    }, AIQ.date(points[i].day))));
    svg.appendChild(frag);
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
    svg.classList.add("plan-ink");
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

    if (opts.sensors !== false) {
      (data.sensor_devices || []).forEach(s => {
        const c = document.createElementNS(ns, "rect");
        c.setAttribute("x", s.location[0] - 11); c.setAttribute("y", -s.location[1] - 11);
        c.setAttribute("width", 22); c.setAttribute("height", 22); c.setAttribute("class", "sensor");
        frag.appendChild(c);
        if (opts.labels !== false) {
          const t = document.createElementNS(ns, "text");
          t.setAttribute("x", s.location[0] + 20); t.setAttribute("y", -s.location[1] + 5);
          t.setAttribute("class", "node-label");
          t.textContent = s.id;
          frag.appendChild(t);
        }
      });
    }

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
