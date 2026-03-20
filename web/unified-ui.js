(function () {
  "use strict";

  var THEME_KEY = "sf_theme";
  var FALLBACK_THEME = "dark";
  var FORCE_DARK_THEME = true;
  var QUICK_OPEN_ID = "sf-quick-open";
  var QUICK_INPUT_ID = "sf-quick-open-input";

  function ensureMetaCharset() {
    if (document.querySelector('meta[charset]')) return;
    var meta = document.createElement("meta");
    meta.setAttribute("charset", "UTF-8");
    if (document.head && document.head.firstChild) {
      document.head.insertBefore(meta, document.head.firstChild);
    } else if (document.head) {
      document.head.appendChild(meta);
    }
  }

  function ensureLanguage() {
    if (!document.documentElement.getAttribute("lang")) {
      document.documentElement.setAttribute("lang", "ko");
    }
  }

  function getStoredTheme() {
    try {
      var value = localStorage.getItem(THEME_KEY);
      if (value === "light" || value === "dark") return value;
    } catch (e) {}
    return null;
  }

  function getSystemTheme() {
    // Keep default consistent across pages that use different style bundles.
    return "dark";
  }

  function setThemeColorMeta(theme) {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement("meta");
      meta.setAttribute("name", "theme-color");
      if (document.head) document.head.appendChild(meta);
    }
    meta.setAttribute("content", theme === "dark" ? "#0d1422" : "#f4f7fb");
  }

  function applyTheme(theme) {
    var next = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    setThemeColorMeta(next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch (e) {}
    updateToggleLabel(next);
  }

  function toggleTheme() {
    applyTheme("dark");
  }

  function updateToggleLabel(theme) {
    var button = document.getElementById("sf-theme-toggle");
    if (!button) return;
    button.textContent = theme === "dark" ? "L" : "D";
    button.setAttribute(
      "aria-label",
      theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
    );
    button.title = theme === "dark" ? "Light mode" : "Dark mode";
  }

  function ensureToggleButton() {
    if (FORCE_DARK_THEME) return;
    if (!document.body) return;
    if (document.getElementById("sf-theme-toggle")) return;
    var button = document.createElement("button");
    button.id = "sf-theme-toggle";
    button.type = "button";
    button.className = "sf-theme-toggle";
    button.addEventListener("click", toggleTheme);
    document.body.appendChild(button);
    updateToggleLabel(document.documentElement.getAttribute("data-theme") || FALLBACK_THEME);
  }

  function collectQuickLinks() {
    return Array.prototype.slice.call(document.querySelectorAll("a[href]"))
      .map(function (link) {
        var href = link.getAttribute("href");
        var text = (link.textContent || "").replace(/\s+/g, " ").trim();
        if (!href || !text || href.charAt(0) === "#") return null;
        return { href: href, text: text };
      })
      .filter(function (item, index, arr) {
        if (!item) return false;
        return arr.findIndex(function (candidate) {
          return candidate && candidate.href === item.href;
        }) === index;
      })
      .slice(0, 24);
  }

  function renderQuickLinks(query) {
    var root = document.getElementById(QUICK_OPEN_ID);
    if (!root) return;
    var list = root.querySelector("[data-quick-open-list]");
    if (!list) return;
    var normalized = String(query || "").toLowerCase().trim();
    var links = collectQuickLinks().filter(function (item) {
      return !normalized || item.text.toLowerCase().indexOf(normalized) !== -1 || item.href.toLowerCase().indexOf(normalized) !== -1;
    });
    list.innerHTML = links.length
      ? links.map(function (item, index) {
          return '<a class="sf-quick-open-item" href="' + item.href + '" data-quick-open-item="' + index + '">' +
            '<span>' + item.text + '</span><span class="sf-quick-open-hint">' + item.href + '</span></a>';
        }).join("")
      : '<div class="sf-quick-open-empty">일치하는 화면이 없습니다.</div>';
  }

  function ensureQuickOpen() {
    if (!document.body || document.getElementById(QUICK_OPEN_ID)) return;
    var root = document.createElement("div");
    root.id = QUICK_OPEN_ID;
    root.className = "sf-quick-open hidden";
    root.innerHTML = '' +
      '<div class="sf-quick-open-backdrop" data-quick-open-close="true"></div>' +
      '<div class="sf-quick-open-panel" role="dialog" aria-modal="true" aria-label="빠른 이동">' +
        '<div class="sf-quick-open-head">' +
          '<span class="sf-quick-open-title">빠른 이동</span>' +
          '<span class="sf-quick-open-shortcut">Ctrl+K</span>' +
        '</div>' +
        '<input id="' + QUICK_INPUT_ID + '" class="sf-quick-open-input" type="text" placeholder="화면 이름이나 경로를 입력하세요" autocomplete="off" />' +
        '<div class="sf-quick-open-list" data-quick-open-list="true"></div>' +
      '</div>';
    document.body.appendChild(root);
    root.addEventListener("click", function (event) {
      if (event.target && event.target.getAttribute("data-quick-open-close") === "true") {
        root.classList.add("hidden");
      }
    });
    var input = document.getElementById(QUICK_INPUT_ID);
    if (input) {
      input.addEventListener("input", function (event) {
        renderQuickLinks(event.target.value);
      });
    }
  }

  function openQuickOpen() {
    ensureQuickOpen();
    var root = document.getElementById(QUICK_OPEN_ID);
    var input = document.getElementById(QUICK_INPUT_ID);
    if (!root || !input) return;
    renderQuickLinks("");
    root.classList.remove("hidden");
    input.value = "";
    input.focus();
  }

  function bindQuickOpenShortcut() {
    document.addEventListener("keydown", function (event) {
      var key = String(event.key || "").toLowerCase();
      var target = event.target;
      var typing = target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable);
      if (key === "escape") {
        var root = document.getElementById(QUICK_OPEN_ID);
        if (root && !root.classList.contains("hidden")) root.classList.add("hidden");
        return;
      }
      if (typing) return;
      if ((event.ctrlKey || event.metaKey) && key === "k") {
        event.preventDefault();
        openQuickOpen();
        return;
      }
      if (key === "/") {
        event.preventDefault();
        openQuickOpen();
      }
    });
  }

  function init() {
    ensureMetaCharset();
    ensureLanguage();
    var initialTheme = FORCE_DARK_THEME ? "dark" : (getStoredTheme() || getSystemTheme() || FALLBACK_THEME);
    applyTheme(initialTheme);
    ensureToggleButton();
    ensureQuickOpen();
    bindQuickOpenShortcut();
  }

  window.setSoftFactoryTheme = applyTheme;
  window.getSoftFactoryTheme = function () {
    return document.documentElement.getAttribute("data-theme") || FALLBACK_THEME;
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
