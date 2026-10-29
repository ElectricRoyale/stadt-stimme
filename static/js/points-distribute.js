// „Punkte verteilen“: −/+ in Fünferschritten, Restpunkte, die 100 Quadrate, der Vergleich mit dem
// Haushalt und der Speicherstand, alles live. Rein zusätzlich: Ohne JavaScript bleiben Zahlenfelder
// und Speichern voll nutzbar; der Server prüft die 100-Punkte-Grenze (ADR-011).
// Ereignisse am Formular für Karte und Filter: „dist:change“ (Punkte je Ziel), „dist:focus“
// (Ziel unter Maus oder Fokus); die Karte meldet „dist:pick“ (zur Zeile springen).
(function () {
  "use strict";

  var form = document.querySelector("form[data-distribute]");
  if (!form) return;

  var budget = Number(form.dataset.budget);
  var step = Number(form.dataset.step) || 1;
  var inputs = Array.prototype.slice.call(form.querySelectorAll("input[data-points]"));
  var rows = Array.prototype.slice.call(form.querySelectorAll("[data-target]"));
  var initial = {};
  inputs.forEach(function (input) { initial[input.name] = valueOf(input); });
  var savedText = (form.querySelector("[data-save-status]") || {}).textContent || "";
  var FLASH_MS = 1600;

  function valueOf(input) {
    var value = parseInt(input.value, 10);
    return isNaN(value) || value < 0 ? 0 : value;
  }

  function total(except) {
    return inputs.reduce(function (sum, input) { return input === except ? sum : sum + valueOf(input); }, 0);
  }

  function each(selector, fn) { form.querySelectorAll(selector).forEach(fn); }
  function setText(selector, text) { each(selector, function (node) { node.textContent = text; }); }
  function plural(n, one, many) { return n === 1 ? one : many; }

  // Ein Feld bekommt höchstens, was neben den anderen noch frei ist.
  function clamp(input, wanted) {
    input.value = String(Math.max(0, Math.min(wanted, budget - total(input))));
  }

  function points() {
    var map = {};
    inputs.forEach(function (input) { map[input.name] = valueOf(input); });
    return map;
  }

  function renderRows(remaining) {
    rows.forEach(function (row) {
      var input = row.querySelector("input[data-points]");
      var value = valueOf(input);
      row.classList.toggle("is-given", value > 0);
      input.classList.toggle("is-zero", value === 0);
      row.querySelector('[data-step="-1"]').disabled = value === 0;
      row.querySelector('[data-step="1"]').disabled = remaining === 0;
    });
  }

  function themeSums() {
    var sums = {};
    each("[data-theme]", function (section) {
      var sum = 0;
      section.querySelectorAll("input[data-points]").forEach(function (input) { sum += valueOf(input); });
      sums[section.dataset.theme] = sum;
      section.querySelectorAll("[data-theme-sum]").forEach(function (node) { node.textContent = String(sum); });
    });
    return sums;
  }

  // Je Thema erst die Einrichtungen, dann „… allgemein“, wie auf dem Server (ledger_cells).
  function renderLedger(used) {
    var grid = form.querySelector("[data-ledger]");
    if (!grid) return;
    var cells = [];
    each("[data-theme]", function (section) {
      var targets = Array.prototype.slice.call(section.querySelectorAll("[data-target]"));
      var general = targets.filter(function (t) { return t.dataset.target.indexOf("c-") === 0; });
      var places = targets.filter(function (t) { return general.indexOf(t) < 0; });
      places.concat(general).forEach(function (target) {
        var n = valueOf(target.querySelector("input[data-points]"));
        for (var i = 0; i < n; i++) cells.push({ key: target.dataset.target, general: general.indexOf(target) >= 0 });
      });
    });
    var nodes = grid.children;
    for (var i = 0; i < nodes.length; i++) {
      var cell = cells[i];
      var node = nodes[i];
      var was = node.dataset.key || "";
      var key = cell ? cell.key : "";
      if (was === key) continue;
      node.className = "ledger__cell" + (cell ? " is-given" + (cell.general ? " is-general" : "") : "");
      if (cell) node.dataset.key = key; else delete node.dataset.key;
    }
    grid.setAttribute("aria-label", used + " von " + budget + " Punkten vergeben, " + (budget - used) + " frei");
  }

  function renderLedgerThemes(sums) {
    each("[data-ledger-theme]", function (item) {
      var value = item.querySelector("[data-theme-sum]");
      value.classList.toggle("is-given", sums[item.dataset.ledgerTheme] > 0);
    });
  }

  function renderCompare(sums, used) {
    var lead = null;
    each("[data-compare-theme]", function (item) {
      var mine = sums[item.dataset.compareTheme] || 0;
      var spend = Number(item.dataset.spend);
      item.querySelector("[data-theme-bar]").style.width = Math.min(mine, 100) + "%";
      if (mine > spend && (!lead || mine - spend > lead.mine - lead.spend)) lead = { name: item.dataset.name, mine: mine, spend: spend };
    });
    var node = form.querySelector("[data-compare-lead]");
    if (!node) return;
    var year = node.dataset.year;
    node.textContent = "";
    if (lead) {
      node.appendChild(document.createTextNode("Du gibst "));
      var strong = document.createElement("strong");
      strong.textContent = lead.name;
      node.appendChild(strong);
      node.appendChild(document.createTextNode(" " + lead.mine + " von " + budget + " Punkten." + (year ? " Im Haushalt " + year + " bekam das Thema " + lead.spend + " %." : "")));
    } else {
      node.textContent = used ? "Deine Punkte folgen ungefähr dem Haushalt" + (year ? " " + year : "") + "." : "Noch keine Punkte vergeben.";
    }
  }

  function changes() {
    return inputs.filter(function (input) { return valueOf(input) !== initial[input.name]; }).length;
  }

  function renderSave(remaining) {
    var count = changes();
    var text = savedText;
    if (count > 0) {
      text = plural(count, "1 Änderung", count + " Änderungen") + " noch nicht gespeichert"
        + (remaining > 0 ? ", " + remaining + " Punkte frei. Du kannst trotzdem speichern." : ".");
    }
    each("[data-save-submit]", function (button) { button.disabled = count === 0; });
    each("[data-save-reset]", function (button) { button.hidden = count === 0; });
    each("[data-save-status]", function (node) {
      node.textContent = text;
      node.classList.toggle("is-changed", count > 0);
    });
    var bar = form.querySelector("[data-save-bar]");
    if (bar) bar.hidden = count === 0;
    form.classList.toggle("has-changes", count > 0);
  }

  function render() {
    var used = total(null);
    var remaining = Math.max(budget - used, 0);
    setText("[data-remaining]", String(remaining));
    setText("[data-used]", String(used));
    setText("[data-state-sentence]", remaining > 0
      ? "Du hast " + used + " von " + budget + " Punkten vergeben, " + remaining + " sind noch frei."
      : "Alle " + budget + " Punkte sind vergeben. Du kannst jederzeit umverteilen.");
    renderRows(remaining);
    var sums = themeSums();
    renderLedger(used);
    renderLedgerThemes(sums);
    renderCompare(sums, used);
    renderSave(remaining);
    form.dispatchEvent(new CustomEvent("dist:change", { detail: { points: points() } }));
  }

  // Eingaben
  rows.forEach(function (row) {
    var input = row.querySelector("input[data-points]");
    row.querySelectorAll("[data-step]").forEach(function (button) {
      button.hidden = false;
      button.addEventListener("click", function () {
        clamp(input, valueOf(input) + Number(button.dataset.step) * step);
        render();
      });
    });
    input.addEventListener("input", function () {
      input.value = input.value.replace(/\D/g, "").slice(0, 3);
    });
    input.addEventListener("change", function () { clamp(input, valueOf(input)); render(); });
    input.addEventListener("focus", function () { input.select(); });
    input.addEventListener("keydown", function (event) {
      if (event.key === "ArrowUp" || event.key === "ArrowDown") {
        event.preventDefault();
        clamp(input, valueOf(input) + (event.key === "ArrowUp" ? 1 : -1));
        render();
      }
    });
  });

  each("[data-save-reset]", function (button) {
    button.addEventListener("click", function () {
      inputs.forEach(function (input) { input.value = String(initial[input.name]); });
      render();
    });
  });

  // Fokus: Zeile unter Maus oder Tastatur hebt ihre Quadrate hervor.
  function setFocus(key) {
    var grid = form.querySelector("[data-ledger]");
    if (grid) {
      grid.classList.toggle("is-focus", !!key);
      Array.prototype.forEach.call(grid.children, function (cell) { cell.classList.toggle("is-focus", !!key && cell.dataset.key === key); });
    }
    var theme = key ? form.querySelector("#ziel-" + key).closest("[data-theme]").dataset.theme : null;
    each("[data-ledger-theme]", function (item) { item.classList.toggle("is-dim", !!theme && item.dataset.ledgerTheme !== theme); });
    rows.forEach(function (row) { row.classList.toggle("is-focus", row.dataset.target === key); });
    form.dispatchEvent(new CustomEvent("dist:focus", { detail: { key: key } }));
  }

  rows.forEach(function (row) {
    var key = row.dataset.target;
    row.addEventListener("mouseenter", function () { setFocus(key); });
    row.addEventListener("mouseleave", function () { setFocus(null); });
    row.addEventListener("focusin", function () { setFocus(key); });
    row.addEventListener("focusout", function () { setFocus(null); });
  });

  // Von der Karte zur Zeile: sichtbar machen, hinscrollen, Fokus ins Zahlenfeld, kurz markieren.
  var flashTimer = null;
  form.addEventListener("dist:pick", function (event) {
    var row = form.querySelector("#ziel-" + event.detail.key);
    if (!row) return;
    var smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    row.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "center" });
    row.querySelector("input[data-points]").focus({ preventScroll: true });
    rows.forEach(function (r) { r.classList.remove("is-flash"); });
    row.classList.add("is-flash");
    clearTimeout(flashTimer);
    flashTimer = setTimeout(function () { row.classList.remove("is-flash"); }, FLASH_MS);
  });

  // Rechte Leiste: Höhe für position: sticky (points.css).
  var rail = form.querySelector("[data-rail]");
  if (rail && window.ResizeObserver) {
    new ResizeObserver(function () {
      rail.style.setProperty("--rail-height", rail.offsetHeight + "px");
    }).observe(rail);
  }

  render();
})();
