"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// The pre-multipage site addressed its collapsible groups with URL hashes.
// Mounted only on the Overview route: known legacy hashes forward to the
// route that now owns the content; unknown hashes are left untouched.
const LEGACY_HASH_ROUTES: Record<string, string> = {
  "#extraction": "/obligations",
  "#rejected-claims": "/obligations#rejected",
  "#explore": "/sources",
  "#ogc01": "/authorities",
  "#evaluation": "/evaluation",
};

export function LegacyHashRedirect() {
  const router = useRouter();

  useEffect(() => {
    const forward = () => {
      const target = LEGACY_HASH_ROUTES[window.location.hash];

      if (target) {
        router.replace(target);
      }
    };

    forward();
    // The retired single page also honored hash edits after load.
    window.addEventListener("hashchange", forward);

    return () => window.removeEventListener("hashchange", forward);
  }, [router]);

  return null;
}
