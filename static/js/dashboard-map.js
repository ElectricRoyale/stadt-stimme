// Dashboard: Karte mit Einrichtungen (Ebene „Gebäude & Orte“) oder Themen (Ebene „Bereiche“),
// Filter und Detailansicht. Die Werte kommen vom Server (json_script); Texte nur über textContent.
(function () {
  "use strict";

  var dataNode = document.getElementById("dash-map-data");
  var mapNode = document.getElementById("dash-map");
  var detail = document.getElementById("dash-detail");
  if (!dataNode || !mapNode || !detail || !window.L || !window.StadtStimmeMap) return;

  var data = JSON.parse(dataNode.textContent);
  var loggedIn = mapNode.dataset.loggedIn === "1";
  var state = { layer: "orte", theme: null, mine: false, selected: null };
  var placesByKey = {};
  var themesById = {};
  var themesByKey = {};
  data.places.forEach(function (p) { placesByKey[p.key] = p; });
  data.themes.forEach(function (t) { themesById[t.id] = t; themesByKey[t.key] = t; });

  document.querySelectorAll("[data-js-only]").forEach(function (node) { node.hidden = false; });
  document.querySelectorAll("[data-select]").forEach(function (node) { node.disabled = false; });

  // Karte
  var map = window.StadtStimmeMap.create(mapNode, data.places.map(function (p) { return [p.lat, p.lng]; }));
  var layer = L.layerGroup().addTo(map);

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function pin(lat, lng, size, label, text, classes, onPick) {
    return window.StadtStimmeMap.pin(lat, lng, { size: size, label: label, text: text, classes: classes, onPick: onPick });
  }

  function render() {
    layer.clearLayers();
    if (state.layer === "orte") {
      data.places.forEach(function (p) {
        var value = state.mine ? p.mine : p.share;
        if (state.mine && value === 0) return;
        var dim = state.theme !== null && state.theme !== p.theme;
        var size = Math.max(30, Math.round(28 + value * 1.4));
        var label = p.name + ": " + (state.mine ? value + " deiner Punkte" : value + " Prozent aller Punkte");
        var classes = "cat-" + p.color + (dim ? " map-pin--dim" : "") + (state.selected === p.key ? " map-pin--selected" : "");
        pin(p.lat, p.lng, size, label, value + (state.mine ? " P." : " %"), classes, function () { select(p.key); }).addTo(layer);
      });
    } else {
      data.themes.forEach(function (t) {
        var value = state.mine ? t.mine : t.share;
        if (t.lat === null || value === 0) return;
        var size = Math.round(44 + value * 2);
        var label = t.name + ": " + (state.mine ? value + " deiner Punkte" : value + " Prozent aller Punkte");
        var classes = "map-pin--area cat-" + t.color + (state.selected === t.key ? " map-pin--selected" : "");
        pin(t.lat, t.lng, size, label, value + (state.mine ? " P." : " %"), classes, function () { select(t.key); }).addTo(layer);
      });
    }
  }

  function setPressed(selector, isPressed) {
    document.querySelectorAll(selector).forEach(function (button) {
      button.setAttribute("aria-pressed", String(isPressed(button)));
    });
  }

  function syncControls() {
    setPressed("[data-layer]", function (b) { return b.dataset.layer === state.layer; });
    setPressed("[data-filter-theme]", function (b) {
      return b.dataset.filterTheme === (state.theme === null ? "" : String(state.theme));
    });
    setPressed("[data-filter-mine]", function () { return state.mine; });
  }

  // Detail
  function tag(text, tone) { return el("span", "ss-tag tone-" + tone, text); }

  function figure(value, label, className) {
    var wrap = el("span", className || "");
    wrap.appendChild(el("strong", "", value));
    wrap.appendChild(document.createTextNode(label));
    return wrap;
  }

  function closeButton() {
    var button = el("button", "dash-detail__close");
    button.type = "button";
    button.setAttribute("aria-label", "Details schließen");
    button.textContent = "×";
    button.addEventListener("click", function () { select(null); });
    return button;
  }

  function header(kind) {
    var top = el("div", "dash-detail__top");
    top.appendChild(tag(kind, "idea"));
    top.appendChild(closeButton());
    return top;
  }

  function giveLink(key, text) {
    var link = el("a", "ss-btn ss-btn--primary", text);
    link.href = "/verteilen/#id_" + key;
    return link;
  }

  function renderPlace(p) {
    var theme = themesById[p.theme];
    detail.appendChild(header("Einrichtung"));
    var title = el("h2", "", p.name);
    title.id = "dash-detail-title";
    detail.appendChild(title);
    var figures = el("div", "dash-detail__figures");
    figures.appendChild(figure(p.share + " %", "aller Bürgerpunkte"));
    if (loggedIn) figures.appendChild(figure(p.mine + " P.", "von dir", "is-mine"));
    detail.appendChild(figures);
    if (p.measures.length) {
      detail.appendChild(el("h3", "ss-eyebrow", "Darin fließen die Punkte"));
      var list = el("ul");
      p.measures.forEach(function (m) {
        var item = el("li");
        item.appendChild(el("span", "", m.title));
        item.appendChild(tag(m.status, m.tone));
        list.appendChild(item);
      });
      detail.appendChild(list);
    }
    var toTheme = el("button", "ss-btn--ghost dash-detail__theme", "Teil des Themas " + theme.name + " (" + theme.share + " %)");
    toTheme.type = "button";
    toTheme.addEventListener("click", function () { select(theme.key); });
    detail.appendChild(toTheme);
    var actions = el("div", "dash-detail__actions");
    actions.appendChild(giveLink(p.key, "Punkte geben"));
    detail.appendChild(actions);
  }

  function renderTheme(t) {
    detail.appendChild(header("Thema"));
    var title = el("h2", "cat-" + t.color);
    title.id = "dash-detail-title";
    title.appendChild(el("span", "dot"));
    title.appendChild(document.createTextNode(t.name));
    detail.appendChild(title);
    var figures = el("div", "dash-detail__figures");
    figures.appendChild(figure(t.share + " %", "aller Bürgerpunkte"));
    figures.appendChild(figure(t.generalShare + " %", "für das ganze Thema"));
    if (loggedIn) figures.appendChild(figure(t.mine + " P.", "von dir", "is-mine"));
    detail.appendChild(figures);
    var list = el("ul");
    t.places.forEach(function (key) {
      var p = placesByKey[key];
      var item = el("li");
      var button = el("button", "ss-btn--ghost", p.name);
      button.type = "button";
      button.addEventListener("click", function () { select(key); });
      item.appendChild(button);
      item.appendChild(el("strong", "", p.share + " %"));
      list.appendChild(item);
    });
    detail.appendChild(list);
    detail.appendChild(el("p", "", "Punkte für das ganze Thema verteilt die Stadt auf alle Vorhaben darin, auch auf neue."));
    var actions = el("div", "dash-detail__actions");
    actions.appendChild(giveLink(t.key, "Punkte an „" + t.name + " allgemein“ geben"));
    detail.appendChild(actions);
  }

  function select(key) {
    state.selected = key;
    detail.textContent = "";
    var place = key && placesByKey[key];
    var theme = key && themesByKey[key];
    if (place) renderPlace(place);
    else if (theme) renderTheme(theme);
    detail.hidden = !(place || theme);
    if (place) state.theme = place.theme;
    if (theme) state.theme = theme.id;
    if (!key) state.theme = null;
    syncControls();
    render();
    if (!detail.hidden) detail.focus({ preventScroll: false });
  }

  document.querySelectorAll("[data-layer]").forEach(function (button) {
    button.addEventListener("click", function () { state.layer = button.dataset.layer; syncControls(); render(); });
  });
  document.querySelectorAll("[data-filter-theme]").forEach(function (button) {
    button.addEventListener("click", function () {
      var id = button.dataset.filterTheme;
      if (id === "") select(null);
      else select(themesById[id].key);
    });
  });
  document.querySelectorAll("[data-filter-mine]").forEach(function (button) {
    button.addEventListener("click", function () { state.mine = !state.mine; syncControls(); render(); });
  });
  document.querySelectorAll("[data-select]").forEach(function (button) {
    button.addEventListener("click", function () { select(button.dataset.select); });
  });

  syncControls();
  render();
})();
