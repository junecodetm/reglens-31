import { useEffect, useRef, type RefObject } from "react";
import gsap from "gsap";

import { EASE } from "./tokens.ts";

// Counts the displayed number up to the value React already rendered. The
// DOM is authored in final state: the tween only transiently overwrites
// textContent, and reduced-motion users never see it run.
export function useCountUp(
  ref: RefObject<HTMLElement | null>,
  value: number | null,
): void {
  const lastAnimatedValueRef = useRef<number | null>(null);

  useEffect(() => {
    const element = ref.current;

    if (
      value === null ||
      element === null ||
      lastAnimatedValueRef.current === value
    ) {
      return;
    }

    lastAnimatedValueRef.current = value;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    const proxy = { current: 0 };
    const tween = gsap.to(proxy, {
      current: value,
      duration: 0.6,
      ease: EASE,
      snap: { current: 1 },
      onUpdate: () => {
        element.textContent = String(Math.round(proxy.current));
      },
      onComplete: () => {
        element.textContent = String(value);
      },
    });

    return () => {
      tween.kill();
      element.textContent = String(value);
    };
  }, [ref, value]);
}
