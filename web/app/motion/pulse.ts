import gsap from "gsap";

import { DUR, EASE } from "./tokens.ts";

// Brief background pulse drawing the eye to a just-located highlight span.
// Self-guards reduced motion; the element's authored styles are the final
// state (clearProps removes the inline value when the tween ends).
export function pulseHighlight(element: HTMLElement): void {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  const finalBackground = getComputedStyle(element).backgroundColor;

  gsap.fromTo(
    element,
    { backgroundColor: "var(--soft-blue)" },
    {
      backgroundColor: finalBackground,
      duration: DUR.slow,
      ease: EASE,
      delay: 0.1,
      clearProps: "backgroundColor",
    },
  );
}
