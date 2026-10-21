/* Doctor Younger Clinic: page behaviour.
   No libraries. Every feature checks that its elements exist, so one file serves every page. */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // Browser storage can be blocked (private mode, strict settings), so every access is guarded.
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* ignore */ } }
  };

  requestAnimationFrame(function () { setTimeout(function () { document.body.classList.add("is-loaded"); }, 60); });

  /* ---------- Header and floating buttons ---------- */
  var header = $("[data-header]");
  var bar = $(".action-bar");
  var lineFloat = $(".line-float");
  var lastY = window.scrollY;
  function onScroll() {
    var y = window.scrollY;
    if (header) {
      header.classList.toggle("is-solid", y > 40);
      header.classList.toggle("is-hidden", y > 400 && y > lastY && !document.body.classList.contains("menu-open"));
    }
    if (bar) bar.classList.toggle("is-shown", y > 300);
    if (lineFloat) lineFloat.classList.toggle("is-shown", y > 500);
    lastY = y;
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile menu ---------- */
  var toggle = $("[data-menu-toggle]");
  var nav = $("[data-nav]");
  if (toggle && nav) {
    var label = toggle.querySelector(".menu-toggle__label");
    var setMenu = function (open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      nav.classList.toggle("is-open", open);
      document.body.classList.toggle("menu-open", open);
      label.textContent = open ? label.dataset.close : label.dataset.open;
    };
    toggle.addEventListener("click", function () { setMenu(toggle.getAttribute("aria-expanded") !== "true"); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });
  }

  /* ---------- Reveal on scroll: one soft fade per block, and the skin diagram ---------- */
  var revealables = $$("[data-reveal], [data-frame], [data-skin]");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.1 });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---------- Drag to scroll rows ---------- */
  $$("[data-drag-scroll]").forEach(function (row) {
    var down = false, startX = 0, startLeft = 0, moved = 0;
    row.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse") return;
      down = true; moved = 0; startX = e.clientX; startLeft = row.scrollLeft;
    });
    window.addEventListener("pointermove", function (e) {
      if (!down) return;
      var dx = e.clientX - startX; moved = Math.abs(dx);
      if (moved > 4) row.classList.add("is-dragging");
      row.scrollLeft = startLeft - dx;
    });
    window.addEventListener("pointerup", function () {
      down = false;
      setTimeout(function () { row.classList.remove("is-dragging"); }, 0);
    });
    row.addEventListener("click", function (e) { if (moved > 4) e.preventDefault(); }, true);
  });

  /* ---------- Treatment finder ---------- */
  $$("[data-finder]").forEach(function (finder) {
    var chips = $$("[data-concern]", finder);
    var cells = $$(".svc-grid__cell", finder);
    function select(id, animate) {
      chips.forEach(function (c) { c.setAttribute("aria-selected", c.dataset.concern === id ? "true" : "false"); });
      // FLIP: remember where visible cards were, change the filter, then animate from the old spot
      var first = new Map();
      if (animate && !reduceMotion) cells.forEach(function (c) { if (!c.classList.contains("is-hidden")) first.set(c, c.getBoundingClientRect()); });
      cells.forEach(function (c) {
        var show = id === "all" || (" " + c.dataset.concerns + " ").indexOf(" " + id + " ") !== -1;
        c.classList.toggle("is-hidden", !show);
      });
      if (!animate || reduceMotion) return;
      cells.forEach(function (c, i) {
        if (c.classList.contains("is-hidden")) return;
        var last = c.getBoundingClientRect(), f = first.get(c);
        var card = c.firstElementChild;
        card.classList.add("is-in");
        if (f) {
          c.style.transform = "translate(" + (f.left - last.left) + "px," + (f.top - last.top) + "px)";
          c.style.transition = "none";
          requestAnimationFrame(function () { c.style.transition = ""; c.style.transform = ""; });
        } else {
          c.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400, easing: "ease", fill: "backwards" });
        }
      });
    }
    chips.forEach(function (c) { c.addEventListener("click", function () { select(c.dataset.concern, true); }); });
    select(finder.dataset.start || "all", false);
  });

  /* ---------- Doctors on duty ---------- */
  var dataEl = $("#duty-data");
  var duty = $("[data-duty]");
  if (dataEl && duty) {
    var data = JSON.parse(dataEl.textContent);
    var list = $("[data-duty-list]", duty);
    var empty = $("[data-duty-empty]", duty);
    var dayButtons = $$("[data-duty-day]", duty);
    var branchButtons = $$("[data-duty-branch]", duty);

    // Today in Bangkok, Monday = 0
    var now = new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Bangkok" }));
    var todayIndex = (now.getDay() + 6) % 7;
    var state = {
      branch: duty.dataset.branch || store.get("dy-branch") || (branchButtons[0] && branchButtons[0].dataset.dutyBranch),
      day: todayIndex
    };
    // The date the selected weekday falls on this week, for "week of the month" shifts.
    var dateFor = function (dayIndex) { var d = new Date(now); d.setDate(now.getDate() + (dayIndex - todayIndex)); return d; };
    var weekOfMonth = function (d) { return Math.ceil(d.getDate() / 7); };

    var render = function () {
      var week = weekOfMonth(dateFor(state.day));
      var rows = [];
      data.doctors.forEach(function (doc) {
        doc.shifts.forEach(function (s) {
          if (s.branch !== state.branch || s.days.indexOf(state.day) === -1) return;
          if (s.weeks && s.weeks.indexOf(week) === -1) return;
          if (s.except && s.except.indexOf(week) !== -1) return;
          rows.push({ doc: doc, shift: s });
        });
      });
      rows.sort(function (a, b) { return a.shift.from.localeCompare(b.shift.from); });
      list.innerHTML = "";
      rows.forEach(function (row, i) {
        var li = document.createElement("li");
        li.className = "duty__item";
        var a = document.createElement("a"); a.href = row.doc.url;
        var img = document.createElement("img"); img.src = row.doc.photo; img.alt = ""; img.loading = "lazy";
        var text = document.createElement("div");
        var name = document.createElement("strong"); name.textContent = row.doc.name;
        var time = document.createElement("span");
        time.textContent = (row.doc.nickname ? row.doc.nickname + " · " : "") +
          row.shift.from.replace(":", ".") + " - " + row.shift.to.replace(":", ".") + (data.suffix ? " " + data.suffix : "");
        text.appendChild(name); text.appendChild(time);
        a.appendChild(img); a.appendChild(text); li.appendChild(a); list.appendChild(li);
      });
      empty.hidden = rows.length > 0;
      dayButtons.forEach(function (b) {
        var i = Number(b.dataset.dutyDay);
        b.setAttribute("aria-selected", i === state.day ? "true" : "false");
        b.classList.toggle("is-today", i === todayIndex);
      });
      branchButtons.forEach(function (b) { b.setAttribute("aria-selected", b.dataset.dutyBranch === state.branch ? "true" : "false"); });
    };
    dayButtons.forEach(function (b) { b.addEventListener("click", function () { state.day = Number(b.dataset.dutyDay); render(); }); });
    branchButtons.forEach(function (b) {
      b.addEventListener("click", function () { state.branch = b.dataset.dutyBranch; store.set("dy-branch", state.branch); render(); });
    });
    render();
  }

  /* ---------- Cookie consent, then Google Analytics ---------- */
  var cookie = $("[data-cookie]");
  function loadAnalytics() {
    if (!window.DY || !window.DY.ga4) return;
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + window.DY.ga4;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", window.DY.ga4);
    // Count calls and LINE taps, which are the clinic's bookings.
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a");
      if (!a) return;
      if (a.href.indexOf("tel:") === 0) window.gtag("event", "call", { number: a.href.slice(4) });
      else if (a.href.indexOf("line.me") !== -1) window.gtag("event", "line_click");
    });
  }
  if (cookie) {
    var choice = store.get("dy-consent");
    if (choice === "yes") loadAnalytics();
    else if (!choice) cookie.hidden = false;
    $("[data-cookie-accept]", cookie).addEventListener("click", function () { store.set("dy-consent", "yes"); cookie.hidden = true; loadAnalytics(); });
    $("[data-cookie-decline]", cookie).addEventListener("click", function () { store.set("dy-consent", "no"); cookie.hidden = true; });
  }
})();
