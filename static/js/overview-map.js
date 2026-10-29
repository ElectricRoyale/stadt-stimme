// Übersicht: Einrichtungen als Quadrate auf der Karte, Rangliste darunter und Detail zur Auswahl.
// Ein geöffnetes Thema in „Wunsch und Haushalt“ blendet die übrigen Einrichtungen ab.
// Die Werte kommen vom Server (json_script); Texte nur über textContent.
(function () {
  "use strict";

  var dataNode = document.getElementById("ov-map-data");
  var mapNode = document.getElementById("ov-map");
  var rank = document.getElementById("ov-rank");
  var detail = document.getElementById("ov-map-detail");
  if (!dataNode || !mapNode || !rank || !detail) return;

  var places = JSON.parse(dataNode.textContent).places;
  var loggedIn = mapNode.dataset.loggedIn === "1";
  var hint = document.getElementById("karte-hinweis");
  var state = { scope: "alle", theme: null, selected: null };
  var byKey = {};
  places.forEach(function (p) { byKey[p.key] = p; });

  document.querySelectorAll("#karte [data-js-only]").forEach(function (node) { node.hidden = false; });
  rank.querySelectorAll("[data-select]").forEach(function (button) {
    button.disabled = !byKey[button.dataset.select];
  });

  var located = places.filter(function (p) { return p.lat !== null; });
  var layer = null;
  if (window.L && window.StadtStimmeMap) {
    var map = window.StadtStimmeMap.create(mapNode, located.map(function (p) { return [p.lat, p.lng]; }));
    layer = L.layerGroup().addTo(map);
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function mine() { return state.scope === "meine"; }

  function renderMarkers() {
    if (!layer) return;
    layer.clearLayers();
    located.forEach(function (p) {
      var size = mine() ? (p.mine > 0 ? 14 + p.mine * 0.9 : 12) : 14 + p.share * 1.5;
      var classes = "sq-pin"
        + (mine() && p.mine === 0 ? " is-empty" : "")
        + (state.theme !== null && state.theme !== p.theme ? " is-dim" : "")
        + (state.selected === p.key ? " is-selected" : "");
      var label = p.name + ": " + (mine() ? p.mine + " deiner Punkte" : p.share + " Prozent aller Bürgerpunkte");
      window.StadtStimmeMap.pin(p.lat, p.lng, {
        size: Math.round(Math.min(size, 64)), label: label, text: "", classes: classes,
        onPick: function () { select(state.selected === p.key ? null : p.key); },
      }).addTo(layer);
    });
  }

  function renderRank() {
    rank.querySelectorAll("li[data-theme]").forEach(function (item) {
      var value = item.querySelector(".ov-rank__value");
      value.textContent = mine() ? value.dataset.mine : value.dataset.all;
      item.classList.toggle("is-dim", state.theme !== null && String(state.theme) !== item.dataset.theme);
    });
    if (hint) hint.textContent = mine() ? hint.dataset.mine : hint.dataset.all;
  }

  function figure(list, label, value, className) {
    var wrap = el("div");
    wrap.appendChild(el("dt", "", label));
    wrap.appendChild(el("dd", className || "", value));
    list.appendChild(wrap);
  }

  function renderDetail(p) {
    detail.textContent = "";
    var top = el("div", "ov-detail__top");
    var heading = el("div");
    heading.appendChild(el("p", "ov-meta", [p.themeName, p.address].filter(Boolean).join(" · ")));
    var title = el("h3", "", p.name);
    title.id = "ov-map-detail-title";
    heading.appendChild(title);
    top.appendChild(heading);
    var back = el("button", "ov-detail__back", "Zur Liste");
    back.type = "button";
    back.addEventListener("click", function () { select(null); });
    top.appendChild(back);
    detail.appendChild(top);

    var figures = el("dl", "ov-detail__figures");
    figure(figures, "Bürgerpunkte", p.share + " %");
    figure(figures, "Ausgaben", p.spend + " %", "is-spend");
    if (loggedIn) figure(figures, "Von dir", p.mine > 0 ? p.mine + " P." : "–");
    detail.appendChild(figures);

    if (p.measures.length) {
      var list = el("ul", "ov-detail__measures");
      p.measures.forEach(function (m) {
        var item = el("li");
        item.appendChild(el("span", "", m.title));
        item.appendChild(el("span", "pill pill--" + m.statusKey, m.status));
        list.appendChild(item);
      });
      detail.appendChild(list);
    }

    var give = el("a", "btn-outline", loggedIn ? "Punkte geben" : "Code eingeben und Punkte geben");
    give.href = loggedIn ? mapNode.dataset.giveUrl + "#id_" + p.key : mapNode.dataset.redeemUrl;
    detail.appendChild(give);
  }

  function select(key) {
    var place = key ? byKey[key] : null;
    var previous = state.selected;
    state.selected = place ? key : null;
    detail.hidden = !place;
    rank.hidden = !!place;
    if (place) {
      renderDetail(place);
      detail.focus();
    } else if (previous) {
      var back = rank.querySelector('[data-select="' + previous + '"]');
      if (back) back.focus();
    }
    renderMarkers();
  }

  function render() { renderMarkers(); renderRank(); }

  document.querySelectorAll("#karte [data-scope]").forEach(function (button) {
    button.addEventListener("click", function () {
      state.scope = button.dataset.scope;
      document.querySelectorAll("#karte [data-scope]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === button));
      });
      render();
    });
  });

  rank.addEventListener("click", function (event) {
    var button = event.target.closest("[data-select]");
    if (button && !button.disabled) select(button.dataset.select);
  });

  detail.addEventListener("keydown", function (event) {
    if (event.key === "Escape") select(null);
  });

  // Geöffnetes Thema in „Wunsch und Haushalt“ hebt seine Einrichtungen hervor.
  document.querySelectorAll("#wunsch-haushalt details[data-theme]").forEach(function (details) {
    details.addEventListener("toggle", function () {
      var open = document.querySelector("#wunsch-haushalt details[data-theme][open]");
      state.theme = open ? Number(open.dataset.theme) : null;
      render();
    });
  });

  render();
})();
