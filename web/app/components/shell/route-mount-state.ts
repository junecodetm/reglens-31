// Session-scoped flag distinguishing the initial page load from client-side
// navigations. Every route records its mount (the Overview has no PageHeader,
// so it records directly); PageHeader focuses its h1 only when a route has
// already mounted before — the first load never steals focus.
let hasMountedARouteBefore = false;

export function recordRouteMount(): boolean {
  const wasMountedBefore = hasMountedARouteBefore;
  hasMountedARouteBefore = true;
  return wasMountedBefore;
}
