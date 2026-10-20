/* Doctor Younger Clinic: page behaviour.
   No libraries. Every feature checks that its elements exist, so one file serves every page. */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Browser storage can be blocked (private mode, strict settings), so every access is guarded.
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
    sget: function (k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } },
    sset: function (k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { /* ignore */ } }
  };

  /* ---------- Intro: first page view of a visit only ---------- */
  var intro = document.querySelector("[data-intro]");
  var introDelay = 0;
  if (intro) {
    if (reduceMotion || store.sget("dy-intro")) {
      intro.classList.add("is-skipped");
    } else {
      store.sset("dy-intro", "1");
      introDelay = 1900;
      document.documentElement.style.setProperty("--intro-delay", introDelay + "ms");
      setTimeout(function () { intro.classList.add("is-skipped"); }, 2700);
    }
  }
  requestAnimationFrame(function () {
    setTimeout(function () { document.body.classList.add("is-loaded"); }, 60);
  });

  /* ---------- Header: solid after scrolling, hides on scroll down ---------- */
  var header = document.querySelector("[data-header]");
  var bar = document.querySelector(".action-bar");
  var lastY = window.scrollY;
  function onScroll() {
    var y = window.scrollY;
    if (header) {
      header.classList.toggle("is-solid", y > 40);
      header.classList.toggle("is-hidden", y > 400 && y > lastY && !document.body.classList.contains("menu-open"));
    }
    if (bar) bar.classList.toggle("is-shown", y > 300);
    lastY = y;
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile menu ---------- */
  var toggle = document.querySelector("[data-menu-toggle]");
  var nav = document.querySelector("[data-nav]");
  if (toggle && nav) {
    var label = toggle.querySelector(".menu-toggle__label");
    function setMenu(open) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      nav.classList.toggle("is-open", open);
      document.body.classList.toggle("menu-open", open);
      label.textContent = open ? label.dataset.close : label.dataset.open;
    }
    toggle.addEventListener("click", function () { setMenu(toggle.getAttribute("aria-expanded") !== "true"); });
    nav.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });
  }

  /* ---------- Reveal on scroll ---------- */
  var revealables = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    revealables.forEach(function (el) { io.observe(el); });
  } else {
    revealables.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---------- Gentle parallax on arch images ---------- */
  var parallax = document.querySelectorAll("[data-parallax] img");
  if (parallax.length && !reduceMotion) {
    var ticking = false;
    function update() {
      parallax.forEach(function (img) {
        var r = img.parentElement.getBoundingClientRect();
        var p = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
        img.style.transform = "scale(1.1) translateY(" + (p * -24).toFixed(1) + "px)";
      });
      ticking = false;
    }
    window.addEventListener("scroll", function () { if (!ticking) { requestAnimationFrame(update); ticking = true; } }, { passive: true });
    update();
  }

  /* ---------- Doctors on duty ---------- */
  var dataEl = document.getElementById("duty-data");
  var duty = document.querySelector("[data-duty]");
  if (dataEl && duty) {
    var data = JSON.parse(dataEl.textContent);
    var list = duty.querySelector("[data-duty-list]");
    var empty = duty.querySelector("[data-duty-empty]");
    var dayButtons = duty.querySelectorAll("[data-duty-day]");
    var branchButtons = duty.querySelectorAll("[data-duty-branch]");

    // Today in Bangkok, Monday = 0
    var now = new Date(new Date().toLocaleString("en-US", { timeZone: "Asia/Bangkok" }));
    var todayIndex = (now.getDay() + 6) % 7;

    var state = {
      branch: duty.dataset.branch || store.get("dy-branch") || (branchButtons[0] && branchButtons[0].dataset.dutyBranch),
      day: todayIndex
    };

    // The date that the selected weekday falls on this week, used for "week of the month" shifts.
    function dateFor(dayIndex) {
      var d = new Date(now);
      d.setDate(now.getDate() + (dayIndex - todayIndex));
      return d;
    }
    function weekOfMonth(d) { return Math.ceil(d.getDate() / 7); }

    function render() {
      var date = dateFor(state.day);
      var week = weekOfMonth(date);
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
        li.style.animationDelay = (i * 70) + "ms";
        var img = document.createElement("img");
        img.src = row.doc.photo; img.alt = ""; img.loading = "lazy";
        var text = document.createElement("div");
        var name = document.createElement("strong");
        name.textContent = row.doc.name;
        var time = document.createElement("span");
        time.textContent = (row.doc.nickname ? row.doc.nickname + " · " : "") +
          row.shift.from.replace(":", ".") + " - " + row.shift.to.replace(":", ".") +
          (data.suffix ? " " + data.suffix : "");
        text.appendChild(name); text.appendChild(time);
        li.appendChild(img); li.appendChild(text);
        list.appendChild(li);
      });
      empty.hidden = rows.length > 0;

      dayButtons.forEach(function (b) {
        var i = Number(b.dataset.dutyDay);
        b.setAttribute("aria-selected", i === state.day ? "true" : "false");
        b.classList.toggle("is-today", i === todayIndex);
      });
      branchButtons.forEach(function (b) {
        b.setAttribute("aria-selected", b.dataset.dutyBranch === state.branch ? "true" : "false");
      });
    }

    dayButtons.forEach(function (b) {
      b.addEventListener("click", function () { state.day = Number(b.dataset.dutyDay); render(); });
    });
    branchButtons.forEach(function (b) {
      b.addEventListener("click", function () {
        state.branch = b.dataset.dutyBranch; store.set("dy-branch", state.branch); render();
      });
    });
    render();
  }

  /* ---------- Cookie consent, then Google Analytics ---------- */
  var cookie = document.querySelector("[data-cookie]");
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
    cookie.querySelector("[data-cookie-accept]").addEventListener("click", function () {
      store.set("dy-consent", "yes"); cookie.hidden = true; loadAnalytics();
    });
    cookie.querySelector("[data-cookie-decline]").addEventListener("click", function () {
      store.set("dy-consent", "no"); cookie.hidden = true;
    });
  }
})();
