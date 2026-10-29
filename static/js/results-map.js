// Ergebnisse: ein Kreis je Einrichtung, rot wo Bürger mehr wollen, gold wo die Stadt mehr
// ausgibt, die Zahl darunter. Größe = Betrag der Lücke. Werte vom Server (json_script), Texte nur
// über textContent. Hört auf „res:select“ und „res:theme“, meldet „res:pick“ (results.js).
(function () {
  "use strict";

  var root = document.querySelector("[data-results]");
  var node = document.getElementById("res-map");
  var dataNode = document.getElementById("res-map-data");
  if (!root || !node || !dataNode || !window.L || !window.StadtStimmeMap) return;

  var data = JSON.parse(dataNode.textContent);
  var map = window.StadtStimmeMap.create(node, data.places.map(function (p) { return [p.lat, p.lng]; }));
  var shown = root.querySelector("[data-detail]:not([hidden])");
  var selected = shown ? shown.dataset.detail : null;
  var markers = {};
  var HIT = 44;
  var MAX = 56;

  function size(gap) { return Math.round(Math.min(10 + Math.abs(gap) * 1.5, MAX)); }

  function icon(place) {
    var wrap = document.createElement("span");
    var square = document.createElement("span");
    square.className = "gap-pin__square";
    square.style.setProperty("--size", size(place.gap) + "px");
    var label = document.createElement("span");
    label.className = "gap-pin__label";
    label.textContent = place.gapText;
    wrap.appendChild(square);
    wrap.appendChild(label);
    var height = Math.max(size(place.gap) + 20, HIT);
    var width = Math.max(size(place.gap), HIT);
    // Mitte des Kreises liegt auf dem Ort, die Zahl hängt darunter.
    return L.divIcon({
      className: "map-pin gap-pin tone-" + place.tone,
      html: wrap.innerHTML,
      iconSize: [width, height],
      iconAnchor: [width / 2, size(place.gap) / 2],
    });
  }

  data.places.forEach(function (place) {
    var label = place.name + ": Lücke " + place.gapText + " Prozentpunkte. Einzelheiten zeigen";
    var marker = L.marker([place.lat, place.lng], { icon: icon(place), title: label, alt: label, keyboard: true, riseOnHover: true });
    var pick = function () { root.dispatchEvent(new CustomEvent("res:pick", { detail: { key: place.key } })); };
    marker.on("click", pick);
    marker.on("keypress", function (e) { if (e.originalEvent.key === "Enter" || e.originalEvent.key === " ") pick(); });
    marker.bindTooltip(place.name, { direction: "top", offset: [0, -size(place.gap) / 2 - 4] });
    marker.addTo(map);
    markers[place.key] = { marker: marker, place: place };
  });

  function render(theme) {
    Object.keys(markers).forEach(function (key) {
      var entry = markers[key];
      var el = entry.marker.getElement();
      if (!el) return;
      el.classList.toggle("is-selected", key === selected);
      if (theme !== undefined) el.classList.toggle("is-dim", !!theme && String(entry.place.theme) !== theme);
      entry.marker.setZIndexOffset(key === selected ? 1000 : 0);
    });
  }

  root.addEventListener("res:select", function (event) { selected = event.detail.key; render(); });
  root.addEventListener("res:theme", function (event) { render(event.detail.theme); });
  render("");
})();
