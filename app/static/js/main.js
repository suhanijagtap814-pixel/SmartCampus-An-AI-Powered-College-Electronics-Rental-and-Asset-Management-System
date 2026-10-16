/* Smart Campus Rental - shared front-end helpers. */
(function () {
  "use strict";

  // Auto-dismiss flash messages after a few seconds.
  document.addEventListener("DOMContentLoaded", function () {
    var flashes = document.querySelectorAll("#flashArea > div");
    flashes.forEach(function (el) {
      setTimeout(function () {
        el.style.transition = "opacity .4s ease";
        el.style.opacity = "0";
        setTimeout(function () { el.remove(); }, 400);
      }, 4500);
    });
  });

  // Booking price + deposit estimator (used on the booking page).
  document.addEventListener("DOMContentLoaded", function () {
    var start = document.getElementById("startDate");
    var end = document.getElementById("endDate");
    var est = document.getElementById("estimate");
    if (!start || !end || !est) return;

    function recalc() {
      var perDay = parseFloat(est.getAttribute("data-price") || "0");
      var s = new Date(start.value);
      var e = new Date(end.value);
      var days = Math.max(1, Math.round((e - s) / 86400000) || 1);
      var total = perDay * days;
      est.textContent = "Estimated rental: ₹" + total.toFixed(0) +
        " for " + days + " day(s) (₹" + perDay.toFixed(0) + "/day).";
    }
    start.addEventListener("change", recalc);
    end.addEventListener("change", recalc);
    recalc();
  });
})();
