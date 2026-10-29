// Gemeinsame Kartenbasis für Übersicht, Verteilen und Ergebnisse: Leaflet mit Kachelserver aus den
// data-Attributen und Markern als divIcon. Texte nur über textContent.
(function () {
  "use strict";

  // Kacheln ohne API-Schlüssel (ADR-012). Lädt der erste Server keine einzige Kachel, kommt der
  // Ausweichserver; liefert auch der nichts, bleibt der ruhige Hintergrund mit den Markern.
  // Die Seite selbst sendet keinen Referer nach außen (SECURE_REFERRER_POLICY = same-origin),
  // OSM-Kachelserver verlangen ihn aber. Für Kacheln geht daher nur der Ursprung mit.
  var GIVE_UP_AFTER = 4;

  function tiles(map, node) {
    var sources = [
      { url: node.dataset.tiles, attribution: node.dataset.attribution },
      { url: node.dataset.tilesFallback, attribution: node.dataset.attributionFallback },
    ].filter(function (source) { return source.url; });
    var layer = null;

    function use(index) {
      if (layer) map.removeLayer(layer);
      var source = sources[index];
      if (!source) {
        node.classList.add("map-canvas--plain");
        return;
      }
      var loaded = false;
      var errors = 0;
      layer = L.tileLayer(source.url, {
        maxZoom: 19,
        attribution: source.attribution,
        referrerPolicy: "strict-origin-when-cross-origin",
      });
      layer.on("tileload", function () { loaded = true; });
      layer.on("tileerror", function () {
        errors += 1;
        if (!loaded && errors === GIVE_UP_AFTER) use(index + 1);
      });
      layer.addTo(map);
    }

    use(0);
  }

  function create(node, points) {
    node.textContent = "";
    var map = L.map(node, { scrollWheelZoom: false, zoomControl: true });
    tiles(map, node);
    if (points.length) map.fitBounds(points, { padding: [40, 40], maxZoom: 16 });
    else map.setView([51.16, 10.45], 6);
    return map;
  }

  // options.fixedHit: Trefferfläche bleibt 44 px, der Kreis darf darüber hinaus wachsen. So kann
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
