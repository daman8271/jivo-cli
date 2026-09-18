/* board.js — Approval Board.
   The page holds no numbers of its own. Everything comes from the VPS publisher
   every 30 seconds; the sitting-time counters tick every second off each row's
   own rejection timestamp, so the clock is honest between fetches. */
(function () {
  "use strict";

  var BOOKS = [["OIL", "Oil", "oil"], ["MART", "Mart", "mart"], ["BEV", "Beverages", "bev"]];
  var POLL_MS = 30000, STALE_MS = 300000, DAY = 86400000;
  var board = null, active = "OIL", failed = 0;

  var $ = function (id) { return document.getElementById(id); };

  /* ---- theme ------------------------------------------------------------ */
  function theme(t) {
    document.documentElement.setAttribute("data-theme", t);
    $("theme").textContent = t === "dark" ? "Light" : "Dark";
    $("theme").setAttribute("aria-pressed", t === "dark" ? "true" : "false");
    try { localStorage.setItem("approvals:theme", t); } catch (e) {}
  }
  $("theme").addEventListener("click", function () {
    theme(document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark");
  });
  (function () {
    var t = document.documentElement.getAttribute("data-theme") || "light";
    $("theme").textContent = t === "dark" ? "Light" : "Dark";
    $("theme").setAttribute("aria-pressed", t === "dark" ? "true" : "false");
  })();

  /* ---- formatting ------------------------------------------------------ */
  function rupees(n) {                       // Indian grouping, no paise
    n = Math.round(Number(n) || 0);
    var s = String(Math.abs(n)), out;
    if (s.length > 3) {
      var head = s.slice(0, -3), tail = s.slice(-3), parts = [];
      while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
      if (head) parts.unshift(head);
      out = parts.join(",") + "," + tail;
    } else out = s;
    return (n < 0 ? "-" : "") + out;
  }

  function lakh(n) {
    n = Number(n) || 0;
    if (n >= 10000000) return (n / 10000000).toFixed(2) + " crore";
    if (n >= 100000) return (n / 100000).toFixed(2) + " lakh";
    return rupees(n);
  }

  /* SAP hands us a wall-clock IST stamp with no zone. Pin it to +05:30 so the
     age is right on a phone that is not on IST. */
  function parseIST(s) {
    if (!s) return null;
    var d = new Date(s.replace(" ", "T") + "+05:30");
    return isNaN(d.getTime()) ? null : d;
  }

  function sitting(ms) {                     // the big counter
    if (ms == null) return "—";
    var m = Math.floor(ms / 60000), h = Math.floor(m / 60), d = Math.floor(h / 24);
    if (d >= 30) return d + "d";
    if (d >= 1) return d + "d " + (h % 24) + "h";
    if (h >= 1) return h + "h " + (m % 60) + "m";
    return Math.max(m, 0) + "m";
  }

  function ago(ms) {                         // for the freshness line
    var s = Math.max(0, Math.round(ms / 1000));
    if (s < 90) return s + " s ago";
    var m = Math.round(s / 60);
    if (m < 90) return m + " min ago";
    return Math.round(m / 60) + " h ago";
  }

  function band(ms) {
    var d = ms / DAY;
    if (d >= 90) return "is-ancient";
    if (d >= 7) return "is-late";
    if (d >= 2) return "is-warn";
    return "";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function whenLabel(d) {
    var day = d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
    var t = d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
    return day + " at " + t;
  }

  function plural(n, one, many) { return n === 1 ? one : many; }

  /* ---- render ---------------------------------------------------------- */
  function renderBooks() {
    $("books").innerHTML = BOOKS.map(function (b) {
      var bk = board && board.books[b[0]];
      var open = bk ? bk.open : "–", late = bk ? bk.late : 0;
      return '<button class="book' + (b[0] === active ? " is-active" : "") +
        '" type="button" data-book="' + b[0] + '" data-co="' + b[2] + '"' +
        (b[0] === active ? ' aria-current="true"' : "") + ">" +
        '<span class="name">' + b[1] + "</span>" +
        '<span class="n">' + open + "<small>open</small></span>" +
        '<span class="late' + (late ? " has" : "") + '">' +
        (late ? late + " past 2 days" : (bk ? "none past 2 days" : "")) + "</span>" +
        "</button>";
    }).join("");
    Array.prototype.forEach.call($("books").querySelectorAll(".book"), function (el) {
      el.addEventListener("click", function () {
        active = el.getAttribute("data-book");
        document.documentElement.setAttribute("data-co", el.getAttribute("data-co"));
        render();
      });
    });
  }

  function renderBands() {
    var el = $("bands"), bits = [];
    if (!board) { el.innerHTML = ""; return; }

    Object.keys(board.errors || {}).forEach(function (k) {
      var name = (BOOKS.filter(function (b) { return b[0] === k; })[0] || [k, k])[1];
      bits.push('<div class="band is-dead"><strong>' + name + " could not be read.</strong> " +
        "That is not a zero. The book is missing from this board until the next good read. " +
        esc(board.errors[k]).slice(0, 160) + "</div>");
    });

    var age = Date.now() - new Date(board.generated_at).getTime();
    if (age > STALE_MS || failed > 2) {
      bits.push('<div class="band is-dead"><strong>This board stopped updating ' + ago(age) +
        ".</strong> Everything below is from then, not now.</div>");
    }

    var late = board.totals.late_alarmable || 0;
    if (late > 0) {
      bits.push('<div class="band is-late"><strong>' + late + " " +
        plural(late, "entry has", "entries have") + " been sitting more than 2 days.</strong> " +
        "Bhawani sent " + plural(late, "it", "them") + " back and " +
        plural(late, "it has", "they have") + " not been re-done.</div>");
    }
    el.innerHTML = bits.join("");
    document.title = (late ? "(" + late + ") " : "") + "Approval Board";
  }

  function rowHTML(r, now) {
    var d = parseIST(r.rejected_at), ms = d ? now - d.getTime() : null;
    var cls = ms == null ? "" : band(ms);
    return '<li class="row ' + cls + '" data-at="' + esc(r.rejected_at) + '">' +
      '<div class="age"><b>' + sitting(ms) + "</b></div>" +
      '<div class="draft">' + r.doc_entry + "</div>" +
      '<div class="body">' +
        '<div class="l1">' +
          '<span class="vendor">' + esc(r.vendor) + "</span>" +
          (r.bill_no ? '<span class="bill">' + esc(r.bill_no) + "</span>" : "") +
          (r.doc_type && r.doc_type !== "A/P Invoice"
            ? '<span class="type">' + esc(r.doc_type) + "</span>" : "") +
        "</div>" +
        '<div class="l2">' +
          '<span class="when">Rejected ' + (d ? whenLabel(d) : "—") + ".</span>" +
          (r.reason ? '<q class="reason">' + esc(r.reason) + "</q>"
                    : '<span class="reason none">No reason given</span>') +
        "</div>" +
      "</div>" +
      '<div class="who"><b>' + esc(r.who) + "</b><small>" + esc(r.login) + "</small></div>" +
      '<div class="amt">' + rupees(r.amount) + "</div>" +
    "</li>";
  }

  function renderSheet() {
    var bk = board && board.books[active];
    var name = (BOOKS.filter(function (b) { return b[0] === active; })[0] || [active, active])[1];
    $("sheet-title").textContent = name;
    if (!bk) {
      $("sheet-note").textContent = ""; $("sheet-count").textContent = "";
      $("sheet").innerHTML = '<li class="empty"><strong>' + name + " was not read</strong>" +
        "It will be back on the next good read.</li>";
      return;
    }
    $("sheet-note").textContent = bk.open ? "₹" + lakh(bk.amount) + " held up" : "";
    $("sheet-count").textContent = bk.open
      ? bk.open + " " + plural(bk.open, "entry", "entries") : "";
    if (!bk.rows.length) {
      $("sheet").innerHTML = '<li class="empty"><strong>Nothing rejected in ' + name + "</strong>" +
        "Everything Bhawani has seen here is either approved or still with her.</li>";
      return;
    }
    var now = Date.now();
    $("sheet").innerHTML = bk.rows.map(function (r) { return rowHTML(r, now); }).join("");
  }

  /* Ticks every second so the counter is a real clock, not a value frozen at
     the last fetch. */
  function tick() {
    var now = Date.now();
    Array.prototype.forEach.call(document.querySelectorAll(".row[data-at]"), function (li) {
      var d = parseIST(li.getAttribute("data-at"));
      if (!d) return;
      var ms = now - d.getTime(), b = li.querySelector(".age b");
      if (b) b.textContent = sitting(ms);
      li.className = "row " + band(ms);
    });
    var live = $("live");
    if (board) {
      var age = now - new Date(board.generated_at).getTime();
      if (age > STALE_MS || failed > 2) {
        live.className = "live is-dead";
        live.textContent = "Stopped " + ago(age);
      } else {
        live.className = "live";
        live.textContent = "Live, read " + ago(age);
      }
    } else if (failed > 0) {
      live.className = "live is-dead";
      live.textContent = "Cannot reach the board";
    }
  }

  function render() { renderBooks(); renderBands(); renderSheet(); tick(); }

  /* ---- fetch ----------------------------------------------------------- */
  function load() {
    fetch(window.BOARD_URL + "?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { board = j; failed = 0; render(); })
      .catch(function () {
        failed++;
        // Keep the last good board on screen rather than blanking it; the
        // live line and the band say how old it is.
        if (!board) {
          $("sheet").innerHTML = '<li class="empty"><strong>Cannot reach the board data</strong>' +
            "The publisher on the VPS is not answering. Nothing is shown rather than a wrong zero.</li>";
        }
        renderBands(); tick();
      });
  }

  load();
  setInterval(load, POLL_MS);
  setInterval(tick, 1000);
})();
