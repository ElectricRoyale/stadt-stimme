// Vorschläge: Liste filtern (Schritt, Suche, Alle/Unterstützt/Meine, Thema) und sortieren.
// Rein zusätzlich: Ohne JavaScript filtern die Schritte per ?schritt=. Unterstützen: support-toggle.js.
(function () {
  "use strict";

  var root = document.querySelector("[data-proposals]");
  var list = root && root.querySelector("[data-list]");
  if (!list) return;

  var rows = Array.prototype.slice.call(list.querySelectorAll("[data-row]"));
  var holder = list.querySelector("[data-rows]");
  var count = list.querySelector("[data-list-count]");
  var empty = list.querySelector("[data-list-empty]");
  var stageNote = list.querySelector("[data-stage-note]");
  var ways = Array.prototype.slice.call(root.querySelectorAll("[data-way]"));
  var themes = Array.prototype.slice.call(list.querySelectorAll("[data-list-theme]"));
  var scopes = Array.prototype.slice.call(list.querySelectorAll("[data-list-scope]"));
  var query = list.querySelector("[data-list-query]");
  var sort = list.querySelector("[data-list-sort]");
  var current = ways.filter(function (w) { return w.getAttribute("aria-current") === "true"; })[0];
  var state = { stage: current ? current.dataset.way : "", theme: "", scope: "alle", query: "" };

  root.querySelectorAll("[data-js-only]").forEach(function (node) { node.hidden = false; });

  function pressed(buttons, active) { buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b === active)); }); }

  function matches(row) {
    var words = state.query.trim().toLocaleLowerCase("de");
    return (!state.stage || row.dataset.stage === state.stage)
      && (!state.theme || row.dataset.theme === state.theme)
      && (state.scope === "alle" || (state.scope === "meine" ? row.dataset.own : row.dataset.supported))
      && (!words || row.dataset.search.indexOf(words) >= 0);
  }

  function apply() {
    var shown = 0;
    rows.forEach(function (row) { row.hidden = !matches(row); if (!row.hidden) shown += 1; });
    count.textContent = "(" + shown + ")";
    empty.hidden = shown > 0;
    ways.forEach(function (w) {
      if (w.dataset.way === state.stage) w.setAttribute("aria-current", "true"); else w.removeAttribute("aria-current");
    });
    stageNote.hidden = !state.stage;
    if (state.stage) {
      var way = ways.filter(function (w) { return w.dataset.way === state.stage; })[0];
      stageNote.querySelector("[data-stage-name]").textContent = way.querySelector(".way-step__label").textContent;
    }
  }

  var order = {
    support: function (a, b) { return b.dataset.supports - a.dataset.supports || b.dataset.created - a.dataset.created; },
    "new": function (a, b) { return b.dataset.created - a.dataset.created; },
    old: function (a, b) { return a.dataset.created - b.dataset.created; },
  };
  function resort() {
    var own = rows.filter(function (r) { return r.dataset.own; });
    var others = rows.filter(function (r) { return !r.dataset.own; });
    own.sort(order[sort.value]).concat(others.sort(order[sort.value])).forEach(function (row) { holder.appendChild(row); });
  }

  ways.forEach(function (way) {
    way.addEventListener("click", function (event) {
      event.preventDefault();
      state.stage = state.stage === way.dataset.way ? "" : way.dataset.way;
      if (window.history.replaceState) window.history.replaceState(null, "", state.stage ? "?schritt=" + state.stage : window.location.pathname);
      apply();
    });
  });
  stageNote.querySelector("[data-stage-clear]").addEventListener("click", function (event) {
    event.preventDefault();
    state.stage = "";
    apply();
  });
  themes.forEach(function (chip) {
    chip.addEventListener("click", function () { state.theme = chip.dataset.listTheme; pressed(themes, chip); apply(); });
  });
  scopes.forEach(function (button) {
    button.addEventListener("click", function () { state.scope = button.dataset.listScope; pressed(scopes, button); apply(); });
  });
  query.addEventListener("input", function () { state.query = query.value; apply(); });
  sort.addEventListener("change", resort);

  apply();
})();
