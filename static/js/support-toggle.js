// „Unterstützen“ als Umschalter für Vorschläge, auf der Übersicht und der Seite „Vorschläge“.
// Wurzel: [data-support-root] mit data-support-url (…/0/unterstuetzen/). Knöpfe: [data-support].
// Zähler, Satz, Fortschritt und Schritt kommen vom Server; Texte nur über textContent.
(function () {
  "use strict";

  var root = document.querySelector("[data-support-root]");
  if (!root || !window.fetch) return;

  var live = root.querySelector("[data-support-live]");
  var token = root.querySelector("input[name=csrfmiddlewaretoken]");
  if (!token) return;

  root.querySelectorAll("[data-support][data-js-only]").forEach(function (button) { button.hidden = false; });

  function say(text) { if (live) live.textContent = text; }

  function render(button, on) {
    var title = button.dataset.title;
    button.setAttribute("aria-pressed", String(on));
    button.setAttribute("aria-label", on ? "Unterstützung für „" + title + "“ zurückziehen" : "„" + title + "“ unterstützen");
  }

  function updateRow(id, data) {
    var row = document.getElementById("vorschlag-" + id);
    if (!row) return;
    row.dataset.supports = data.supports;
    row.dataset.supported = data.supported ? "1" : "";
    row.dataset.stage = data.stage;
    var sentence = row.querySelector("[data-sentence]");
    if (sentence) sentence.textContent = data.sentence;
    var progress = row.querySelector("[data-progress]");
    if (progress) progress.style.width = data.progress + "%";
    var pill = row.querySelector("[data-stage-pill]");
    if (pill) { pill.textContent = data.stageLabel; pill.className = "pill stage stage--" + data.stage; }
  }

  function toggle(button) {
    var id = button.dataset.support;
    button.disabled = true;
    fetch(root.dataset.supportUrl.replace("/0/", "/" + id + "/"), {
      method: "POST", headers: { "X-CSRFToken": token.value }, credentials: "same-origin",
    }).then(function (response) {
      return response.json().then(function (data) { return { ok: response.ok, data: data }; });
    }).then(function (result) {
      button.disabled = false;
      if (!result.ok) { say(result.data.error || "Das hat nicht geklappt."); return; }
      var data = result.data;
      root.querySelectorAll("[data-support='" + id + "']").forEach(function (b) { render(b, data.supported); });
      updateRow(id, data);
      say((data.supported ? "Unterstützt. " : "Unterstützung zurückgezogen. ") + data.sentence);
    }).catch(function () {
      button.disabled = false;
      say("Keine Verbindung. Bitte versuche es noch einmal.");
    });
  }

  root.addEventListener("click", function (event) {
    var button = event.target.closest("[data-support]");
    if (button) toggle(button);
  });
})();
