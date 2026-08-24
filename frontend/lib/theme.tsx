"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Theme = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  toggle: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeState | null>(null);

const STORAGE_KEY = "sms_theme";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolve(theme: Theme): ResolvedTheme {
  if (theme === "system") return systemPrefersDark() ? "dark" : "light";
  return theme;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() => resolve(getInitialTheme()));

  useEffect(() => {
    const root = document.documentElement;
    const apply = () => {
      const next = resolve(theme);
      setResolvedTheme(next);
      root.classList.toggle("dark", next === "dark");
      root.style.colorScheme = next;
    };
    apply();
    window.localStorage.setItem(STORAGE_KEY, theme);

    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => setThemeState(next), []);
  const toggle = useCallback(
    () =>
      setThemeState((t) => {
        // Cycle light → dark → system → light so every state is reachable.
        if (t === "light") return "dark";
        if (t === "dark") return "system";
        return "light";
      }),
    [],
  );

  const value = useMemo(() => ({ theme, resolvedTheme, toggle, setTheme }), [theme, resolvedTheme, toggle, setTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

export function ThemeInitScript() {
  return (
    <script
      dangerouslySetInnerHTML={{
        __html: `(function(){try{var s=localStorage.getItem("${STORAGE_KEY}")||"system";var d=s==="dark"||(s==="system"&&matchMedia("(prefers-color-scheme: dark)").matches);if(d){document.documentElement.classList.add("dark");document.documentElement.style.colorScheme="dark"}else{document.documentElement.classList.remove("dark");document.documentElement.style.colorScheme="light"}}catch(e){}})();`,
      }}
    />
  );
}
