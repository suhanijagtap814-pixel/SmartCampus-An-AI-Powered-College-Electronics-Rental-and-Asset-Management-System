/* Staff QR scanner controller.
   Uses the html5-qrcode library (loaded from CDN) when a camera is available,
   and always supports manual payload lookup via /api/scan-qr. */
(function () {
  "use strict";

  function renderResult(data) {
    var box = document.getElementById("qrResult");
    if (!box) return;
    if (!data.found) {
      box.innerHTML = '<div class="bg-rose-50 border border-rose-200 text-rose-800 rounded-lg px-4 py-3 text-sm">' +
        (data.error || "Device not found.") + "</div>";
      return;
    }
    var d = data.device;
    box.innerHTML =
      '<a href="' + d.url + '" class="flex items-center gap-4 bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition">' +
      '<img src="' + (d.image_url || "/static/uploads/devices/default.jpg") + '" class="w-16 h-16 rounded-lg object-cover">' +
      '<div><div class="font-semibold text-slate-900">' + d.name + "</div>" +
      '<div class="text-xs text-slate-500">' + d.code + " · " + d.status + " · " + (d.location || "") + "</div></div></a>";
  }

  function lookup(payload) {
    fetch("/api/scan-qr", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ qr_code: payload })
    })
      .then(function (r) { return r.json(); })
      .then(renderResult)
      .catch(function () { renderResult({ found: false, error: "Network error." }); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("qrLookupBtn");
    var manual = document.getElementById("qrManual");
    if (btn && manual) {
      btn.addEventListener("click", function () {
        if (manual.value.trim()) lookup(manual.value.trim());
      });
    }

    // Optional live camera scanning if html5-qrcode is present.
    var reader = document.getElementById("qrReader");
    if (reader && window.Html5Qrcode) {
      try {
        var scanner = new window.Html5Qrcode("qrReader");
        scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 220 },
          function (decodedText) { lookup(decodedText); }
        ).catch(function () { /* camera unavailable - manual entry still works */ });
      } catch (e) { /* ignore */ }
    }
  });
})();
