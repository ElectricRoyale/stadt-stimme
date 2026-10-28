// Vorschlag machen: macht aus dem Formular drei Schritte (Anliegen, Einordnen, Prüfen), schlägt
// Thema und Ort aus dem Text vor und zeigt ähnliche Vorschläge. Ohne JavaScript bleibt es ein
// einseitiges Formular. Texte nur über textContent.
(function () {
  "use strict";

  var form = document.querySelector("[data-proposal-form]");
  if (!form) return;

  var live = document.getElementById("prop-live");
  var stepError = form.querySelector("[data-step-error]");
  var title = form.elements.title;
  var text = form.elements.text;
  var facilitiesGroup = form.querySelector("[data-facilities]");
  var guessNote = form.querySelector("[data-guess-note]");
  var places = JSON.parse(document.getElementById("prop-guess-data").textContent);
  var step = Number(form.dataset.errorStep) || 1;
  var reached = step;
  var guessed = step > 1;

  form.querySelectorAll("[data-js-only]").forEach(function (node) { node.hidden = false; });

  function radios(name) { return Array.prototype.slice.call(form.querySelectorAll("input[name='" + name + "']")); }
  function checked(name) { return radios(name).filter(function (r) { return r.checked; })[0] || null; }
  function labelOf(input) { return input ? input.closest("label").textContent.trim() : ""; }
  function check(name, value) { radios(name).forEach(function (r) { r.checked = r.value === String(value); }); }

  // Schritte
  function show(n) {
    step = n;
    reached = Math.max(reached, n);
    form.querySelectorAll("[data-step]").forEach(function (node) { node.hidden = Number(node.dataset.step) !== n; });
    document.querySelectorAll("[data-aside]").forEach(function (node) { node.hidden = Number(node.dataset.aside) !== n; });
    form.querySelectorAll(".prop-progress [data-goto]").forEach(function (button) {
      var target = Number(button.dataset.goto);
      button.disabled = target > reached;
      button.classList.toggle("is-done", target < n);
      if (target === n) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
    form.querySelector("[data-back]").disabled = n === 1;
    form.querySelector("[data-next]").hidden = n === 3;
    form.querySelector("[data-submit]").hidden = n !== 3;
    if (n === 3) fillReview();
    syncFacilities();
    live.textContent = "Schritt " + n + " von 3";
  }

  function validate(n) {
    if (n === 1 && title.value.trim().length < 8) return { message: "Bitte gib einen Titel mit mindestens 8 Zeichen ein.", field: title };
    if (n === 2 && !checked("category")) return { message: "Bitte wähle ein Thema.", field: radios("category")[0] };
    if (n === 2 && checked("where") && checked("where").value === "place" && !checked("facility")) {
      return { message: "Bitte wähle einen Ort oder stell „Nein, allgemein“ ein.", field: radios("facility")[0] };
    }
    return null;
  }

  function setError(error) {
    stepError.hidden = !error;
    stepError.textContent = error ? error.message : "";
    if (error && error.field === title) title.setAttribute("aria-invalid", "true");
    else title.removeAttribute("aria-invalid");
    if (error && error.field) error.field.focus();
  }

  function goTo(n) {
    for (var s = step; s < n; s++) {
      var error = validate(s);
      if (error) { show(s); setError(error); return; }
    }
    setError(null);
    if (n >= 2 && !guessed) guess();
    show(n);
    var first = form.querySelector("[data-step='" + n + "'] input, [data-step='" + n + "'] button");
    if (first) first.focus();
  }

  // Thema und Ort aus dem Text vorschlagen (einmal, beim ersten Wechsel zu Schritt 2)
  function words(value) { return value.toLowerCase().match(/[\p{L}\p{N}]{5,}/gu) || []; }

  function guess() {
    guessed = true;
    if (checked("category") || checked("facility")) return;
    var said = words(title.value + " " + text.value);
    var best = null, bestHits = 0;
    places.forEach(function (place) {
      var hits = words(place.name).filter(function (w) { return said.indexOf(w) >= 0; }).length;
      if (hits > bestHits) { best = place; bestHits = hits; }
    });
    if (!best) return;
    check("where", "place");
    check("facility", best.id);
    check("category", best.category);
    guessNote.textContent = "Wir haben aus deinem Text etwas vorausgewählt. Ändere es, wenn es nicht passt.";
  }

  function syncFacilities() {
    var place = checked("where") && checked("where").value === "place";
    facilitiesGroup.hidden = !place;
  }

  function fillReview() {
    var where = checked("where") && checked("where").value === "place" ? labelOf(checked("facility")) : "Kein bestimmter Ort";
    var values = {
      title: title.value.trim(),
      text: text.value.trim() || "Keine Beschreibung",
      category: labelOf(checked("category")) || "–",
      where: where || "Kein bestimmter Ort"
    };
    form.querySelectorAll("[data-review]").forEach(function (node) { node.textContent = values[node.dataset.review]; });
  }

  form.querySelector("[data-next]").addEventListener("click", function () { goTo(step + 1); });
  form.querySelector("[data-back]").addEventListener("click", function () { setError(null); show(Math.max(1, step - 1)); });
  form.querySelectorAll("[data-goto]").forEach(function (button) {
    button.addEventListener("click", function () {
      var n = Number(button.dataset.goto);
      if (n < step) { setError(null); show(n); } else goTo(n);
    });
  });
  form.addEventListener("submit", function (event) {
    if (step < 3) { event.preventDefault(); goTo(step + 1); }
  });
  radios("where").forEach(function (r) { r.addEventListener("change", syncFacilities); });
  [title, text].forEach(function (field) {
    field.addEventListener("input", function () {
      if (step === 1) guessed = false;
      if (!stepError.hidden) setError(null);
    });
  });

  // Zeichenzähler
  form.querySelectorAll("[data-count]").forEach(function (field) {
    var counter = document.getElementById(field.dataset.count);
    function update() { counter.textContent = field.value.length + " / " + field.maxLength + " Zeichen"; }
    field.addEventListener("input", update);
    update();
  });

  // Ähnliche Vorschläge
  var similarBox = form.querySelector("[data-similar]");
  var similarList = similarBox.querySelector("ul");
  var loggedIn = form.dataset.loggedIn === "1";
  var csrf = form.elements.csrfmiddlewaretoken.value;
  var timer = null;

  function supportButton(item, row) {
    var button = document.createElement("button");
    button.type = "button";
    function render() {
      button.className = "ss-btn " + (item.supported ? "ss-btn--primary" : "ss-btn--secondary");
      button.textContent = item.supported ? "Unterstützt" : "Unterstützen";
      button.setAttribute("aria-pressed", String(item.supported));
      row.textContent = item.title + " · " + item.supports + " Unterstützungen";
    }
    button.addEventListener("click", function () {
      fetch(form.dataset.supportUrl.replace("/0/", "/" + item.id + "/"), {
        method: "POST", headers: { "X-CSRFToken": csrf }, credentials: "same-origin"
      }).then(function (response) { return response.ok ? response.json() : null; }).then(function (data) {
        if (!data) return;
        item.supported = data.supported;
        item.supports = data.supports;
        render();
        live.textContent = data.supported ? "Unterstützt" : "Unterstützung zurückgezogen";
      });
    });
    render();
    return button;
  }

  function showSimilar(items) {
    similarList.textContent = "";
    items.forEach(function (item) {
      var li = document.createElement("li");
      var row = document.createElement("span");
      row.textContent = item.title + " · " + item.supports + " Unterstützungen";
      li.appendChild(row);
      if (loggedIn && !item.own) li.appendChild(supportButton(item, row));
      similarList.appendChild(li);
    });
    similarBox.hidden = items.length === 0;
  }

  function lookup() {
    var query = (title.value + " " + text.value).trim();
    if (query.length < 5) { showSimilar([]); return; }
    fetch(form.dataset.similarUrl + "?q=" + encodeURIComponent(query), { credentials: "same-origin" })
      .then(function (response) { return response.ok ? response.json() : { items: [] }; })
      .then(function (data) { showSimilar(data.items); })
      .catch(function () { showSimilar([]); });
  }

  [title, text].forEach(function (field) {
    field.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(lookup, 400); });
  });

  show(step);
  if (title.value) lookup();
})();
