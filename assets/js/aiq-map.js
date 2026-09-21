/* AssetIQ prototype — cartographic map component.
   Draws a self-contained map sheet: neat line, map frame, coordinate grid,
   hydrographic symbology, feature labels, legend, north arrow, scale bar and
   title block. Styles are inline so the SVG stands alone (export, print).
   Geometry is a SYNTHETIC local grid in metres; the sheet says so. */

(function () {
  const NS = "http://www.w3.org/2000/svg";
  const FONT = "IBM Plex Sans, Segoe UI, Arial, sans-serif";
  const C = {
    ink: "#1b2a30", frame: "#1b2a30", grid: "#d9e1de", gridLabel: "#5c7078",
    water: "#bcd8e3", waterEdge: "#3b7ea1", waterLabel: "#2a6386",
    ftl: "#1f3a5f", buffer: "#c49a5c", bufferFill: "#f6ead6",
    catch: "#eef2ee", catchEdge: "#8ea39a", bund: "#6b5a45",
    struct: "#1b2a30", sensor: "#0e6e73", change: "#b3261e",
    rev: "#8e4585", irr: "#b0701a", not: "#2e6d4c", paper: "#ffffff", band: "#f7f9f8", bed: "#eeece0"
  };
  const FALSE_E = 10000, FALSE_N = 20000;   // keeps grid labels positive

  function el(name, attrs, text) {
    const n = document.createElementNS(NS, name);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text !== undefined) n.textContent = text;
    return n;
  }
  const pts = (arr, T) => arr.map(p => T(p).join(",")).join(" ");

  function drawMap(svg, data, opts = {}) {
    const g = data.geometry, a = data.asset;
    const uid = (svg.id || "map") + "-";
    const W = 720, H = 660;
    const F = { x: 48, y: 40, w: 632, h: 430 };           // map frame
    svg.innerHTML = "";
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", `Map of ${a.display_name}: ${opts.title || "spatial baseline"}`);
    svg.style.width = "100%"; svg.style.height = "auto"; svg.style.display = "block";

    /* ---------- transform: fit the asset (buffer + margin) into the frame */
    const ext = g.buffer_outer_boundary;
    const pad = opts.pad || 150;
    let minX = Math.min(...ext.map(p => p[0])) - pad, maxX = Math.max(...ext.map(p => p[0])) + pad;
    let minY = Math.min(...ext.map(p => p[1])) - pad, maxY = Math.max(...ext.map(p => p[1])) + pad;
    const s = Math.min(F.w / (maxX - minX), F.h / (maxY - minY));
    const cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    minX = cx - F.w / 2 / s; maxX = cx + F.w / 2 / s;
    minY = cy - F.h / 2 / s; maxY = cy + F.h / 2 / s;
    const T = p => [+(F.x + (p[0] - minX) * s).toFixed(1), +(F.y + (maxY - p[1]) * s).toFixed(1)];

    /* ---------- defs: hatching and clip */
    const defs = el("defs", {});
    const hatch = el("pattern", { id: uid + "buf", patternUnits: "userSpaceOnUse", width: 6, height: 6, patternTransform: "rotate(45)" });
    hatch.appendChild(el("rect", { width: 6, height: 6, fill: C.bufferFill }));
    hatch.appendChild(el("line", { x1: 0, y1: 0, x2: 0, y2: 6, stroke: C.buffer, "stroke-width": 1 }));
    defs.appendChild(hatch);
    const chg = el("pattern", { id: uid + "chg", patternUnits: "userSpaceOnUse", width: 4, height: 4, patternTransform: "rotate(-45)" });
    chg.appendChild(el("line", { x1: 0, y1: 0, x2: 0, y2: 4, stroke: C.change, "stroke-width": 1.2 }));
    defs.appendChild(chg);
    const clip = el("clipPath", { id: uid + "clip" });
    clip.appendChild(el("rect", { x: F.x, y: F.y, width: F.w, height: F.h }));
    defs.appendChild(clip);
    svg.appendChild(defs);

    /* ---------- sheet */
    svg.appendChild(el("rect", { x: 0, y: 0, width: W, height: H, fill: C.paper }));
    svg.appendChild(el("rect", { x: 6, y: 6, width: W - 12, height: H - 12, fill: "none", stroke: C.frame, "stroke-width": 1.6 }));
    svg.appendChild(el("rect", { x: 10, y: 10, width: W - 20, height: H - 20, fill: "none", stroke: C.frame, "stroke-width": 0.5 }));

    const map = el("g", { "clip-path": `url(#${uid}clip)` });
    map.appendChild(el("rect", { x: F.x, y: F.y, width: F.w, height: F.h, fill: "#fbfcfb" }));

    /* catchment, grid */
    map.appendChild(el("polygon", { points: pts(g.catchment, T), fill: C.catch, stroke: C.catchEdge, "stroke-width": 1, "stroke-dasharray": "7 4" }));
    const step = 100;
    for (let x = Math.ceil(minX / step) * step; x <= maxX; x += step)
      map.appendChild(el("line", { x1: T([x, 0])[0], x2: T([x, 0])[0], y1: F.y, y2: F.y + F.h, stroke: C.grid, "stroke-width": 0.6 }));
    for (let y = Math.ceil(minY / step) * step; y <= maxY; y += step)
      map.appendChild(el("line", { x1: F.x, x2: F.x + F.w, y1: T([0, y])[1], y2: T([0, y])[1], stroke: C.grid, "stroke-width": 0.6 }));

    /* buffer, water, FTL */
    map.appendChild(el("polygon", { points: pts(g.buffer_outer_boundary, T), fill: `url(#${uid}buf)`, stroke: C.buffer, "stroke-width": 0.8 }));
    map.appendChild(el("polygon", { points: pts(g.ftl_boundary, T), fill: C.bed, stroke: "none" }));
    map.appendChild(el("polygon", { points: pts(g.water_spread_current, T), fill: C.water, stroke: C.waterEdge, "stroke-width": 0.8 }));
    map.appendChild(el("polygon", { points: pts(g.ftl_boundary, T), fill: "none", stroke: C.ftl, "stroke-width": 1.9 }));

    /* departmental record overlays */
    const OV = { "DR-REV": C.rev, "DR-IRR": C.irr, "DR-NOT": C.not };
    (opts.overlays || []).forEach(id => {
      if (g.record_boundaries && g.record_boundaries[id])
        map.appendChild(el("polygon", { points: pts(g.record_boundaries[id], T), fill: "none", stroke: OV[id], "stroke-width": 1.5, "stroke-dasharray": "6 3" }));
    });

    /* bund with chainage */
    const bund = g.structures.find(x => x.type === "bund");
    if (bund) {
      const [p0, p1] = bund.line;
      map.appendChild(el("polyline", { points: pts(bund.line, T), fill: "none", stroke: C.bund, "stroke-width": 4.5, "stroke-linecap": "butt" }));
      const len = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
      for (let c = 0; c <= len + 0.1; c += 100) {
        const f = c / len, p = [p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f];
        const [X, Y] = T(p);
        map.appendChild(el("line", { x1: X, x2: X, y1: Y - 7, y2: Y, stroke: C.bund, "stroke-width": 1 }));
        map.appendChild(el("text", { x: X, y: Y - 10, "text-anchor": "middle", "font-size": 8, "font-family": FONT, fill: C.bund }, `${c}`));
      }
      const [bx, by] = T([p0[0], p0[1]]);
      map.appendChild(el("text", { x: bx - 6, y: by + 3, "text-anchor": "end", "font-size": 8.5, "font-family": FONT, fill: C.bund }, "Ch (m)"));
    }

    /* structures: inlets as arrows, sluice and weir as symbols */
    g.structures.filter(x => x.point).forEach(st => {
      const [X, Y] = T(st.point);
      if (st.type === "inlet") {
        const v = [-st.point[0], -st.point[1]], m = Math.hypot(...v) || 1;
        const ux = v[0] / m, uy = -v[1] / m;           // screen direction toward centre
        const x0 = X - ux * 26, y0 = Y - uy * 26;
        map.appendChild(el("line", { x1: x0, y1: y0, x2: X - ux * 4, y2: Y - uy * 4, stroke: C.waterEdge, "stroke-width": 1.8 }));
        const hx = X - ux * 4, hy = Y - uy * 4, px = -uy, py = ux;
        map.appendChild(el("polygon", { points: `${hx + ux * 5},${hy + uy * 5} ${hx + px * 4},${hy + py * 4} ${hx - px * 4},${hy - py * 4}`, fill: C.waterEdge }));
        const lft = st.id === "IN-2";
        map.appendChild(el("text", { x: lft ? x0 - 6 : x0 + (ux < 0 ? 4 : -4), y: lft ? y0 + 3 : y0 - 5, "text-anchor": lft ? "end" : (ux < 0 ? "start" : "end"), "font-size": 9.5, "font-family": FONT, fill: C.ink }, st.id.replace("IN-", "Inlet ")));
      } else {
        const sym = st.type === "sluice"
          ? el("rect", { x: X - 4.5, y: Y - 4.5, width: 9, height: 9, fill: C.struct })
          : el("polygon", { points: `${X},${Y - 6} ${X + 6},${Y + 4} ${X - 6},${Y + 4}`, fill: C.struct });
        map.appendChild(sym);
        const lab = st.type === "sluice" ? { x: X - 8, y: Y + 14, a: "end", t: "Sluice" } : { x: X + 9, y: Y + 14, a: "start", t: "Surplus weir" };
        map.appendChild(el("text", { x: lab.x, y: lab.y, "text-anchor": lab.a, "font-size": 9.5, "font-family": FONT, fill: C.ink }, lab.t));
      }
    });

    /* sensors */
    if (opts.sensors !== false) (data.sensor_devices || []).forEach(sd => {
      const [X, Y] = T(sd.location);
      map.appendChild(el("circle", { cx: X, cy: Y, r: 5, fill: C.paper, stroke: C.sensor, "stroke-width": 1.6 }));
      map.appendChild(el("circle", { cx: X, cy: Y, r: 1.8, fill: C.sensor }));
      const left = sd.type === "level";
      map.appendChild(el("text", { x: left ? X - 8 : X + 8, y: left ? Y - 7 : Y + 3.5, "text-anchor": left ? "end" : "start", "font-size": 9, "font-family": FONT, fill: C.sensor }, sd.id));
    });

    /* change */
    if (opts.changes !== false) (g.change_polygons || []).forEach((cp, i) => {
      map.appendChild(el("polygon", { points: pts(cp.polygon, T), fill: `url(#${uid}chg)`, stroke: C.change, "stroke-width": 1.4 }));
      const top = cp.polygon.reduce((m, p) => p[1] > m[1] ? p : m, cp.polygon[0]);
      const [X, Y] = T(top);
      map.appendChild(el("line", { x1: X + 3, y1: Y - 2, x2: X + 70, y2: Y - 30, stroke: C.change, "stroke-width": 0.8 }));
      map.appendChild(el("text", { x: X + 73, y: Y - 30, "font-size": 9.5, "font-family": FONT, fill: C.change, "font-weight": 600 }, `C-${String(i + 1).padStart(2, "0")} fill, ${opts.changeDate || ""}`.replace(/, $/, "")));
    });

    /* water body name — hydrographic convention: italic, blue */
    const [lx, ly] = T([0, -20]);
    map.appendChild(el("text", { x: lx, y: ly, "text-anchor": "middle", "font-size": 15, "font-style": "italic", "letter-spacing": 1.5, "font-family": FONT, fill: C.waterLabel }, a.display_name.replace(" (fictitious)", "").toUpperCase()));
    map.appendChild(el("text", { x: lx, y: ly + 15, "text-anchor": "middle", "font-size": 9, "font-style": "italic", "font-family": FONT, fill: C.waterLabel }, `water spread ${opts.waterDate || ""}`.trim()));
    svg.appendChild(map);

    /* ---------- frame and grid labels (false origin applied) */
    svg.appendChild(el("rect", { x: F.x, y: F.y, width: F.w, height: F.h, fill: "none", stroke: C.frame, "stroke-width": 1.2 }));
    for (let x = Math.ceil(minX / 200) * 200; x <= maxX; x += 200) {
      const X = T([x, 0])[0];
      svg.appendChild(el("line", { x1: X, x2: X, y1: F.y - 5, y2: F.y, stroke: C.frame, "stroke-width": 0.8 }));
      svg.appendChild(el("text", { x: X, y: F.y - 8, "text-anchor": "middle", "font-size": 8.5, "font-family": FONT, fill: C.gridLabel }, `${(x + FALSE_E).toLocaleString("en-IN")} E`));
    }
    for (let y = Math.ceil(minY / 200) * 200; y <= maxY; y += 200) {
      const Y = T([0, y])[1];
      svg.appendChild(el("line", { x1: F.x - 5, x2: F.x, y1: Y, y2: Y, stroke: C.frame, "stroke-width": 0.8 }));
      const t = el("text", { x: F.x - 8, y: Y, "text-anchor": "middle", "font-size": 8.5, "font-family": FONT, fill: C.gridLabel,
        transform: `rotate(-90 ${F.x - 8} ${Y})` }, `${(y + FALSE_N).toLocaleString("en-IN")} N`);
      svg.appendChild(t);
    }

    /* ---------- lower band: legend | north + scale | title block */
    const by = F.y + F.h + 14, bh = H - 16 - by;
    svg.appendChild(el("rect", { x: 10, y: by - 4, width: W - 20, height: bh + 10, fill: C.band }));
    svg.appendChild(el("line", { x1: 10, x2: W - 10, y1: by - 4, y2: by - 4, stroke: C.frame, "stroke-width": 0.8 }));

    // legend
    const L = el("g", {});
    L.appendChild(el("text", { x: 22, y: by + 12, "font-size": 10, "font-weight": 700, "letter-spacing": 1, "font-family": FONT, fill: C.ink }, "LEGEND"));
    const items = [
      ["water", `Water spread${opts.waterDate ? ", " + opts.waterDate : ""}`],
      ["ftl", "Full tank level (FTL)"],
      ["bed", "Lake bed within FTL, exposed"],
      ["buffer", "Buffer zone, 30 m"],
      ["catch", "Catchment boundary"],
      ["bund", "Bund, chainage in m"],
      ["inlet", "Inlet, direction of flow"],
      ["struct", "Sluice ▪ / surplus weir ▲"]
    ];
    if (opts.sensors !== false) items.push(["sensor", "Monitoring station"]);
    if (opts.changes !== false) items.push(["change", "Change detected"]);
    (opts.overlays || []).forEach(id => {
      const r = (data.departmental_records || []).find(d => d.id === id);
      if (r) items.push(["ov:" + id, `${r.department.split(" (")[0]} record, ${r.ftl_area_ha} ha`]);
    });
    const colW = 188, rowH = 15.5, perCol = Math.ceil(items.length / 2);
    items.forEach(([k, label], i) => {
      const x = 22 + Math.floor(i / perCol) * colW, y = by + 26 + (i % perCol) * rowH;
      const sw = el("g", {});
      if (k === "water") sw.appendChild(el("rect", { x, y: y - 7, width: 22, height: 10, fill: C.water, stroke: C.waterEdge, "stroke-width": 0.8 }));
      else if (k === "bed") sw.appendChild(el("rect", { x, y: y - 7, width: 22, height: 10, fill: C.bed, stroke: C.ftl, "stroke-width": 0.8 }));
      else if (k === "ftl") sw.appendChild(el("line", { x1: x, x2: x + 22, y1: y - 2, y2: y - 2, stroke: C.ftl, "stroke-width": 2 }));
      else if (k === "buffer") sw.appendChild(el("rect", { x, y: y - 7, width: 22, height: 10, fill: `url(#${uid}buf)`, stroke: C.buffer, "stroke-width": 0.8 }));
      else if (k === "catch") sw.appendChild(el("line", { x1: x, x2: x + 22, y1: y - 2, y2: y - 2, stroke: C.catchEdge, "stroke-width": 1.2, "stroke-dasharray": "5 3" }));
      else if (k === "bund") sw.appendChild(el("line", { x1: x, x2: x + 22, y1: y - 2, y2: y - 2, stroke: C.bund, "stroke-width": 4.5 }));
      else if (k === "inlet") { sw.appendChild(el("line", { x1: x, x2: x + 16, y1: y - 2, y2: y - 2, stroke: C.waterEdge, "stroke-width": 1.8 }));
        sw.appendChild(el("polygon", { points: `${x + 22},${y - 2} ${x + 15},${y - 6} ${x + 15},${y + 2}`, fill: C.waterEdge })); }
      else if (k === "struct") { sw.appendChild(el("rect", { x, y: y - 6.5, width: 8, height: 8, fill: C.struct }));
        sw.appendChild(el("polygon", { points: `${x + 17},${y - 7} ${x + 22},${y + 2} ${x + 12},${y + 2}`, fill: C.struct })); }
      else if (k === "sensor") { sw.appendChild(el("circle", { cx: x + 11, cy: y - 2, r: 5, fill: C.paper, stroke: C.sensor, "stroke-width": 1.6 }));
        sw.appendChild(el("circle", { cx: x + 11, cy: y - 2, r: 1.8, fill: C.sensor })); }
      else if (k === "change") sw.appendChild(el("rect", { x, y: y - 7, width: 22, height: 10, fill: `url(#${uid}chg)`, stroke: C.change, "stroke-width": 1.2 }));
      else if (k.startsWith("ov:")) sw.appendChild(el("line", { x1: x, x2: x + 22, y1: y - 2, y2: y - 2, stroke: OV[k.slice(3)], "stroke-width": 1.6, "stroke-dasharray": "6 3" }));
      L.appendChild(sw);
      L.appendChild(el("text", { x: x + 30, y: y + 1.5, "font-size": 9.5, "font-family": FONT, fill: C.ink }, label));
    });
    svg.appendChild(L);

    // north arrow (grid north) and scale bar
    const nx = 460, ny = by + 20;
    svg.appendChild(el("polygon", { points: `${nx},${ny - 10} ${nx + 8},${ny + 14} ${nx},${ny + 8}`, fill: C.ink }));
    svg.appendChild(el("polygon", { points: `${nx},${ny - 10} ${nx - 8},${ny + 14} ${nx},${ny + 8}`, fill: C.paper, stroke: C.ink, "stroke-width": 1 }));
    svg.appendChild(el("text", { x: nx, y: ny - 14, "text-anchor": "middle", "font-size": 11, "font-weight": 700, "font-family": FONT, fill: C.ink }, "N"));
    svg.appendChild(el("text", { x: nx, y: ny + 27, "text-anchor": "middle", "font-size": 8, "font-family": FONT, fill: C.gridLabel }, "Grid north"));

    const lens = [100, 200, 250, 500];
    const Lm = lens.find(l => l * s >= 70) || 500, px = Lm * s, sx = 408, sy = by + 72, seg = px / 4;
    for (let i = 0; i < 4; i++)
      svg.appendChild(el("rect", { x: sx + i * seg, y: sy, width: seg, height: 5, fill: i % 2 ? C.paper : C.ink, stroke: C.ink, "stroke-width": 0.8 }));
    [0, Lm / 2, Lm].forEach((v, i) =>
      svg.appendChild(el("text", { x: sx + i * px / 2, y: sy + 16, "text-anchor": "middle", "font-size": 8.5, "font-family": FONT, fill: C.ink }, `${v}`)));
    svg.appendChild(el("text", { x: sx + px / 2, y: sy + 28, "text-anchor": "middle", "font-size": 8, "font-family": FONT, fill: C.gridLabel }, "Scale in metres"));

    // title block
    const tx = 520, tw = W - 16 - tx;
    svg.appendChild(el("rect", { x: tx, y: by, width: tw, height: bh - 2, fill: C.paper, stroke: C.frame, "stroke-width": 0.8 }));
    const tl = [
      [a.display_name.replace(" (fictitious)", "").toUpperCase(), 11, 700, C.ink],
      [opts.title || "Spatial baseline", 9.5, 600, C.ink],
      [`${opts.mapRef || "AIQ-L01-01"} · as at ${opts.asAt || ""}`.replace(/ as at $/, ""), 8, 400, C.gridLabel],
      [`Baseline ${data.spatial_baseline.id}, accepted ${opts.acceptedOn || ""}`, 8, 400, C.gridLabel],
      [data.spatial_baseline.method.replace(" (synthetic)", ""), 8, 400, C.gridLabel],
      ["Grid: synthetic local, metres", 8, 400, C.gridLabel],
      [`False origin ${FALSE_E.toLocaleString("en-IN")} E, ${FALSE_N.toLocaleString("en-IN")} N`, 8, 400, C.gridLabel]
    ];
    tl.forEach(([t, fs, fw, col], i) =>
      svg.appendChild(el("text", { x: tx + 8, y: by + 15 + i * 13, "font-size": fs, "font-weight": fw, "font-family": FONT, fill: col }, t)));
    svg.appendChild(el("rect", { x: tx, y: by + bh - 22, width: tw, height: 20, fill: "#fbeceb" }));
    svg.appendChild(el("text", { x: tx + tw / 2, y: by + bh - 8.5, "text-anchor": "middle", "font-size": 7.2, "font-weight": 700, "letter-spacing": 0, "font-family": FONT, fill: C.change }, "ILLUSTRATIVE — NOT A SURVEY PRODUCT"));

    return svg;
  }

  window.AIQMap = { draw: drawMap };
})();
