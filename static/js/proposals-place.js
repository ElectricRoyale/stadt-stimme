// „Vorschlag machen“, Schritt Einordnen: Ort allgemein, bekannte Einrichtung oder neuer Punkt auf
// der Karte (ADR-022). Zeigt das passende Feld; die Karte entsteht erst, wenn sie sichtbar wird.
// Klick oder „Kartenmitte setzen“ schreibt Breiten- und Längengrad in die versteckten Felder.
(function () {
  "use strict";

  var form = document.querySelector("form[data-compose]");
  var mapNode = form && form.querySelector("[data-pick-map]");
  if (!mapNode || !window.L || !window.StadtStimmeMap) return;

  var lat = form.elements.latitude;
  var lng = form.elements.longitude;
  var status = form.querySelector("[data-pick-status]");
  var defaultStatus = status.textContent;
  var radios = Array.prototype.slice.call(form.querySelectorAll("input[name='where']"));
  var map = null;
  var marker = null;

  function where() {
    var picked = radios.filter(function (r) { return r.checked; })[0];
    return picked ? picked.value : "allgemein";
  }

  function round(n) { return Math.round(n * 1e6) / 1e6; }

  function place(latlng) {
    lat.value = round(latlng.lat);
    lng.value = round(latlng.lng);
    if (marker) marker.setLatLng(latlng);
    else marker = L.marker(latlng, { icon: StadtStimmeMap.icon({ classes: "sq-pin prop-pick__pin", size: 22 }), keyboard: false }).addTo(map);
    status.textContent = "Ort gesetzt. Tippe erneut, um ihn zu verschieben.";
    form.dispatchEvent(new CustomEvent("place:set"));
  }

  function ensureMap() {
    if (map) { map.invalidateSize(); return; }
    var data = document.getElementById("v-karte-orte");
    var bounds = data ? JSON.parse(data.textContent) : [];
    map = StadtStimmeMap.create(mapNode, bounds);
    map.on("click", function (event) { place(event.latlng); });
    if (lat.value && lng.value) {
      var saved = L.latLng(Number(lat.value), Number(lng.value));
      place(saved);
      map.setView(saved, 16);
    }
  }

  function sync() {
    var current = where();
    form.querySelectorAll("[data-where-panel]").forEach(function (panel) {
      panel.hidden = panel.dataset.wherePanel !== current;
    });
    if (current === "neu") ensureMap();
  }

  form.querySelector("[data-pick-center]").addEventListener("click", function () {
    ensureMap();
    place(map.getCenter());
  });
  radios.forEach(function (r) { r.addEventListener("change", sync); });
  form.addEventListener("compose:step", function () { if (where() === "neu") ensureMap(); });
  if (!lat.value) status.textContent = defaultStatus;
  sync();
})();
