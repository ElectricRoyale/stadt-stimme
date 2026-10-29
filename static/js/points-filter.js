// „Punkte verteilen“: Suche, „Nur mit meinen Punkten“ und Themenfilter für die Liste. Verborgene
// Zeilen behalten ihre Werte und werden mitgespeichert. Meldet „dist:filter“ an die Karte.
(function () {
  "use strict";

  var form = document.querySelector("form[data-distribute]");
  var bar = form && form.querySelector("[data-filters]");
  if (!bar) return;

  var query = bar.querySelector("[data-filter-query]");
  var mine = bar.querySelector("[data-filter-mine]");
  var chips = Array.prototype.slice.call(bar.querySelectorAll("[data-filter-theme]"));
  var count = bar.querySelector("[data-filter-count]");
  var empty = form.querySelector("[data-filter-empty]");
  var total = Number(count.dataset.total);
  var state = { query: "", theme: "", mine: false };

  bar.hidden = false;

  function hasPoints(row) {
    var input = row.querySelector("input[data-points]");
    return (parseInt(input.value, 10) || 0) > 0 || (parseInt(input.defaultValue, 10) || 0) > 0;
  }

  function matches(row, theme) {
    var words = state.query.trim().toLocaleLowerCase("de");
    return (!state.theme || state.theme === theme)
      && (!state.mine || hasPoints(row))
      && (!words || row.dataset.search.indexOf(words) >= 0);
  }

  function apply() {
    var visible = [];
    form.querySelectorAll("[data-theme]").forEach(function (section) {
      var shown = 0;
      section.querySelectorAll("[data-target]").forEach(function (row) {
        var ok = matches(row, section.dataset.theme);
        row.hidden = !ok;
        if (ok) { shown += 1; visible.push(row.dataset.target); }
      });
      section.hidden = shown === 0;
    });
    count.textContent = visible.length === total
      ? "Alle " + total + " Ziele: Einrichtungen und ganze Themen"
      : visible.length + " von " + total + " Zielen";
    if (empty) empty.hidden = visible.length > 0;
    form.dispatchEvent(new CustomEvent("dist:filter", { detail: { visible: visible } }));
  }

  function reset() {
    state = { query: "", theme: "", mine: false };
    query.value = "";
    mine.checked = false;
    chips.forEach(function (chip) { chip.setAttribute("aria-pressed", String(chip.dataset.filterTheme === "")); });
    apply();
  }

  query.addEventListener("input", function () { state.query = query.value; apply(); });
  // Enter in der Suche soll nicht das Formular absenden.
  query.addEventListener("keydown", function (event) { if (event.key === "Enter") event.preventDefault(); });
  mine.addEventListener("change", function () { state.mine = mine.checked; apply(); });
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      state.theme = chip.dataset.filterTheme;
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      apply();
    });
  });
  if (empty) empty.querySelector("[data-filter-reset]").addEventListener("click", reset);

  // Die Karte springt zu einer Zeile, die ein Filter verbirgt: Filter aufheben.
  form.addEventListener("dist:pick", function (event) {
    var row = form.querySelector("#ziel-" + event.detail.key);
    if (row && row.hidden) reset();
  }, true);
})();
