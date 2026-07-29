import gsap from "gsap";

import { DUR, EASE } from "./tokens.ts";

// Brief background pulse drawing the eye to a just-located highlight span.
// Self-guards reduced motion; the element's authored styles are the final
// state (clearProps removes the inline value when the tween ends).
export function pulseHighlight(element: HTMLElement): void {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  const computed = getComputedStyle(element);
  const finalBackground = computed.backgroundColor;
  // GSAP can't parse var() as a color — resolve the custom property first
  // (custom properties inherit, so the element's computed style has it).
  const softBlue = computed.getPropertyValue("--soft-blue").trim();

  if (!softBlue) {
    return;
  }

  gsap.fromTo(
    element,
    { backgroundColor: softBlue },
    {
      backgroundColor: finalBackground,
      duration: DUR.slow,
      ease: EASE,
      delay: 0.1,
      clearProps: "backgroundColor",
    },
  );
}
