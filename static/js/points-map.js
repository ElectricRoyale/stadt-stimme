// „Punkte verteilen“: Karte der Einrichtungen. Die Größe des Quadrats folgt deinen Punkten, grau
// heißt noch ohne Punkte. Zeile unter Maus oder Fokus markiert ihr Quadrat; ein Tipp auf ein
// Quadrat springt zur Zeile („dist:pick“). Werte vom Server (json_script), Texte nur über textContent.
(function () {
  "use strict";

  var form = document.querySelector("form[data-distribute]");
  var node = document.getElementById("dist-map");
  var dataNode = document.getElementById("dist-map-data");
  if (!form || !node || !dataNode || !window.L || !window.StadtStimmeMap) return;

  var places = JSON.parse(dataNode.textContent);
  var map = window.StadtStimmeMap.create(node, places.map(function (p) { return [p.lat, p.lng]; }));
  var markers = {};
  var state = { points: {}, focus: null, visible: null };
  var note = form.querySelector("[data-general-note]");

  function size(points) { return Math.round(Math.min(points > 0 ? 14 + points * 0.6 : 12, 64)); }

  places.forEach(function (p) {
    var marker = window.StadtStimmeMap.pin(p.lat, p.lng, {
      size: 12, fixedHit: true, label: p.name, classes: "sq-pin theme-" + (p.color || "sicherheit"),
      onPick: function () { form.dispatchEvent(new CustomEvent("dist:pick", { detail: { key: p.key } })); },
    });
    marker.bindTooltip(p.name, { direction: "top", offset: [0, -14] });
    marker.on("mouseover", function () { marker.openTooltip(); });
    marker.addTo(map);
    markers[p.key] = { marker: marker, place: p };
  });

  function render() {
    Object.keys(markers).forEach(function (key) {
      var entry = markers[key];
      var el = entry.marker.getElement();
      if (!el) return;
      var points = state.points[key] || 0;
      var hidden = state.visible !== null && state.visible.indexOf(key) < 0;
      el.classList.toggle("is-empty", points === 0);
      el.classList.toggle("is-selected", state.focus === key);
      el.classList.toggle("is-dim", hidden || (state.focus !== null && state.focus !== key));
      el.firstChild.style.setProperty("--size", size(points) + "px");
      var label = entry.place.name + ": " + (points > 0 ? points + " deiner Punkte" : "keine Punkte von dir") + ". Zur Zeile springen";
      el.setAttribute("title", label);
      el.setAttribute("aria-label", label);
      entry.marker.setZIndexOffset(state.focus === key ? 1000 : 0);
    });
    if (note) {
      var general = Object.keys(state.points).reduce(function (sum, key) {
        return key.indexOf("c-") === 0 ? sum + state.points[key] : sum;
      }, 0);
      note.textContent = general > 0 ? " " + general + " Punkte gehen an ganze Themen und haben keinen Ort auf der Karte." : "";
    }
  }

  function readInputs() {
    form.querySelectorAll("input[data-points]").forEach(function (input) {
      state.points[input.name] = parseInt(input.value, 10) || 0;
    });
  }

  form.addEventListener("dist:change", function (event) { state.points = event.detail.points; render(); });
  form.addEventListener("dist:filter", function (event) { state.visible = event.detail.visible; render(); });
  form.addEventListener("dist:focus", function (event) {
    var previous = state.focus;
    state.focus = event.detail.key;
    if (previous && markers[previous]) markers[previous].marker.closeTooltip();
    if (state.focus && markers[state.focus]) markers[state.focus].marker.openTooltip();
    render();
  });

  readInputs();
  render();
})();
