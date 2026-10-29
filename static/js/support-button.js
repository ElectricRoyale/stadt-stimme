// „Unterstützen“ bei Vorschlägen: schaltet über den bestehenden Endpunkt um (POST, JSON-Antwort)
// und aktualisiert Zähler, Fortschritt und Schwelle. Ohne JavaScript bleiben die Knöpfe verborgen.
(function () {
  "use strict";

  var panel = document.querySelector("[data-support-threshold]");
  if (!panel || !window.fetch) return;
  var token = panel.querySelector("input[name=csrfmiddlewaretoken]");
  var status = panel.querySelector("[data-support-status]");
  var threshold = Number(panel.dataset.supportThreshold) || 1;
  if (!token) return;

  // Erfolg nur für Screenreader ansagen, Fehler auch sichtbar zeigen.
  function say(text, visible) {
    if (!status) return;
    status.textContent = text;
    status.classList.toggle("ss-visually-hidden", !visible);
  }

  function update(item, button, data) {
    button.setAttribute("aria-pressed", String(data.supported));
    button.textContent = data.supported ? "Unterstützt" : "Unterstützen";
    item.querySelector("[data-support-count]").textContent = data.supports;
    var reached = data.supports >= threshold;
    var meter = item.querySelector(".meter-line");
    meter.classList.toggle("is-reached", reached);
    meter.firstElementChild.style.width = Math.min(100, Math.round(data.supports / threshold * 100)) + "%";
    item.querySelector("[data-support-reached]").hidden = !reached;
    say(data.supported ? "Unterstützt" : "Unterstützung zurückgezogen", false);
  }

  panel.querySelectorAll("[data-support-url]").forEach(function (button) {
    var item = button.closest("[data-support-item]");
    button.hidden = false;
    button.addEventListener("click", function () {
      button.disabled = true;
      fetch(button.dataset.supportUrl, {
        method: "POST",
        headers: { "X-CSRFToken": token.value },
        credentials: "same-origin",
      })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) throw new Error(data.error || "Das hat nicht geklappt.");
            return data;
          });
        })
        .then(function (data) { update(item, button, data); })
        .catch(function (error) { say(error.message, true); })
        .then(function () { button.disabled = false; });
    });
  });
})();
