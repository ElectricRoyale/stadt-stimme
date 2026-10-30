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

  // Zoomen mit Strg/⌘ + Mausrad und Touchpad-Pinch; ein normales Mausrad scrollt weiter die
  // Seite. Chrome, Edge und Firefox melden Pinch als Mausrad mit ctrlKey, Safari als Geste.
  var HINT_MS = 1500;
  var MODIFIER = /Mac|iPhone|iPad/.test(navigator.platform) ? "⌘" : "Strg";

  function wheelWithModifier(map, node) {
    var hint = document.createElement("p");
    hint.className = "map-canvas__hint";
    hint.setAttribute("aria-hidden", "true");
    hint.textContent = "Zum Zoomen " + MODIFIER + " gedrückt halten und scrollen";
    node.appendChild(hint);
    var timer = null;

    // Vor Leaflets eigenem Handler: ohne Taste bekommt Leaflet das Ereignis nicht.
    node.addEventListener("wheel", function (e) {
      if (e.ctrlKey || e.metaKey) {
        hint.classList.remove("is-visible");
        return;
      }
      e.stopImmediatePropagation();
      hint.classList.add("is-visible");
      clearTimeout(timer);
      timer = setTimeout(function () { hint.classList.remove("is-visible"); }, HINT_MS);
    }, { capture: true, passive: true });
  }

  function safariPinch(map, node) {
    var startZoom = null;
    var around = null;
    node.addEventListener("gesturestart", function (e) {
      e.preventDefault();
      startZoom = map.getZoom();
      around = map.mouseEventToContainerPoint(e);
    });
    node.addEventListener("gesturechange", function (e) { e.preventDefault(); });
    node.addEventListener("gestureend", function (e) {
      e.preventDefault();
      if (startZoom === null || !e.scale) return;
      map.setZoomAround(around, Math.round(startZoom + Math.log2(e.scale)));
      startZoom = null;
    });
  }

  function create(node, points) {
    node.textContent = "";
    var map = L.map(node, { scrollWheelZoom: true, zoomControl: true });
    wheelWithModifier(map, node);
    safariPinch(map, node);
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
