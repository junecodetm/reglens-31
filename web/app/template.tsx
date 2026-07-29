"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useRef, type ReactNode } from "react";

import { DUR, EASE } from "./motion/tokens";

gsap.registerPlugin(useGSAP);

export default function Template({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const media = gsap.matchMedia();

      media.add("(prefers-reduced-motion: no-preference)", () => {
        // opacity, NOT autoAlpha: autoAlpha toggles visibility:hidden, which
        // would make the PageHeader h1 unfocusable during the entrance tween.
        gsap.from(ref.current, {
          opacity: 0,
          y: 8,
          duration: DUR.base,
          ease: EASE,
          clearProps: "all",
        });
      });

      return () => media.revert();
    },
    { scope: ref },
  );

  return <div ref={ref}>{children}</div>;
}
