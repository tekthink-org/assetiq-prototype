/* AssetIQ — application shell.
   Renders the fixed sidebar, the top bar and the role switcher into every page,
   so the pages themselves hold only their own content. A page declares itself
   with <body data-screen="overview">; everything else is derived here. */

(function () {
  const ROLE_KEY = "aiq-role";
  const DEFAULT_ROLE = "officer";

  /* Navigation. Each item names the roles that may see it. The groups are the
     four things an officer actually does: watch, know the asset, act, report. */
  const NAV = [
    {
      group: "Monitor", items: [
        { id: "home", label: "Home", href: "index.html", roles: ["officer"], hint: "Every screen, as tiles" },
        { id: "overview", label: "Lake overview", href: "lake.html", roles: ["officer", "field", "department"], hint: "Status, decisions, overdue" },
        { id: "alerts", label: "Alerts by parameter", href: "alerts.html", roles: ["officer"], hint: "Verify and act" },
        { id: "change", label: "Change detection", href: "change.html", roles: ["officer"], hint: "Pass against baseline" },
      ]
    },
    {
      group: "The asset", items: [
        { id: "boundary", label: "Boundary and records", href: "baseline.html", roles: ["officer", "department"], hint: "FTL, buffer, disputes" },
        { id: "survey", label: "Survey numbers", href: "survey.html", roles: ["officer", "department"], hint: "Revenue parcels" },
        { id: "perimeter", label: "Perimeter and bund", href: "perimeter.html", roles: ["officer"], hint: "Protection, segment by segment" },
        { id: "lifecycle", label: "Lake lifecycle", href: "lifecycle.html", roles: ["officer", "department"], hint: "Custody stage and gates" },
      ]
    },
    {
      group: "Act", items: [
        { id: "encroachment", label: "Encroachment cases", href: "encroachment.html", roles: ["officer"], hint: "Detection to removal" },
        { id: "works", label: "Restoration progress", href: "works.html", roles: ["officer"], hint: "Measured, check-measured" },
        { id: "field", label: "Field capture", href: "field.html", roles: ["officer", "field"], hint: "Forms, geo-fence, offline" },
      ]
    },
    {
      group: "Report", items: [
        { id: "compliance", label: "Compliance submissions", href: "compliance.html", roles: ["officer", "department"], hint: "One dataset, many formats" },
        { id: "department", label: "Department view", href: "department.html", roles: ["officer", "department"], hint: "What each department owes" },
        { id: "public", label: "Public view", href: "public.html", roles: ["officer", "public"], hint: "Published and withheld" },
        { id: "amenity", label: "Amenity suitability", href: "amenity.html", roles: ["officer"], hint: "Outside FTL and buffer only" },
      ]
    },
  ];

  const ROLES = [
    { key: "officer", name: "Officer", who: "Nodal officer" },
    { key: "field", name: "Field", who: "Field assistant" },
    { key: "department", name: "Department", who: "Revenue, Irrigation, others" },
    { key: "public", name: "Public", who: "Citizen" },
  ];

  function getRole() {
    try { return sessionStorage.getItem(ROLE_KEY) || DEFAULT_ROLE; }
    catch (e) { return DEFAULT_ROLE; }
  }
  function setRole(r) {
    try { sessionStorage.setItem(ROLE_KEY, r); } catch (e) {}
  }

  function visibleNav(role) {
    return NAV.map(g => ({ group: g.group, items: g.items.filter(i => i.roles.includes(role)) }))
      .filter(g => g.items.length);
  }

  /* Where a role should land when it has no access to the current screen. */
  function homeFor(role) {
    return ({ officer: "index.html", field: "field.html", department: "department.html", public: "public.html" })[role];
  }

  function build(screen, data) {
    const role = getRole();
    const groups = visibleNav(role);
    /* the command home belongs to the officer view; other roles have their own */
    const allowed = screen === "home" ? role === "officer" : groups.some(g => g.items.some(i => i.id === screen));

    const shell = document.createElement("div");
    shell.className = "app";
    shell.innerHTML = `
      <aside class="side">
        <a class="brand" href="index.html">Asset<span>IQ</span></a>
        <nav>
          ${groups.map(g => `
            <div class="nav-group">
              <p class="nav-h">${g.group}</p>
              ${g.items.map(i => `
                <a class="nav-i${i.id === screen ? " on" : ""}" href="${i.href}" data-id="${i.id}">
                  <span class="nav-l">${i.label}</span>
                  <span class="nav-hint">${i.hint}</span>
                </a>`).join("")}
            </div>`).join("")}
        </nav>
        <div class="side-foot">
          <p>Interactive wireframe</p>
          <p>All data fictitious</p>
        </div>
      </aside>
      <div class="main">
        <header class="topbar">
          <div class="tb-asset">
            <span class="tb-name" id="tb-asset">—</span>
            <span class="tb-sub" id="tb-sub"></span>
          </div>
          <div class="tb-right">
            <span class="tb-as-at" id="tb-asat"></span>
            <div class="rolesw" role="group" aria-label="View as">
              <span class="rolesw-l">View as</span>
              ${ROLES.map(r => `<button type="button" data-role="${r.key}" aria-pressed="${r.key === role}" title="${r.who}">${r.name}</button>`).join("")}
            </div>
          </div>
        </header>
        <div class="content" id="app-content"></div>
      </div>`;

    /* move the page's own markup into the content area */
    const page = document.getElementById("page");
    document.body.insertBefore(shell, document.body.firstChild);
    shell.querySelector("#app-content").appendChild(page);

    shell.querySelectorAll("[data-role]").forEach(b => b.addEventListener("click", () => {
      const r = b.dataset.role;
      setRole(r);
      const ok = screen === "home" ? r === "officer" : visibleNav(r).some(g => g.items.some(i => i.id === screen));
      location.href = ok ? location.pathname + location.hash : homeFor(r);
    }));

    if (data) {
      document.getElementById("tb-asset").textContent = data.asset.display_name;
      document.getElementById("tb-sub").textContent =
        `${data.asset.ftl_area_ha} ha at FTL · ${data.asset.zone}, ${data.asset.circle} · ${data.authority.name}`;
      document.getElementById("tb-asat").textContent = "As at " + AIQ.dateTime(data.officer_view.as_of);
    }

    if (!allowed) {
      const c = document.getElementById("app-content");
      c.innerHTML = `<div class="page"><section class="panel"><h2>Not in this view</h2>
        <div class="body">
          <p>The <strong>${ROLES.find(r => r.key === role).name}</strong> view does not include this screen.
             That is the point of a role: a field assistant does not see draft notices, and a public
             page does not see an open enforcement case.</p>
          <p><a href="${homeFor(role)}">Go to the ${ROLES.find(r => r.key === role).name} home</a>,
             or switch the view at the top right.</p>
        </div></section></div>`;
    }
    return { role, allowed };
  }

  /* Every page boots the same way: load the data, draw the shell, then render.
     A page that throws shows the reason rather than a screen of empty panels. */
  async function boot(render) {
    const screen = document.body.dataset.screen;
    let data = null, err = null;
    try { data = await aiqLoad(); } catch (e) { err = e; }
    const ctx = build(screen, data);
    if (err) {
      document.getElementById("app-content").innerHTML =
        `<div class="page"><section class="panel"><h2>The demonstration data did not load</h2>
          <div class="body"><p>This page reads <code>data/aiq_demo_data_v0.2.json</code>. Serve the folder
          over HTTP (<code>python3 -m http.server 8080</code>) rather than opening the file from disk.</p>
          <p class="wire-note">${String(err.message || err)}</p></div></section></div>`;
      return;
    }
    if (!ctx.allowed) return;
    try { await render(data, ctx); }
    catch (e) {
      console.error(e);
      const box = document.createElement("section");
      box.className = "panel";
      box.innerHTML = `<h2>This screen failed to render</h2><div class="body">
        <p class="wire-note">${String(e.message || e)}</p></div>`;
      document.getElementById("page").prepend(box);
    }
  }

  window.AIQShell = { build, boot, getRole, setRole, NAV, ROLES, visibleNav, homeFor };
})();
