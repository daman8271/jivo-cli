/* board.js — JIVO Approval Board.
   The page holds no numbers of its own. Everything is fetched from the VPS
   publisher every 30 seconds; the ages tick every second off each row's own
   rejection timestamp, so the clock is honest even between fetches. */
(function () {
  "use strict";

  var BOOKS = [["OIL", "Oil", "oil"], ["MART", "Mart", "mart"], ["BEV", "Beverages", "bev"]];
  var POLL_MS = 30000, STALE_MS = 300000;
  var board = null, active = "OIL", failed = 0;

  var $ = function (id) { return document.getElementById(id); };

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

  function crore(n) {
    n = Number(n) || 0;
    if (n >= 10000000) return "₹" + (n / 10000000).toFixed(2) + " cr";
    if (n >= 100000) return "₹" + (n / 100000).toFixed(2) + " L";
    return "₹" + rupees(n);
  }

  /* SAP hands us a wall-clock IST stamp with no zone. Pin it to +05:30 so the
     age is right on a phone that is not on IST. */
  function parseIST(s) {
    if (!s) return null;
    var d = new Date(s.replace(" ", "T") + "+05:30");
    return isNaN(d.getTime()) ? null : d;
  }

  function sitting(ms) {
    if (ms == null) return "—";
    var m = Math.floor(ms / 60000), h = Math.floor(m / 60), d = Math.floor(h / 24);
    if (d >= 1) return d + "d " + (h % 24) + "h";
    if (h >= 1) return h + "h " + (m % 60) + "m";
    return Math.max(m, 0) + "m";
  }

  function band(ms) {                        // age -> chip class
    var d = ms / 86400000;
    if (d >= 90) return "chip--other";
    if (d >= 7) return "chip--danger";
    if (d >= 2) return "chip--warn";
    return "chip--neutral";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function hhmm(d) {
    return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
  }

  function rejectedLabel(d) {
    return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) + " " + hhmm(d);
  }

  /* ---- render ---------------------------------------------------------- */
  function renderTabs() {
    $("tabs").innerHTML = BOOKS.map(function (b) {
      var bk = board && board.books[b[0]], n = bk ? bk.open : 0;
      var late = bk ? bk.late : 0;
      return '<button class="tab' + (b[0] === active ? " is-active" : "") +
        '" role="tab" data-book="' + b[0] + '" data-co="' + b[2] + '">' + b[1] +
        ' <span class="count">' + n + "</span>" +
        (late ? ' <span class="count" style="background:var(--danger-bg);color:var(--danger)">' + late + "</span>" : "") +
        "</button>";
    }).join("");
    Array.prototype.forEach.call($("tabs").querySelectorAll(".tab"), function (el) {
      el.addEventListener("click", function () {
        active = el.getAttribute("data-book");
        document.documentElement.setAttribute("data-co", el.getAttribute("data-co"));
        render();
      });
    });
  }

  function renderBanner() {
    var el = $("banner"), bits = [];
    if (!board) { el.innerHTML = ""; return; }

    var errs = Object.keys(board.errors || {});
    if (errs.length) {
      bits.push('<div class="warnbox warnbox--danger"><strong>' + errs.join(", ") +
        " could not be read.</strong> Those books are not on this board at all &mdash; " +
        "this is not a zero. " + esc(board.errors[errs[0]]).slice(0, 160) + "</div>");
    }

    var age = Date.now() - new Date(board.generated_at).getTime();
    if (age > STALE_MS || failed > 2) {
      bits.push('<div class="warnbox"><strong>This board has stopped updating.</strong> ' +
        "Last read from SAP was " + sitting(age) + " ago. The numbers below are from then, not now.</div>");
    }

    var late = board.totals.late_alarmable || 0;
    if (late > 0) {
      bits.push('<div class="warnbox warnbox--danger"><strong>' + late + " rejected " +
        (late > 1 ? "entries are" : "entry is") + " past 2 days.</strong> " +
        "Bhawani sent " + (late > 1 ? "them" : "it") + " back and " +
        (late > 1 ? "they have" : "it has") + " not been re-done.</div>");
    }
    el.innerHTML = bits.join("");
    document.title = (board.totals.late_alarmable ? "(" + board.totals.late_alarmable + ") " : "") +
      "JIVO Approval Board";
  }

  function renderKpis() {
    var bk = board && board.books[active];
    if (!bk) { $("kpis").innerHTML = ""; return; }
    var over2 = bk.late, cleared = board.totals.cleared_today;
    $("kpis").innerHTML = [
      kpi("Rejected, still open", bk.open, "", bk.open ? "" : "is-ok"),
      kpi("Past 2 days", over2, "", over2 ? "is-danger" : "is-ok"),
      kpi("Cleared today", cleared, "all three books", "is-ok"),
      kpi("Value held up", crore(bk.amount), "", "is-muted")
    ].join("");
  }

  function kpi(label, value, sub, cls) {
    return '<div class="kpi ' + (cls || "") + '"><span class="kpi-l">' + label +
      '</span><span class="kpi-v">' + value + "</span>" +
      (sub ? '<span class="kpi-sub">' + sub + "</span>" : "") + "</div>";
  }

  function renderTable() {
    var bk = board && board.books[active];
    var box = $("tblbox");
    if (!bk) { box.innerHTML = '<div class="empty"><strong>No data</strong>this book was not read.</div>'; return; }
    if (!bk.rows.length) {
      box.innerHTML = '<div class="empty"><strong>Nothing rejected</strong>' +
        "every entry in this book is either approved or waiting with Bhawani.</div>";
      return;
    }
    var now = Date.now();
    box.innerHTML = '<table class="tbl"><thead><tr>' +
      "<th>Draft</th><th>Type</th><th>Vendor</th><th>Bill no.</th>" +
      '<th class="num">Amount</th><th>Keyed by</th><th>Rejected</th><th>Sitting</th>' +
      "</tr></thead><tbody>" +
      bk.rows.map(function (r) {
        var d = parseIST(r.rejected_at), ms = d ? now - d.getTime() : null;
        return '<tr data-at="' + esc(r.rejected_at) + '">' +
          '<td class="mono">' + r.doc_entry + "</td>" +
          "<td>" + esc(r.doc_type) + "</td>" +
          '<td><span class="ellipsis" title="' + esc(r.vendor) + '">' + esc(r.vendor) + "</span></td>" +
          '<td class="mono wrap-anywhere">' + esc(r.bill_no) + "</td>" +
          '<td class="num">' + rupees(r.amount) + "</td>" +
          '<td class="who">' + esc(r.who) + "</td>" +
          '<td class="when">' + (d ? rejectedLabel(d) : "—") + "</td>" +
          '<td><span class="chip ' + (ms == null ? "chip--neutral" : band(ms)) + ' age">' +
          sitting(ms) + "</span></td>" +
          "</tr>" +
          '<tr class="reasonrow"><td></td><td colspan="7">' +
          (r.reason ? '<span class="reason">' + esc(r.reason) + "</span>"
                    : '<span class="reason noreason">no reason given</span>') +
          "</td></tr>";
      }).join("") + "</tbody></table>";
  }

  /* Ticks every second so "Sitting" is a real clock, not a value frozen at the
     last fetch. */
  function tickAges() {
    var now = Date.now();
    Array.prototype.forEach.call(document.querySelectorAll("tr[data-at]"), function (tr) {
      var d = parseIST(tr.getAttribute("data-at"));
      if (!d) return;
      var ms = now - d.getTime(), chip = tr.querySelector(".age");
      if (!chip) return;
      chip.textContent = sitting(ms);
      chip.className = "chip " + band(ms) + " age";
    });
    if (board) {
      var age = Date.now() - new Date(board.generated_at).getTime();
      $("freshness").innerHTML = age > STALE_MS
        ? '<span class="dead">stopped · ' + sitting(age) + " old</span>"
        : "live · read from SAP " + sitting(age) + " ago";
    }
  }

  function render() {
    renderTabs(); renderBanner(); renderKpis(); renderTable(); tickAges();
    var bk = board && board.books[active];
    $("booknote").textContent = bk
      ? bk.open + " rejected, " + crore(bk.amount) + " held up"
      : "";
  }

  /* ---- fetch ----------------------------------------------------------- */
  function load() {
    fetch(window.BOARD_URL + "?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { board = j; failed = 0; render(); })
      .catch(function () {
        failed++;
        // Keep the last good board on screen rather than blanking it; the
        // freshness line says how old it is.
        if (!board) {
          $("tblbox").innerHTML = '<div class="empty"><strong>Cannot reach the board data</strong>' +
            "the VPS publisher is not answering. Nothing is shown rather than a wrong zero.</div>";
        }
        renderBanner();
      });
  }

  load();
  setInterval(load, POLL_MS);
  setInterval(tickAges, 1000);
})();
