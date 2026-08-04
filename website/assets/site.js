/* Astral Orchestrator site behavior.
   Loaded synchronously in <head> so the theme is applied before first
   paint. All DOM wiring waits for DOMContentLoaded. It makes no programmatic
   network calls, analytics, or cookie writes. */

(() => {
  "use strict";

  const root = document.documentElement;
  root.classList.add("js");

  function mediaQuery(query) {
    return typeof window.matchMedia === "function"
      ? window.matchMedia(query)
      : { matches: false };
  }

  /* ---------- Theme: light / dark / system ---------- */

  const THEME_KEY = "astral-theme";
  const THEME_CHOICES = ["light", "dark", "system"];
  const systemQuery = mediaQuery("(prefers-color-scheme: dark)");
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  const THEME_COLORS = { light: "#f4f2ec", dark: "#070b18" };
  const themeToggles = [];

  const storage = {
    read(key) {
      try {
        return window.localStorage.getItem(key);
      } catch {
        return null;
      }
    },
    write(key, value) {
      try {
        window.localStorage.setItem(key, value);
      } catch {
        /* Storage is optional: the active theme remains available this visit. */
      }
    },
  };

  function storedThemeChoice() {
    const saved = storage.read(THEME_KEY);
    return THEME_CHOICES.includes(saved) ? saved : "system";
  }

  let activeThemeChoice = storedThemeChoice();

  function themeChoice() {
    return activeThemeChoice;
  }

  function setThemeChoice(choice) {
    activeThemeChoice = choice;
    storage.write(THEME_KEY, choice);
  }

  function resolveTheme(choice) {
    if (choice === "system") {
      return systemQuery.matches ? "dark" : "light";
    }
    return choice;
  }

  function syncThemeToggles() {
    const choice = themeChoice();
    const resolved = resolveTheme(choice);
    const label =
      choice === "system"
        ? `Theme: system (currently ${resolved}). Activate for light theme.`
        : choice === "light"
          ? "Theme: light. Activate for dark theme."
          : "Theme: dark. Activate for system theme.";

    themeToggles.forEach((toggle) => {
      toggle.dataset.choice = choice;
      toggle.setAttribute("aria-label", label);
      toggle.setAttribute("title", label);
    });
  }

  function applyTheme() {
    const resolved = resolveTheme(themeChoice());
    root.dataset.theme = resolved;
    if (themeMeta) {
      themeMeta.setAttribute("content", THEME_COLORS[resolved]);
    }
    syncThemeToggles();
  }

  applyTheme();

  function onSystemThemeChange() {
    if (themeChoice() === "system") {
      applyTheme();
    }
  }

  if (typeof systemQuery.addEventListener === "function") {
    systemQuery.addEventListener("change", onSystemThemeChange);
  } else if (typeof systemQuery.addListener === "function") {
    systemQuery.addListener(onSystemThemeChange);
  }

  const reduceMotion = mediaQuery("(prefers-reduced-motion: reduce)");

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  onReady(() => {
    /* ---------- Theme toggle button ---------- */

    document.querySelectorAll("[data-theme-toggle]").forEach((toggle) => {
      themeToggles.push(toggle);

      toggle.addEventListener("click", () => {
        const current = themeChoice();
        const next =
          current === "system" ? "light" : current === "light" ? "dark" : "system";
        setThemeChoice(next);
        applyTheme();
      });
    });
    applyTheme();

    /* ---------- Scroll reveal ---------- */

    const revealTargets = document.querySelectorAll("[data-reveal]");
    if (revealTargets.length > 0) {
      if (reduceMotion.matches || !("IntersectionObserver" in window)) {
        revealTargets.forEach((target) => target.classList.add("is-visible"));
      } else {
        const revealObserver = new IntersectionObserver(
          (entries, observer) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
              }
            });
          },
          { threshold: 0.15, rootMargin: "0px 0px -6% 0px" }
        );
        revealTargets.forEach((target) => revealObserver.observe(target));
      }
    }

    /* ---------- Benchmark chart: animate bars + count up ---------- */

    function countUp(element) {
      const target = Number(element.dataset.countTo || "0");
      const decimals = Number(element.dataset.decimals || "0");
      const format = (value) =>
        value.toLocaleString("en-US", {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        });

      if (reduceMotion.matches || target <= 0) {
        element.textContent = format(target);
        return;
      }

      const duration = 1100;
      const start = performance.now();
      const step = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = format(target * eased);
        if (progress < 1) {
          window.requestAnimationFrame(step);
        }
      };
      window.requestAnimationFrame(step);
    }

    document.querySelectorAll("[data-chart]").forEach((chart) => {
      const counters = chart.querySelectorAll("[data-count-to]");
      const activate = () => {
        chart.classList.add("in-view");
        counters.forEach(countUp);
      };

      if (reduceMotion.matches || !("IntersectionObserver" in window)) {
        activate();
        return;
      }

      const chartObserver = new IntersectionObserver(
        (entries, observer) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              activate();
              observer.disconnect();
            }
          });
        },
        { threshold: 0.35 }
      );
      chartObserver.observe(chart);
    });

    /* Stat counters outside the chart share the same count-up behavior. */

    const statCounters = document.querySelectorAll("[data-stat-count]");
    if (statCounters.length > 0) {
      if (reduceMotion.matches || !("IntersectionObserver" in window)) {
        statCounters.forEach(countUp);
      } else {
        const statObserver = new IntersectionObserver(
          (entries, observer) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                countUp(entry.target);
                observer.unobserve(entry.target);
              }
            });
          },
          { threshold: 0.5 }
        );
        statCounters.forEach((counter) => statObserver.observe(counter));
      }
    }

    /* ---------- Copy install command ---------- */

    function copyStatus(button) {
      const statusId = button.dataset.copyStatus;
      return statusId ? document.getElementById(statusId) : null;
    }

    async function copyToClipboard(text) {
      const clipboard = navigator.clipboard;
      if (!clipboard || typeof clipboard.writeText !== "function") {
        throw new Error("Clipboard access is unavailable");
      }
      await clipboard.writeText(text);
    }

    document.querySelectorAll("[data-copy-target]").forEach((button) => {
      const originalLabel = button.textContent;
      let activation = 0;
      let resetTimer;

      function clearResetTimer() {
        if (resetTimer !== undefined) {
          window.clearTimeout(resetTimer);
          resetTimer = undefined;
        }
      }

      function scheduleCopyReset(status, currentActivation) {
        clearResetTimer();
        resetTimer = window.setTimeout(() => {
          if (currentActivation !== activation) return;
          button.textContent = originalLabel;
          if (status) {
            status.textContent = "";
          }
          resetTimer = undefined;
        }, 1800);
      }

      button.addEventListener("click", async () => {
        const currentActivation = ++activation;
        clearResetTimer();
        const command = document.querySelector(button.dataset.copyTarget);
        if (!command) return;

        const status = copyStatus(button);
        let copyLabel = "Copied";
        let statusMessage = "Copied to your clipboard.";
        try {
          await copyToClipboard(command.textContent.trim());
        } catch {
          copyLabel = "Copy unavailable";
          statusMessage = "Clipboard access is unavailable. Select and copy the text manually.";
        }

        if (currentActivation !== activation) return;
        button.textContent = copyLabel;
        if (status) {
          status.textContent = statusMessage;
        }
        scheduleCopyReset(status, currentActivation);
      });
    });

    root.classList.add("js", "js-ready");
  });
})();
