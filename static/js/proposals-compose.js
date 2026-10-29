// „Vorschlag machen“: drei Schritte (Anliegen, Einordnen, Prüfen), Zeichenzähler, Orte passend
// zum Thema und „Gibt es das schon?“ beim Tippen. Ohne JavaScript bleibt es ein einseitiges
// Formular; der Server prüft alles noch einmal. Fehler erst nach dem Versuch weiterzugehen.
(function () {
  "use strict";

  var form = document.querySelector("form[data-compose]");
  if (!form) return;

  var STEPS = ["Anliegen", "Einordnen", "Prüfen"];
  var titleMin = Number(form.dataset.titleMin) || 8;
  var title = form.querySelector("[data-title]");
  var text = form.elements.text;
  var facility = form.querySelector("[data-facility]");
  var heading = form.querySelector("[data-step-heading]");
  var step = Number(form.dataset.errorStep) || 1;
  var reached = step;
  var moved = false;

  form.querySelectorAll("[data-js-only]").forEach(function (node) { node.hidden = false; });

  function themeInputs() { return Array.prototype.slice.call(form.querySelectorAll("input[name='category']")); }
  function theme() { return themeInputs().filter(function (r) { return r.checked; })[0] || null; }

  function setError(key, message) {
    var node = form.querySelector("[data-error-for='" + key + "']");
    if (!node) return;
    node.textContent = message || "";
    node.hidden = !message;
    if (key === "v-titel") {
      if (message) title.setAttribute("aria-invalid", "true"); else title.removeAttribute("aria-invalid");
      title.setAttribute("aria-describedby", message ? "v-titel-fehler" : "v-titel-hilfe");
    } else if (key === "category") {
      form.querySelector(".prop-themes").classList.toggle("is-invalid", !!message);
    } else if (key === "facility") {
      if (message) facility.setAttribute("aria-invalid", "true"); else facility.removeAttribute("aria-invalid");
    }
  }

  function titleError() {
    var n = title.value.trim().length;
    if (n === 0) return "Schreib in einem Satz, worum es geht.";
    if (n < titleMin) return "Noch " + (titleMin - n) + " Zeichen, damit andere verstehen, worum es geht.";
    return "";
  }

  function validate(n) {
    if (n === 1) { var e = titleError(); setError("v-titel", e); return e ? title : null; }
    if (n === 2 && !theme()) {
      setError("category", "Wähle ein Thema, damit die richtige Stelle den Vorschlag bekommt.");
      return themeInputs()[0];
    }
    if (n === 2) { setError("category", ""); return placeProblem(); }
    return null;
  }

  // Ort: „bekannt“ braucht eine Einrichtung, „neu“ einen Punkt auf der Karte (proposals-place.js).
  function where() {
    var picked = form.querySelector("input[name='where']:checked");
    return picked ? picked.value : "allgemein";
  }

  function placeProblem() {
    setError("facility", "");
    setError("where", "");
    if (where() === "bekannt" && !facility.value) {
      setError("facility", "Wähle die Einrichtung oder „Nein, allgemein“.");
      return facility;
    }
    if (where() === "neu" && !form.elements.latitude.value) {
      setError("where", "Tippe auf die Karte, um den Ort zu setzen.");
      return form.querySelector("[data-pick-center]");
    }
    return null;
  }

  function show(n) {
    step = n;
    reached = Math.max(reached, n);
    form.querySelectorAll("[data-step]").forEach(function (node) { node.hidden = Number(node.dataset.step) !== n; });
    form.querySelectorAll("[data-goto]").forEach(function (button) {
      if (!button.classList.contains("steps__item")) return;
      var target = Number(button.dataset.goto);
      button.disabled = target > reached || target === n;
      button.classList.toggle("is-done", target < n);
      button.querySelector("[data-step-mark]").textContent = target < n ? "✓" : String(target);
      if (target === n) button.setAttribute("aria-current", "step"); else button.removeAttribute("aria-current");
    });
    form.querySelector("[data-back]").hidden = n === 1;
    form.querySelector("[data-next]").hidden = n === 3;
    form.querySelector("[data-submit]").hidden = n !== 3;
    heading.textContent = "Schritt " + n + " von 3: " + STEPS[n - 1];
    if (n === 3) fillReview();
    form.dispatchEvent(new CustomEvent("compose:step", { detail: { step: n } }));
    if (moved) heading.focus();
  }

  function goTo(n) {
    for (var s = step; s < n; s++) {
      var field = validate(s);
      if (field) { field.focus(); return; }
    }
    moved = true;
    show(n);
  }

  function fillReview() {
    var picked = theme();
    var values = {
      title: title.value.trim(),
      text: text.value.trim(),
      category: picked ? picked.closest("label").textContent.trim() : "",
      facility: placeLabel(),
    };
    form.querySelectorAll("[data-review]").forEach(function (node) { node.textContent = values[node.dataset.review]; });
  }

  function placeLabel() {
    if (where() === "neu") return "Neuer Ort auf der Karte";
    var option = facility.options[facility.selectedIndex];
    return where() === "bekannt" && option && option.value ? option.textContent : "Kein bestimmter Ort";
  }

  // Orte nur aus dem gewählten Thema
  function syncPlaces() {
    var picked = theme();
    facility.disabled = !picked;
    Array.prototype.forEach.call(facility.options, function (option) {
      if (!option.value) return;
      option.hidden = !picked || option.dataset.category !== picked.value;
      if (option.hidden && option.selected) facility.value = "";
    });
    form.querySelector("[data-facility-hint]").textContent = picked
      ? "Fehlt der Ort in der Liste? Wähle „Ja, neuer Ort“ und tippe auf die Karte."
      : "Erst ein Thema wählen, dann zeigen wir die passenden Orte.";
  }
  themeInputs().forEach(function (r) { r.addEventListener("change", function () { setError("category", ""); syncPlaces(); }); });

  facility.addEventListener("change", function () { if (facility.value) setError("facility", ""); });
  form.addEventListener("place:set", function () { setError("where", ""); });
  form.querySelectorAll("input[name='where']").forEach(function (r) {
    r.addEventListener("change", function () { setError("where", ""); setError("facility", ""); });
  });

  form.querySelector("[data-next]").addEventListener("click", function () { goTo(step + 1); });
  form.querySelector("[data-back]").addEventListener("click", function () { moved = true; show(step - 1); });
  form.querySelectorAll("[data-goto]").forEach(function (button) {
    button.addEventListener("click", function () {
      var n = Number(button.dataset.goto);
      if (n < step) { moved = true; show(n); } else goTo(n);
    });
  });
  form.addEventListener("submit", function (event) {
    if (step < 3) { event.preventDefault(); goTo(step + 1); }
  });
  title.addEventListener("input", function () { if (!form.querySelector("[data-error-for='v-titel']").hidden && !titleError()) setError("v-titel", ""); });

  // Zeichenzähler
  form.querySelectorAll("[data-counter-for]").forEach(function (counter) {
    var field = document.getElementById(counter.dataset.counterFor);
    function update() {
      counter.textContent = field.value.length + "/" + field.maxLength;
      counter.classList.toggle("is-near", field.value.length > field.maxLength - 10);
    }
    field.addEventListener("input", update);
    update();
  });

  // „Gibt es das schon?“
  var box = form.querySelector("[data-similar]");
  var holder = box.querySelector("[data-similar-list]");
  var timer = null;

  function el(tag, className, content) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (content) node.textContent = content;
    return node;
  }

  function supportButton(item) {
    var button = el("button", "support support--small");
    button.type = "button";
    button.dataset.support = item.id;
    button.dataset.title = item.title;
    button.setAttribute("aria-pressed", String(item.supported));
    button.setAttribute("aria-label", item.supported ? "Unterstützung für „" + item.title + "“ zurückziehen" : "„" + item.title + "“ unterstützen");
    button.appendChild(el("span", "support__on", "Unterstützt"));
    button.appendChild(el("span", "support__off", "Unterstützen"));
    return button;
  }

  function render(data) {
    holder.textContent = "";
    data.measures.forEach(function (m) {
      var li = el("li");
      var body = el("div", "prop-similar__text");
      body.appendChild(el("p", "prop-similar__title", m.title));
      body.appendChild(el("p", "prop-similar__meta", "Geplante Maßnahme bei " + m.facility));
      var link = el("a", "btn-outline", "Punkte geben");
      link.href = m.url;
      li.appendChild(body);
      li.appendChild(link);
      holder.appendChild(li);
    });
    data.items.forEach(function (item) {
      var li = el("li");
      var body = el("div", "prop-similar__text");
      body.appendChild(el("p", "prop-similar__title", item.title));
      var meta = el("p", "prop-similar__meta");
      meta.appendChild(el("span", "pill stage stage--" + item.stage, item.stageLabel));
      meta.appendChild(el("span", "", item.supports + " Unterstützungen"));
      body.appendChild(meta);
      li.appendChild(body);
      if (item.canSupport) li.appendChild(supportButton(item));
      holder.appendChild(li);
    });
    box.hidden = !data.measures.length && !data.items.length;
  }

  function lookup() {
    var q = (title.value + " " + text.value).trim();
    if (q.length < 5) { box.hidden = true; return; }
    fetch(form.dataset.similarUrl + "?q=" + encodeURIComponent(q), { credentials: "same-origin" })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (data) { if (data) render(data); })
      .catch(function () { box.hidden = true; });
  }
  [title, text].forEach(function (field) {
    field.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(lookup, 350); });
  });

  syncPlaces();
  show(step);
  if (title.value) lookup();
})();
