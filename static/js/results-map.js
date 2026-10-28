// Ergebnisse: Karte mit dem Unterschied je Einrichtung und Detailansicht. Ohne JavaScript
// wählen die Listenlinks per ?ort= aus; hier wird dasselbe ohne Neuladen gemacht.
(function () {
  "use strict";

  var dataNode = document.getElementById("res-map-data");
  var detail = document.getElementById("res-detail");
  var live = document.getElementById("res-live");
  if (!dataNode || !detail || !detail.querySelector("[data-field='name']")) return;

  var data = JSON.parse(dataNode.textContent);
  var rowsByKey = {};
  data.rows.forEach(function (r) { rowsByKey[r.key] = r; });
  var selected = new URLSearchParams(window.location.search).get("ort");
  if (!rowsByKey[selected]) selected = data.rows.length ? data.rows[0].key : null;

  function field(name) { return detail.querySelector("[data-field='" + name + "']"); }

  function setBar(name, value) {
    var bar = detail.querySelector("[data-bar='" + name + "']");
    bar.style.setProperty("--v", value);
    bar.style.setProperty("--max", data.scaleMax);
  }

  function showDetail(row) {
    field("mark").className = "res-mark cat-" + row.color + (row.isTheme ? " res-mark--theme" : "");
    field("kicker").textContent = row.kicker;
    field("name").textContent = row.name;
    field("wish").textContent = row.wish + " %";
    field("spend").textContent = row.spend + " %";
    field("summary").textContent = row.summary;
    var mine = field("mine");
    if (mine) mine.textContent = row.mine + " Punkte";
    var give = field("give");
    give.href = row.give;
    give.textContent = row.isTheme ? "Punkte an „" + row.name + " allgemein“ geben" : "Punkte geben";
    setBar("wish", row.wish);
    setBar("spend", row.spend);
  }

  // Karte (nur wenn Leaflet geladen ist)
  var mapNode = document.getElementById("res-map");
  var layer = null;
  if (mapNode && window.L && window.StadtStimmeMap) {
    var located = data.rows.filter(function (r) { return r.lat !== null; });
    var map = window.StadtStimmeMap.create(mapNode, located.map(function (r) { return [r.lat, r.lng]; }));
    layer = L.layerGroup().addTo(map);
  }

  function renderMap() {
    if (!layer) return;
    layer.clearLayers();
    data.rows.forEach(function (r) {
      if (r.lat === null) return;
      var label = r.name + ": " + r.wish + " Prozent der Punkte, " + r.spend + " Prozent der Ausgaben";
      var classes = "gap-pin gap-pin--" + r.tone + (r.key === selected ? " map-pin--selected" : "");
      window.StadtStimmeMap.pin(r.lat, r.lng, {
        label: label, text: r.gapText, classes: classes, onPick: function () { select(r.key, true); }
      }).addTo(layer);
    });
  }

  function select(key, focus) {
    var row = rowsByKey[key];
    if (!row) return;
    selected = key;
    showDetail(row);
    document.querySelectorAll("[data-select]").forEach(function (link) {
      if (link.dataset.select === key) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
    renderMap();
    if (window.history.replaceState) window.history.replaceState(null, "", "?ort=" + encodeURIComponent(key));
    if (live) live.textContent = row.name + " ausgewählt";
    if (focus) detail.focus();
  }

  document.querySelectorAll("[data-select]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      event.preventDefault();
      select(link.dataset.select, true);
    });
  });

  renderMap();
})();
