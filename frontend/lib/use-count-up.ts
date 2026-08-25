"use client";

import { useEffect, useRef, useState } from "react";

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia(REDUCED_MOTION_QUERY).matches;
}

/**
 * Animate a number from 0 to `target` with an ease-out curve.
 * Returns the target immediately when the user prefers reduced motion.
 */
export function useCountUp(target: number | null, duration = 600): number {
  const [value, setValue] = useState<number>(0);
  const frameRef = useRef<number>(0);

  useEffect(() => {
    if (target === null || !Number.isFinite(target)) return;
    // Reduced motion: jump straight to the target on the next frame.
    const dur = prefersReducedMotion() ? 0 : duration;
    const start = performance.now();
    const from = 0;
    const tick = (now: number) => {
      const t = dur === 0 ? 1 : Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(from + (target - from) * eased);
      if (t < 1) frameRef.current = requestAnimationFrame(tick);
    };
    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [target, duration]);

  return target === null ? 0 : value;
}
