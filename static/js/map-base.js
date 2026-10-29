// Gemeinsame Kartenbasis für Übersicht und Ergebnisse: Leaflet mit Kachelserver aus den
// data-Attributen und Markern als divIcon. Texte nur über textContent.
(function () {
  "use strict";

  function create(node, points) {
    node.textContent = "";
    var map = L.map(node, { scrollWheelZoom: false, zoomControl: true });
    // Die Seite selbst sendet keinen Referer nach außen (SECURE_REFERRER_POLICY = same-origin).
    // Kachelserver wie OpenStreetMap verlangen ihn aber, sonst kommt "Access blocked".
    // Für Kacheln geht daher nur der Ursprung (ohne Pfad) mit.
    L.tileLayer(node.dataset.tiles, {
      maxZoom: 19,
      attribution: node.dataset.attribution,
      referrerPolicy: "strict-origin-when-cross-origin",
    }).addTo(map);
    if (points.length) map.fitBounds(points, { padding: [40, 40], maxZoom: 16 });
    else map.setView([51.16, 10.45], 6);
    return map;
  }

  // options.fixedHit: Trefferfläche bleibt 44 px, das Quadrat darf darüber hinaus wachsen. So kann
  // eine Seite die Größe später am Element ändern, ohne den Marker neu zu bauen.
  function icon(options) {
    var span = document.createElement("span");
    span.textContent = options.text || "";
    if (options.size) span.style.setProperty("--size", options.size + "px");
    var hit = options.fixedHit ? 44 : Math.max(options.size || 0, 44);
    return L.divIcon({ className: "map-pin " + options.classes, html: span.outerHTML, iconSize: [hit, hit] });
  }

  function pin(lat, lng, options) {
    var marker = L.marker([lat, lng], { icon: icon(options), title: options.label, alt: options.label, keyboard: true, riseOnHover: true });
    marker.on("click", options.onPick);
    marker.on("keypress", function (e) {
      if (e.originalEvent.key === "Enter" || e.originalEvent.key === " ") options.onPick();
    });
    return marker;
  }

  window.StadtStimmeMap = { create: create, pin: pin, icon: icon };
})();
