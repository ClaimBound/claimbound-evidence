(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var D = null;
  try { D = JSON.parse($("atlas-data").textContent); } catch (e) { D = null; }
  if (!D) { $("fatal").hidden = false; return; }
  $("app").hidden = false;

  var ID = 0, PR = 1, ST = 2, DO = 3, LV = 4, DT = 5, CL = 6, SH = 7, SRC = 8;
  var RAWKEYS = { 0: "evidence_id", 1: "protocol_id", 2: "result_status", 3: "domain", 4: "reproduction_level", 6: "claim_boundary" };
  var GLYPH = {
    PASSED_UNDER_PROTOCOL: ["\u2713", "P"], NEGATIVE_RESULT_UNDER_PROTOCOL: ["\u2717", "N"],
    BLOCKED_SOURCE: ["\u25A0", "B"], INSUFFICIENT_COVERAGE: ["\u25D0", "I"],
    SOURCE_DRIFT: ["\u21AF", "D"], REPRODUCED_OUTCOME: ["\u21BB", "R"], HIDDEN: ["\u25A2", "H"]
  };
  var ORDER = Object.keys(GLYPH);
  var PAGE = 50;
  var R = D.rows, N = R.length;
  var langs = D.i18n.langs, L = langs.en, lang = D.i18n["default"];
  var st = { q: "", status: "", domain: "", level: "", from: "", to: "", sort: -1, dir: 1, page: 0, cur: -1, open: -1 };
  var view = [], H = [], byId = Object.create(null), lastFocus = null;

  function store(k, v) { try { if (v === undefined) { return window.localStorage.getItem(k); } window.localStorage.setItem(k, v); } catch (e) { } return null; }
  function t(key, vars) {
    var s = L[key];
    if (typeof s !== "string") { s = langs.en[key]; }
    if (typeof s !== "string") { s = key; }
    if (vars) { s = s.replace(/\{(\w+)\}/g, function (m, k) { return Object.prototype.hasOwnProperty.call(vars, k) ? String(vars[k]) : m; }); }
    return s;
  }
  function el(tag, props, kids) {
    var n = document.createElement(tag), k;
    if (props) { for (k in props) { if (k === "text") { n.textContent = props[k]; } else if (k === "class") { n.className = props[k]; } else { n.setAttribute(k, props[k]); } } }
    (kids || []).forEach(function (c) { n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function clear(n) { while (n.firstChild) { n.removeChild(n.firstChild); } }
  function known(s) { return Object.prototype.hasOwnProperty.call(GLYPH, s) ? s : "unknown"; }
  function badge(s) {
    var g = GLYPH[s] || ["?", "?"];
    return el("span", { "class": "badge s-" + known(s), title: GLYPH[s] ? s : t("unknown_status") }, [el("span", { "aria-hidden": "true", text: g[0] }), el("span", { text: g[1] + " " + (s === null ? "" : s) })]);
  }
  function show(v) { return v === null || v === undefined ? "" : String(v); }

  function setStatic() {
    document.documentElement.lang = lang;
    document.title = D.title;
    $("atlas-title").textContent = D.title;
    Array.prototype.forEach.call(document.querySelectorAll("[data-i18n]"), function (n) { n.textContent = t(n.getAttribute("data-i18n")); });
    Array.prototype.forEach.call(document.querySelectorAll("[data-i18n-attr]"), function (n) {
      n.getAttribute("data-i18n-attr").split(",").forEach(function (pair) { var p = pair.split(":"); n.setAttribute(p[0], t(p[1])); });
    });
  }

  function buildHaystack() {
    var i, r;
    for (i = 0; i < N; i++) {
      r = R[i];
      H.push([r[ID], r[PR], r[ST], r[DO], r[LV], r[CL], r[SRC]].join("\n").toLowerCase());
      if (!(r[ID] in byId)) { byId[r[ID]] = i; }
    }
  }

  function uniq(col) {
    var seen = Object.create(null), out = [];
    R.forEach(function (r) { var v = show(r[col]); if (v !== "" && !seen[v]) { seen[v] = 1; out.push(v); } });
    return out.sort();
  }
  var OPT = { status: ST, domain: DO, level: LV };
  var SEL = { status: "f-status", domain: "f-domain", level: "f-level" };
  function fillSelect(key) {
    var s = $(SEL[key]), vals = key === "status" ? ORDER.filter(function (x) { return D.statuses[x]; }).concat(Object.keys(D.statuses).filter(function (x) { return !GLYPH[x]; }).sort()) : uniq(OPT[key]);
    clear(s);
    s.appendChild(el("option", { value: "", text: t("filter_all") }));
    vals.forEach(function (v) { s.appendChild(el("option", { value: v, text: v })); });
    s.value = st[key];
  }

  function matches(i) {
    var r = R[i];
    if (st.q && H[i].indexOf(st.q) < 0) { return false; }
    if (st.status && show(r[ST]) !== st.status) { return false; }
    if (st.domain && show(r[DO]) !== st.domain) { return false; }
    if (st.level && show(r[LV]) !== st.level) { return false; }
    if (st.from || st.to) {
      if (!r[DT]) { return false; }
      if (st.from && r[DT] < st.from) { return false; }
      if (st.to && r[DT] > st.to) { return false; }
    }
    return true;
  }
  function refilter(keepPage) {
    var i, out = [];
    for (i = 0; i < N; i++) { if (matches(i)) { out.push(i); } }
    if (st.sort >= 0) {
      var c = st.sort, d = st.dir;
      out.sort(function (a, b) { var x = show(R[a][c]), y = show(R[b][c]); return x < y ? -d : x > y ? d : a - b; });
    }
    view = out;
    if (!keepPage) { st.page = 0; st.cur = -1; }
    renderResults();
  }

  function renderIntegrity() {
    var box = $("integrity");
    clear(box);
    D.integrity.forEach(function (g) {
      var b;
      if (g.kind === "ledger" && g.ok) {
        b = el("p", { "class": "banner ok", role: "status", text: t("integrity_ledger_ok", { count: g.count, seq: g.head_seq === null ? "-" : g.head_seq, hash: g.head_hash === null ? "-" : g.head_hash }) });
      } else if (g.kind === "disclosure") {
        b = el("p", { "class": "banner", role: "note", text: t("integrity_disclosure", { full: g.counts.full, summary: g.counts.summary, hidden: g.counts.hidden }) });
      } else if (g.kind === "ledger") {
        var ul = el("ul");
        g.problems.forEach(function (p) { ul.appendChild(el("li", { text: t("problem_item", { code: p.code, seq: p.seq, message: p.message }) })); });
        b = el("div", { "class": "banner bad", role: "alert" }, [el("span", { text: t("integrity_ledger_failed", { count: g.problem_count }) }), ul]);
      } else {
        b = el("p", { "class": "banner", text: t("integrity_cards", { count: g.count }) });
      }
      box.appendChild(b);
    });
    if (D.issues.count) {
      var il = el("ul");
      D.issues.items.forEach(function (x) { il.appendChild(el("li", { text: t("issue_item", { path: x.path, reason: x.reason }) })); });
      var more = D.issues.count > D.issues.items.length ? [el("li", { text: t("issues_more", { n: D.issues.count - D.issues.items.length }) })] : [];
      more.forEach(function (m) { il.appendChild(m); });
      box.appendChild(el("details", { "class": "banner" }, [el("summary", { text: t("integrity_issues", { count: D.issues.count }) }), il]));
    }
    if (D.shown < D.total) { box.appendChild(el("p", { "class": "banner", text: t("truncated", { shown: D.shown, total: D.total }) })); }
  }

  function renderTiles() {
    var box = $("tiles");
    clear(box);
    function tile(label, n, status) {
      var nodes = [el("b", { text: String(n) })];
      nodes.push(status ? badge(status) : el("span", { text: label }));
      box.appendChild(el("div", { "class": "tile" }, nodes));
    }
    tile(t("tile_total"), D.total);
    ORDER.concat(Object.keys(D.statuses).filter(function (x) { return !GLYPH[x]; }).sort()).forEach(function (s) { if (D.statuses[s]) { tile("", D.statuses[s], s); } });
    tile(t("tile_skipped"), D.issues.count);
  }

  function statusCounts() {
    var c = Object.create(null);
    view.forEach(function (i) { var s = show(R[i][ST]); c[s] = (c[s] || 0) + 1; });
    return c;
  }
  function renderBars() {
    var box = $("chart-status"), c = statusCounts(), keys = ORDER.concat(Object.keys(c).filter(function (x) { return !GLYPH[x]; }).sort()).filter(function (x) { return c[x]; });
    var max = 1;
    clear(box);
    keys.forEach(function (k) { if (c[k] > max) { max = c[k]; } });
    if (!keys.length) { box.appendChild(el("p", { "class": "muted", text: t("chart_empty") })); }
    keys.forEach(function (k) {
      var g = GLYPH[k] || ["?", "?"], b = el("button", { type: "button", "class": "bar badge s-" + known(k), "aria-pressed": st.status === k ? "true" : "false", title: k }, [
        el("span", { "class": "lbl", text: g[0] + " " + g[1] + " " + k }), el("i", { style: "width:" + Math.max(1, Math.round(100 * c[k] / max)) + "%" }), el("span", { text: String(c[k]) })]);
      b.addEventListener("click", function () { st.status = st.status === k ? "" : k; $("f-status").value = st.status; refilter(); });
      box.appendChild(b);
    });
  }
  function svg(tag, attrs) {
    var n = document.createElementNS("http://www.w3.org/2000/svg", tag), k;
    for (k in attrs) { n.setAttribute(k, attrs[k]); }
    return n;
  }
  function renderTimeline() {
    var box = $("chart-time"), c = Object.create(null), months = [], max = 1;
    clear(box);
    view.forEach(function (i) { var d = R[i][DT]; if (d) { var m = d.slice(0, 7); c[m] = (c[m] || 0) + 1; } });
    months = Object.keys(c).sort();
    if (!months.length) { box.appendChild(el("p", { "class": "muted", text: t("chart_empty") })); return; }
    months.forEach(function (m) { if (c[m] > max) { max = c[m]; } });
    var w = Math.max(240, months.length * 14), h = 110, bw = w / months.length;
    var s = svg("svg", { viewBox: "0 0 " + w + " " + (h + 16), width: "100%", role: "img", preserveAspectRatio: "none", "aria-label": t("chart_timeline_desc", { first: months[0], last: months[months.length - 1], max: max }) });
    months.forEach(function (m, k) {
      var bh = Math.max(1, Math.round(h * c[m] / max)), r = svg("rect", { "class": "col", x: String(k * bw + 1), y: String(h - bh), width: String(Math.max(1, bw - 2)), height: String(bh) });
      var ti = svg("title", {}); ti.textContent = m + ": " + c[m]; r.appendChild(ti); s.appendChild(r);
    });
    var a = svg("text", { x: "0", y: String(h + 12) }); a.textContent = months[0]; s.appendChild(a);
    var z = svg("text", { x: String(w), y: String(h + 12), "text-anchor": "end" }); z.textContent = months[months.length - 1] + " (max " + max + ")"; s.appendChild(z);
    box.appendChild(s);
  }

  var COLS = [[ID, "col_id", ""], [ST, "col_status", ""], [PR, "col_protocol", ""], [DO, "col_domain", "hide-s"], [LV, "col_level", "hide-s"], [DT, "col_date", ""]];
  function renderHead() {
    var tr = $("head");
    clear(tr);
    COLS.forEach(function (c) {
      var b = el("button", { type: "button", text: t(c[1]) + (st.sort === c[0] ? (st.dir > 0 ? " \u25B2" : " \u25BC") : "") });
      b.addEventListener("click", function () {
        if (st.sort === c[0]) { st.dir = -st.dir; } else { st.sort = c[0]; st.dir = 1; }
        renderHead(); refilter();
      });
      tr.appendChild(el("th", { scope: "col", "class": c[2], "aria-sort": st.sort === c[0] ? (st.dir > 0 ? "ascending" : "descending") : "none" }, [b]));
    });
  }
  function renderTable() {
    var body = $("body"), pages = Math.max(1, Math.ceil(view.length / PAGE)), from = st.page * PAGE;
    clear(body);
    view.slice(from, from + PAGE).forEach(function (i, k) {
      var r = R[i], idb = el("button", { type: "button", "class": "idb", text: r[ID] });
      idb.addEventListener("click", function (ev) { ev.stopPropagation(); openRecord(i); });
      var tr = el("tr", { "class": (from + k === st.cur ? "cur " : "") + (i === st.open ? "sel" : ""), "data-i": String(i) }, [
        el("td", { "class": "id" }, [idb]), el("td", {}, [badge(show(r[ST]))]), el("td", { text: show(r[PR]) }),
        el("td", { "class": "hide-s", text: show(r[DO]) }), el("td", { "class": "hide-s", text: show(r[LV]) }), el("td", { text: r[DT] })]);
      tr.addEventListener("click", function () { st.cur = from + k; openRecord(i); });
      body.appendChild(tr);
    });
    $("empty").hidden = view.length > 0;
    $("prev").disabled = st.page <= 0;
    $("next").disabled = st.page >= pages - 1;
    $("page-info").textContent = t("page_info", { page: st.page + 1, pages: pages });
  }
  function renderResults() {
    $("count").textContent = t("result_count", { n: view.length, total: N });
    renderBars(); renderTimeline(); renderTable();
  }

  function rawOf(i, extra) {
    var r = R[i], o = {}, k;
    for (k in extra) { o[k] = extra[k]; }
    for (k in RAWKEYS) { if (r[k] !== null) { o[RAWKEYS[k]] = r[k]; } }
    var keys = Object.keys(o).sort(), s = {};
    keys.forEach(function (x) { s[x] = o[x]; });
    return s;
  }
  var blocks = {};
  function decodeBlock(b64) {
    if (typeof DecompressionStream === "undefined" || typeof Response === "undefined") { return Promise.reject(new Error("unsupported")); }
    var bin = atob(b64), bytes = new Uint8Array(bin.length), k;
    for (k = 0; k < bin.length; k++) { bytes[k] = bin.charCodeAt(k); }
    return new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"))).text().then(JSON.parse);
  }
  function detail(i) {
    var b = Math.floor(i / D.block);
    if (!blocks[b]) { blocks[b] = decodeBlock(D.blocks[b]); }
    return blocks[b].then(function (list) { return list[i % D.block]; });
  }
  function flash(msg) { $("live").textContent = msg; }
  function copy(text) {
    function fallback() {
      var ta = el("textarea", { "aria-hidden": "true", style: "position:fixed;left:-999px" });
      ta.value = text; document.body.appendChild(ta); ta.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(ta); flash(t(ok ? "copied" : "copy_failed"));
    }
    try {
      if (!navigator.clipboard) { fallback(); return; }
      navigator.clipboard.writeText(text).then(function () { flash(t("copied")); }, fallback);
    } catch (e) { fallback(); }
  }
  function fillDrawer(extra, note) {
    var r = R[st.open], dl = $("fields"), raw = rawOf(st.open, extra);
    clear(dl);
    Object.keys(raw).forEach(function (k) {
      var v = raw[k];
      dl.appendChild(el("dt", { text: k }));
      dl.appendChild(el("dd", { text: typeof v === "string" ? v : JSON.stringify(v, null, 1) }));
    });
    $("raw").textContent = JSON.stringify(raw, null, 2);
    $("drawer-note").textContent = note ? t(note) : "";
    return r;
  }
  function renderDrawer() {
    var d = $("drawer"), i = st.open;
    if (i < 0) { d.hidden = true; return; }
    $("drawer-id").textContent = R[i][ID];
    $("drawer-hash").textContent = t("hash_label") + ": " + R[i][SH];
    fillDrawer(null, "detail_loading");
    flash("");
    d.hidden = false;
    detail(i).then(function (extra) { if (st.open === i) { fillDrawer(extra, ""); } },
      function () { if (st.open === i) { fillDrawer(null, "detail_unavailable"); } });
  }
  function setHash(id) {
    var h = id === null ? location.pathname + location.search : "#" + encodeURIComponent(id);
    try { history.replaceState(null, "", h); } catch (e) { if (id !== null) { location.hash = encodeURIComponent(id); } }
  }
  function openRecord(i) {
    if (st.open < 0) { lastFocus = document.activeElement; }
    st.open = i; renderDrawer(); renderTable(); setHash(R[i][ID]);
    $("close").focus();
  }
  function closeDrawer() {
    if (st.open < 0) { return; }
    st.open = -1; renderDrawer(); renderTable(); setHash(null);
    if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
  }
  function fromHash() {
    var h = location.hash.slice(1), id;
    if (!h) { return; }
    try { id = decodeURIComponent(h); } catch (e) { return; }
    if (id in byId) { st.open = byId[id]; renderDrawer(); renderTable(); }
  }

  function move(delta) {
    if (!view.length) { return; }
    st.cur = Math.min(view.length - 1, Math.max(0, st.cur < 0 ? (delta > 0 ? 0 : view.length - 1) : st.cur + delta));
    st.page = Math.floor(st.cur / PAGE);
    renderTable();
    var row = $("body").querySelector("tr.cur");
    if (row && row.scrollIntoView) { row.scrollIntoView({ block: "nearest" }); }
  }
  function onKey(ev) {
    if (ev.ctrlKey || ev.metaKey || ev.altKey) { return; }
    var tag = ev.target && ev.target.tagName, typing = tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA";
    if (ev.key === "Escape") {
      if (st.open >= 0) { closeDrawer(); } else if (typing) { ev.target.blur(); }
      return;
    }
    if (typing) { return; }
    if (ev.key === "/") { ev.preventDefault(); $("q").focus(); }
    else if (ev.key === "j") { move(1); }
    else if (ev.key === "k") { move(-1); }
    else if (ev.key === "Enter" && tag !== "BUTTON" && st.cur >= 0 && st.cur < view.length) { openRecord(view[st.cur]); }
  }

  function applyTheme(v) {
    if (v === "light" || v === "dark") { document.documentElement.setAttribute("data-theme", v); }
  }
  function setLang(code) {
    if (!langs[code]) { return; }
    lang = code; L = langs[code]; store("atlas-lang", code);
    setStatic(); ["status", "domain", "level"].forEach(fillSelect);
    renderIntegrity(); renderTiles(); renderHead(); renderResults(); renderDrawer();
  }

  function init() {
    var saved = store("atlas-theme"), codes = Object.keys(langs).sort(), sel = $("lang");
    applyTheme(saved);
    var chosen = store("atlas-lang");
    if (chosen && langs[chosen]) { lang = chosen; }
    L = langs[lang];
    if (codes.length > 1) {
      $("lang-wrap").hidden = false;
      codes.forEach(function (c) { sel.appendChild(el("option", { value: c, text: langs[c]._name || c })); });
      sel.value = lang;
      sel.addEventListener("change", function () { setLang(sel.value); });
    }
    $("theme").addEventListener("click", function () {
      var dark = document.documentElement.getAttribute("data-theme") === "dark" || (!document.documentElement.getAttribute("data-theme") && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
      var next = dark ? "light" : "dark";
      applyTheme(next); store("atlas-theme", next);
    });
    buildHaystack();
    setStatic(); ["status", "domain", "level"].forEach(fillSelect);
    $("q").addEventListener("input", function () { st.q = this.value.trim().toLowerCase(); refilter(); });
    [["f-status", "status"], ["f-domain", "domain"], ["f-level", "level"], ["f-from", "from"], ["f-to", "to"]].forEach(function (p) {
      $(p[0]).addEventListener("change", function () { st[p[1]] = this.value; refilter(); });
    });
    $("reset").addEventListener("click", function () {
      st.q = st.status = st.domain = st.level = st.from = st.to = "";
      $("q").value = ""; $("f-from").value = ""; $("f-to").value = "";
      ["status", "domain", "level"].forEach(fillSelect); refilter();
    });
    $("prev").addEventListener("click", function () { if (st.page > 0) { st.page--; renderTable(); } });
    $("next").addEventListener("click", function () { st.page++; renderTable(); });
    $("close").addEventListener("click", closeDrawer);
    $("copy-id").addEventListener("click", function () { if (st.open >= 0) { copy(R[st.open][ID]); } });
    $("copy-hash").addEventListener("click", function () { if (st.open >= 0) { copy(R[st.open][SH]); } });
    $("copy-link").addEventListener("click", function () { if (st.open >= 0) { copy(location.href.split("#")[0] + "#" + encodeURIComponent(R[st.open][ID])); } });
    document.addEventListener("keydown", onKey);
    window.addEventListener("hashchange", fromHash);
    renderIntegrity(); renderTiles(); renderHead();
    refilter();
    fromHash();
  }
  init();
})();
