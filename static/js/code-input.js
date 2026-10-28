// Zeichenzähler für die Code-Eingabe. Rein zusätzlich: Ohne JavaScript bleibt das Formular voll nutzbar.
// Die Normalisierung entspricht normalize_code() in apps/access/codes.py.
(function () {
  "use strict";

  var ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  var LENGTH = 16;

  function normalize(raw) {
    return raw.toUpperCase().replace(/[\s-]/g, "").replace(/O/g, "0").replace(/[IL]/g, "1");
  }

  function hasUnknownChars(code) {
    return code.split("").some(function (char) { return ALPHABET.indexOf(char) < 0; });
  }

  function bind(input) {
    var counter = document.getElementById(input.dataset.codeCounter);
    if (!counter) return;

    function update() {
      var code = normalize(input.value);
      if (hasUnknownChars(code)) {
        counter.textContent = "Enthält Zeichen, die in keinem Code vorkommen.";
        counter.dataset.state = "invalid";
      } else {
        counter.textContent = Math.min(code.length, 99) + " / " + LENGTH + " Zeichen";
        counter.dataset.state = code.length === LENGTH ? "complete" : "";
      }
    }

    counter.hidden = false;
    input.setAttribute("aria-describedby", input.getAttribute("aria-describedby") + " " + counter.id);
    input.addEventListener("input", update);
    update();
  }

  document.querySelectorAll("input[data-code-counter]").forEach(bind);
})();
