"use client";

import { useCallback, useSyncExternalStore } from "react";

const listeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/**
 * Read/write a localStorage-backed value as an external store.
 * Server snapshot is always null; the client hydrates from storage after mount.
 */
export function useLocalValue(key: string): readonly [string | null, (value: string | null) => void] {
  const value = useSyncExternalStore(
    subscribe,
    () => window.localStorage.getItem(key),
    () => null,
  );

  const setValue = useCallback(
    (next: string | null) => {
      if (next === null) window.localStorage.removeItem(key);
      else window.localStorage.setItem(key, next);
      listeners.forEach((l) => l());
    },
    [key],
  );

  return [value, setValue] as const;
}
