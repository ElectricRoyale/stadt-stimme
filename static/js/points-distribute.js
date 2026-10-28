// „Punkte verteilen“: −/+ Knöpfe, Restpunkte und Balken live. Rein zusätzlich: Ohne JavaScript
// bleiben die Zahlenfelder und das Speichern voll nutzbar; der Server prüft die 100-Punkte-Grenze.
(function () {
  "use strict";

  var form = document.querySelector("form[data-budget]");
  if (!form) return;

  var budget = parseInt(form.dataset.budget, 10);
  var inputs = Array.prototype.slice.call(form.querySelectorAll("input[data-points]"));

  function valueOf(input) {
    var value = parseInt(input.value, 10);
    return isNaN(value) || value < 0 ? 0 : value;
  }

  function total(except) {
    return inputs.reduce(function (sum, input) {
      return input === except ? sum : sum + valueOf(input);
    }, 0);
  }

  function setAll(selector, text) {
    form.querySelectorAll(selector).forEach(function (node) { node.textContent = text; });
  }

  function render() {
    var used = total(null);
    var remaining = Math.max(budget - used, 0);
    setAll("[data-remaining]", String(remaining));
    setAll("[data-used]", String(used));
    form.querySelectorAll("[data-used-bar]").forEach(function (bar) {
      bar.style.width = Math.min(used, budget) + "%";
    });
    form.querySelectorAll("[data-used-meter]").forEach(function (meter) {
      meter.setAttribute("aria-label", used + " von " + budget + " Punkten vergeben");
    });
    form.querySelectorAll("[data-remaining-note]").forEach(function (note) {
      note.hidden = remaining === 0;
    });

    form.querySelectorAll("[data-target]").forEach(function (card) {
      var input = card.querySelector("input[data-points]");
      var points = valueOf(input);
      card.classList.toggle("target--active", points > 0);
      card.querySelector("[data-target-bar]").style.width = points + "%";
      card.querySelector('[data-step="-1"]').disabled = points === 0;
      card.querySelector('[data-step="1"]').disabled = remaining === 0;
    });

    form.querySelectorAll("[data-theme]").forEach(function (theme) {
      var sum = 0;
      theme.querySelectorAll("input[data-points]").forEach(function (input) { sum += valueOf(input); });
      theme.querySelectorAll("[data-theme-sum]").forEach(function (node) { node.textContent = String(sum); });
      var summary = form.querySelector('[data-theme-summary="' + theme.getAttribute("aria-labelledby") + '"]');
      if (summary) {
        summary.querySelector("[data-theme-sum]").textContent = String(sum);
        summary.querySelector("[data-theme-bar]").style.width = sum + "%";
      }
    });
  }

  // Ein Feld darf höchstens so viel bekommen, wie neben den anderen noch frei ist.
  function clamp(input, wanted) {
    var max = budget - total(input);
    input.value = String(Math.max(0, Math.min(wanted, max)));
  }

  form.querySelectorAll("[data-step]").forEach(function (button) {
    var input = button.parentElement.querySelector("input[data-points]");
    var step = parseInt(button.dataset.step, 10);
    button.hidden = false;
    button.addEventListener("click", function () {
      clamp(input, valueOf(input) + step);
      render();
    });
  });

  inputs.forEach(function (input) {
    input.addEventListener("change", function () {
      clamp(input, valueOf(input));
      render();
    });
    input.addEventListener("input", render);
  });

  render();
})();
