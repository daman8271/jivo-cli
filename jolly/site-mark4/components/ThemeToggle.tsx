"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "jivo-mark4-theme";

export default function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.dataset.theme === "dark");
    const preference = window.matchMedia("(prefers-color-scheme: dark)");
    const followDevice = () => {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved === "light" || saved === "dark") return;
      } catch {
        // The switch still works when browser storage is unavailable.
      }
      document.documentElement.dataset.theme = preference.matches ? "dark" : "light";
      setDark(preference.matches);
    };
    preference.addEventListener("change", followDevice);
    return () => preference.removeEventListener("change", followDevice);
  }, []);

  function toggle() {
    const next = document.documentElement.dataset.theme !== "dark";
    document.documentElement.dataset.theme = next ? "dark" : "light";
    setDark(next);
    try {
      localStorage.setItem(STORAGE_KEY, next ? "dark" : "light");
    } catch {
      // Keep the selected theme for this visit even without storage.
    }
  }

  return (
    <button
      type="button"
      className="subtle-button theme-toggle"
      aria-label="Dark mode"
      aria-pressed={dark}
      onClick={toggle}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true" className="theme-moon">
        <path d="M20.6 13A8.7 8.7 0 0 1 11 3.4 8.7 8.7 0 1 0 20.6 13Z" />
      </svg>
      <svg viewBox="0 0 24 24" aria-hidden="true" className="theme-sun">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" />
      </svg>
      <span className="theme-moon">Dark mode</span>
      <span className="theme-sun">Light mode</span>
    </button>
  );
}
