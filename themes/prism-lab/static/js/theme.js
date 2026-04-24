// Prism Lab — theme toggle + mobile nav
(function () {
  "use strict";

  // ---- Theme toggle (dark / light with localStorage) ----
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem("prism-theme"); } catch (e) {}
  var prefersLight =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: light)").matches;
  var initial = stored || (prefersLight ? "light" : "dark");
  root.setAttribute("data-theme", initial);

  function setTheme(next) {
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("prism-theme", next); } catch (e) {}
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    var cur = root.getAttribute("data-theme") === "light" ? "light" : "dark";
    setTheme(cur === "light" ? "dark" : "light");
  });

  // ---- Mobile nav (checkbox pattern is CSS-driven; this just closes on link tap) ----
  document.addEventListener("click", function (e) {
    var link = e.target.closest(".nav-primary .nav-link");
    if (!link) return;
    var cb = document.getElementById("nav-toggle");
    if (cb && cb.checked && window.matchMedia("(max-width: 720px)").matches) {
      cb.checked = false;
    }
  });
})();
