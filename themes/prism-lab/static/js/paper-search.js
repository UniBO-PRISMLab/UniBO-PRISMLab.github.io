// Prism Lab — client-side search & filtering for the publications page.
// Filters the already-rendered <li> items by text + year + type + area.
(function () {
  "use strict";

  var search  = document.getElementById("pub-search");
  var yearEl  = document.getElementById("pub-year");
  var typeEl  = document.getElementById("pub-type");
  var areaEl  = document.getElementById("pub-area");
  var list    = document.getElementById("pub-list");
  var empty   = document.getElementById("pub-empty");
  var visible = document.getElementById("pub-visible");
  if (!list) return;

  var items = Array.prototype.slice.call(list.querySelectorAll(".paper-item"));

  function tokens(q) {
    return q.toLowerCase().split(/\s+/).filter(Boolean);
  }

  function apply() {
    var qs   = tokens((search && search.value) || "");
    var year = (yearEl && yearEl.value) || "";
    var type = (typeEl && typeEl.value) || "";
    var area = (areaEl && areaEl.value) || "";
    var shown = 0;

    items.forEach(function (item) {
      var text = item.dataset.text || "";
      var matchText = qs.every(function (t) { return text.indexOf(t) !== -1; });
      var matchYear = !year || item.dataset.year === year;
      var matchType = !type || item.dataset.type === type;
      var matchArea = !area || (" " + (item.dataset.areas || "") + " ").indexOf(" " + area + " ") !== -1;
      var show = matchText && matchYear && matchType && matchArea;
      item.hidden = !show;
      if (show) shown++;
    });

    if (visible) visible.textContent = shown;
    if (empty)   empty.hidden = shown !== 0;
    if (list)    list.hidden  = shown === 0;
  }

  // Debounce text input to avoid thrashing with large lists.
  var timer = null;
  function schedule() {
    if (timer) clearTimeout(timer);
    timer = setTimeout(apply, 80);
  }

  if (search) search.addEventListener("input", schedule);
  [yearEl, typeEl, areaEl].forEach(function (el) {
    if (el) el.addEventListener("change", apply);
  });

  // Preserve state via the URL hash so links like /publications/#q=sciullo&year=2021 work.
  function readState() {
    var h = window.location.hash.replace(/^#/, "");
    if (!h) return;
    h.split("&").forEach(function (kv) {
      var pair = kv.split("=");
      if (!pair[0]) return;
      var val = decodeURIComponent(pair[1] || "");
      if (pair[0] === "q"    && search) search.value = val;
      if (pair[0] === "year" && yearEl) yearEl.value = val;
      if (pair[0] === "type" && typeEl) typeEl.value = val;
      if (pair[0] === "area" && areaEl) areaEl.value = val;
    });
    apply();
  }

  function writeState() {
    var parts = [];
    if (search && search.value) parts.push("q="    + encodeURIComponent(search.value));
    if (yearEl && yearEl.value) parts.push("year=" + encodeURIComponent(yearEl.value));
    if (typeEl && typeEl.value) parts.push("type=" + encodeURIComponent(typeEl.value));
    if (areaEl && areaEl.value) parts.push("area=" + encodeURIComponent(areaEl.value));
    var next = parts.length ? "#" + parts.join("&") : "";
    if (window.location.hash !== next) {
      history.replaceState(null, "", window.location.pathname + window.location.search + next);
    }
  }

  [search, yearEl, typeEl, areaEl].forEach(function (el) {
    if (el) el.addEventListener("change", writeState);
  });
  if (search) search.addEventListener("input", writeState);

  readState();
})();
