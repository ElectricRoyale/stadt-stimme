// Suchleiste oben: „/“ setzt den Fokus in das sichtbare Suchfeld, außer beim Schreiben (ADR-018).
(function () {
  "use strict";

  function isTyping(target) {
    return target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || isTyping(event.target)) return;
    var fields = document.querySelectorAll("[data-top-search]");
    for (var i = 0; i < fields.length; i += 1) {
      if (fields[i].offsetParent !== null) {
        event.preventDefault();
        fields[i].focus();
        return;
      }
    }
  });
})();
