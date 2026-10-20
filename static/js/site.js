/* Doctor Younger Clinic: page behaviour.
   No libraries. Every feature checks that its elements exist, so one file serves every page. */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // Browser storage can be blocked (private mode, strict settings), so every access is guarded.
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* ignore */ } },
    sget: function (k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } },
    sset: function (k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { /* ignore */ } }
  };

  /* ---------- Intro: first page view of a visit only ---------- */
  var intro = $("[data-intro]");
  if (intro) {
    if (reduceMotion || store.sget("dy-intro")) {
      intro.classList.add("is-skipped");
    } else {
      store.sset("dy-intro", "1");
      document.documentElement.style.setProperty("--intro-delay", "1900ms");
      setTimeout(function () { intro.classList.add("is-skipped"); }, 2700);
    }
  }
  requestAnimationFrame(function () { setTimeout(function () { document.body.classList.add("is-loaded"); }, 60); });

  /* ---------- Split headings into words for the rise-in ---------- */
  $$("[data-split]").forEach(function (el) {
    var words = el.textContent.trim().split(/\s+/);
    el.setAttribute("aria-label", el.textContent.trim());
    el.innerHTML = words.map(function (w, i) {
      return '<span class="w" aria-hidden="true"><span style="--i:' + i + '">' + w.replace(/[<>&]/g, "") + "</span></span>";
    }).join(" ");
    el.setAttribute("data-reveal-split", "");
  });

  /* ---------- Header, scroll progress, floating buttons ---------- */
  var header = $("[data-header]");
  var progress = $("[data-progress]");
  var readBar = $("[data-read-progress]");
  var bar = $(".action-bar");
  var lineFloat = $(".line-float");
  var lastY = window.scrollY;
  function onScroll() {
    var y = window.scrollY;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (header) {
      header.classList.toggle("is-solid", y > 40);
      header.classList.toggle("is-hidden", y > 400 && y > lastY && !document.body.classList.contains("menu-open"));
    }
    if (progress) progress.style.transform = "scaleX(" + (max > 0 ? y / max : 0) + ")";
    if (readBar) readBar.style.transform = "scaleX(" + (max > 0 ? y / max : 0) + ")";
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

  /* ---------- Reveal on scroll (text, frames, split headings, diagrams) ---------- */
  var revealables = $$("[data-reveal], [data-frame], [data-split], [data-skin]");
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

  /* ---------- Count-up numbers ---------- */
  var counters = $$("[data-count]");
  if (counters.length && "IntersectionObserver" in window && !reduceMotion) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target, target = Number(el.dataset.count), t0 = performance.now();
        var tick = function (t) {
          var p = Math.min(1, (t - t0) / 1600), e = 1 - Math.pow(1 - p, 4);
          el.textContent = Math.round(target * e);
          if (p < 1) requestAnimationFrame(tick);
        };
        el.textContent = "0";
        requestAnimationFrame(tick);
        co.unobserve(el);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { co.observe(el); });
  }

  /* ---------- Mouse-follow layers, magnetic buttons, tilt (mouse only) ---------- */
  if (finePointer && !reduceMotion) {
    $$("[data-mouse-layer]").forEach(function (layer) {
      var host = layer.closest("section") || document.body;
      host.addEventListener("mousemove", function (e) {
        var r = host.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
        layer.style.transform = "translate3d(" + (x * -18).toFixed(1) + "px," + (y * -14).toFixed(1) + "px,0)";
      });
      host.addEventListener("mouseleave", function () { layer.style.transform = ""; });
      layer.style.transition = "transform .8s cubic-bezier(.16,1,.3,1)";
    });

    $$("[data-magnetic]").forEach(function (el) {
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var x = e.clientX - r.left - r.width / 2, y = e.clientY - r.top - r.height / 2;
        el.style.transform = "translate(" + (x * 0.25).toFixed(1) + "px," + (y * 0.35).toFixed(1) + "px)";
      });
      el.addEventListener("mouseleave", function () { el.style.transform = ""; });
    });

    $$("[data-tilt], [data-tilt-big]").forEach(function (el) {
      var amp = el.hasAttribute("data-tilt-big") ? 10 : 6;
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform = "perspective(900px) rotateY(" + (x * amp).toFixed(2) + "deg) rotateX(" + (-y * amp).toFixed(2) + "deg)";
      });
      el.addEventListener("mouseleave", function () { el.style.transform = ""; });
      el.style.transition = "transform .5s cubic-bezier(.16,1,.3,1)";
    });

    /* Custom cursor ring that grows over links */
    var cursor = $("[data-cursor]");
    if (cursor) {
      var cx = 0, cy = 0, tx = 0, ty = 0;
      document.addEventListener("mousemove", function (e) {
        tx = e.clientX; ty = e.clientY;
        document.body.classList.add("has-cursor");
        cursor.classList.toggle("is-link", !!e.target.closest("a, button, summary, [data-drag-scroll]"));
      });
      document.addEventListener("mouseleave", function () { document.body.classList.remove("has-cursor"); });
      (function loop() {
        cx += (tx - cx) * 0.2; cy += (ty - cy) * 0.2;
        cursor.style.transform = "translate(" + cx + "px," + cy + "px)";
        requestAnimationFrame(loop);
      })();
    }

    /* Floating picture that follows the cursor over list rows */
    $$("[data-hover-preview], .news-list").forEach(function (list) {
      var box = list.querySelector("[data-preview-box]");
      if (!box) { box = document.createElement("div"); box.className = "hover-preview"; box.innerHTML = '<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="">'; list.appendChild(box); }
      var img = box.querySelector("img");
      list.addEventListener("mousemove", function (e) {
        box.style.left = e.clientX + 24 + "px"; box.style.top = e.clientY + "px";
      });
      $$("[data-preview]", list).forEach(function (row) {
        row.addEventListener("mouseenter", function () {
          if (!row.dataset.preview) return;
          img.src = row.dataset.preview; box.classList.add("is-on");
        });
        row.addEventListener("mouseleave", function () { box.classList.remove("is-on"); });
      });
    });
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
          c.animate([{ opacity: 0, transform: "translateY(24px) scale(.97)" }, { opacity: 1, transform: "none" }],
                    { duration: 600, delay: i * 30, easing: "cubic-bezier(.16,1,.3,1)", fill: "backwards" });
        }
      });
    }
    chips.forEach(function (c) { c.addEventListener("click", function () { select(c.dataset.concern, true); }); });
    select(finder.dataset.start || "all", false);
  });

  /* ---------- Gold dust behind the hero ---------- */
  var dust = $("[data-dust]");
  if (dust && !reduceMotion && dust.getContext) {
    var ctx = dust.getContext("2d"), parts = [], w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    var size = function () {
      w = dust.clientWidth; h = dust.clientHeight;
      dust.width = w * dpr; dust.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    size(); window.addEventListener("resize", size);
    for (var i = 0; i < 60; i++) {
      parts.push({ x: Math.random(), y: Math.random(), r: Math.random() * 1.8 + 0.4, s: Math.random() * 0.00025 + 0.00008, p: Math.random() * Math.PI * 2 });
    }
    var mx = 0.5, my = 0.5;
    dust.parentElement.addEventListener("mousemove", function (e) {
      var r = dust.getBoundingClientRect(); mx = (e.clientX - r.left) / r.width; my = (e.clientY - r.top) / r.height;
    });
    var visible = true;
    if ("IntersectionObserver" in window) new IntersectionObserver(function (en) { visible = en[0].isIntersecting; }).observe(dust);
    (function draw(t) {
      if (visible) {
        ctx.clearRect(0, 0, w, h);
        parts.forEach(function (q) {
          q.y -= q.s * 16; if (q.y < -0.02) { q.y = 1.02; q.x = Math.random(); }
          var x = (q.x + (mx - 0.5) * 0.03 * q.r) * w + Math.sin(t / 2000 + q.p) * 8;
          var y = (q.y + (my - 0.5) * 0.03 * q.r) * h;
          var a = 0.25 + 0.35 * Math.sin(t / 900 + q.p) ** 2;
          ctx.beginPath(); ctx.arc(x, y, q.r, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(182,158,89," + a.toFixed(3) + ")"; ctx.fill();
        });
      }
      requestAnimationFrame(draw);
    })(0);
  }

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
        li.style.animationDelay = (i * 70) + "ms";
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
