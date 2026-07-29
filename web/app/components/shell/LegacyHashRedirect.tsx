"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// The pre-multipage site addressed its collapsible groups with URL hashes.
// Mounted only on the Overview route: known legacy hashes forward to the
// route that now owns the content; unknown hashes are left untouched.
const LEGACY_HASH_ROUTES: Record<string, string> = {
  "#about": "/about",
  "#extraction": "/extraction/claims",
  "#rejected-claims": "/extraction/rejected",
  "#explore": "/explore/search",
  "#ogc01": "/ogc01/authority",
  "#evaluation": "/evaluation",
};

export function LegacyHashRedirect() {
  const router = useRouter();

  useEffect(() => {
    const target = LEGACY_HASH_ROUTES[window.location.hash];

    if (target) {
      router.replace(target);
    }
  }, [router]);

  return null;
}
