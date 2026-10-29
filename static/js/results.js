// Ergebnisse: Auswahl ohne Neuladen, Themenfilter, Ansicht „Nach Ort“/„Nach Thema“, Sortierung,
// Link teilen und Drucken. Rein zusätzlich: Ohne JavaScript wählen die Links per ?ort= aus und
// beide Listen stehen untereinander. Ereignisse am Wurzelelement für die Karte: „res:select“
// (gewählter Ort), „res:theme“ (Filter); die Karte meldet „res:pick“.
(function () {
  "use strict";

  var root = document.querySelector("[data-results]");
  if (!root) return;

  var details = Array.prototype.slice.call(root.querySelectorAll("[data-detail]"));
  var detailBox = document.getElementById("auswahl");
  var live = root.querySelector("[data-res-live]");
  var lists = root.querySelector("[data-lists]");
  var placeList = root.querySelector("[data-place-list]");
  var desktop = window.matchMedia("(min-width: 1024px)");
  var smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var current = (details.filter(function (d) { return !d.hidden; })[0] || {}).dataset;
  var state = { key: current ? current.detail : null, theme: "" };

  root.querySelectorAll("[data-js-only]").forEach(function (node) { node.hidden = false; });

  function emit(name, detail) { root.dispatchEvent(new CustomEvent(name, { detail: detail })); }
  function pressed(buttons, active) { buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b === active)); }); }

  // Auswahl
  function select(key, options) {
    var panel = details.filter(function (d) { return d.dataset.detail === key; })[0];
    if (!panel) return;
    state.key = key;
    details.forEach(function (d) { d.hidden = d !== panel; });
    root.querySelectorAll("[data-select]").forEach(function (link) {
      if (link.dataset.select === key) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
    if (window.history.replaceState) window.history.replaceState(null, "", "?ort=" + encodeURIComponent(key));
    if (live) live.textContent = panel.querySelector("h2").textContent + " ausgewählt";
    emit("res:select", { key: key });
    if (!options.focus) return;
    // Unter 1024 px steht die Auswahl unter der Karte: hinscrollen.
    if (!desktop.matches) detailBox.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" });
    detailBox.focus({ preventScroll: true });
  }

  root.addEventListener("click", function (event) {
    var link = event.target.closest("[data-select]");
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    select(link.dataset.select, { focus: true });
  });
  root.addEventListener("res:pick", function (event) { select(event.detail.key, { focus: true }); });

  // Themenfilter: Listen filtern, Karte dimmt die anderen Themen.
  var themeChips = Array.prototype.slice.call(root.querySelectorAll("[data-res-theme]"));
  var count = root.querySelector("[data-place-count]");
  function filter() {
    var shown = 0;
    root.querySelectorAll("[data-lists] [data-theme]").forEach(function (item) {
      item.hidden = !!state.theme && item.dataset.theme !== state.theme;
      if (!item.hidden && item.parentNode === placeList) shown += 1;
    });
    if (count) count.textContent = shown + " von " + count.dataset.total + " Einrichtungen";
    emit("res:theme", { theme: state.theme });
  }
  themeChips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      state.theme = chip.dataset.resTheme;
      pressed(themeChips, chip);
      filter();
    });
  });

  // Ansicht
  var viewButtons = Array.prototype.slice.call(root.querySelectorAll("[data-res-view]"));
  function showView(name) {
    root.querySelectorAll("[data-view]").forEach(function (view) { view.hidden = view.dataset.view !== name; });
    pressed(viewButtons, viewButtons.filter(function (b) { return b.dataset.resView === name; })[0]);
  }
  if (lists && viewButtons.length) {
    lists.classList.add("is-tabbed");
    viewButtons.forEach(function (b) { b.addEventListener("click", function () { showView(b.dataset.resView); }); });
    showView(state.key && state.key.indexOf("c-") === 0 ? "thema" : "ort");
  }

  // Sortierung der Orte
  var sortButtons = Array.prototype.slice.call(root.querySelectorAll("[data-res-sort]"));
  var compare = {
    gap: function (a, b) { return b.dataset.gap - a.dataset.gap || byName(a, b); },
    points: function (a, b) { return b.dataset.points - a.dataset.points || byName(a, b); },
    name: byName,
  };
  function byName(a, b) { return a.dataset.name.localeCompare(b.dataset.name, "de"); }
  sortButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      var items = Array.prototype.slice.call(placeList.querySelectorAll(":scope > li[data-theme]"));
      items.sort(compare[button.dataset.resSort]).forEach(function (item) { placeList.appendChild(item); });
      pressed(sortButtons, button);
    });
  });

  // Link teilen
  root.querySelectorAll("[data-copy-link]").forEach(function (button) {
    var label = button.querySelector("[data-copy-label]");
    button.addEventListener("click", function () {
      var done = function (text) {
        label.textContent = text;
        setTimeout(function () { label.textContent = "Link teilen"; }, 2000);
      };
      if (!navigator.clipboard) return done("Bitte die Adresszeile nutzen");
      navigator.clipboard.writeText(window.location.href).then(
        function () { done("Link kopiert"); },
        function () { done("Bitte die Adresszeile nutzen"); }
      );
    });
  });

  var print = root.querySelector("[data-res-print]");
  if (print) print.addEventListener("click", function () { window.print(); });

  // Rechte Spalte: Höhe für position: sticky (results.css).
  var side = root.querySelector("[data-side]");
  if (side && window.ResizeObserver) {
    new ResizeObserver(function () { side.style.setProperty("--side-height", side.offsetHeight + "px"); }).observe(side);
  }
})();
