export type MetricInterval = [number, number];

export function fmt(value: number | null): string {
  return value === null ? "—" : value.toFixed(3);
}

export function ci(
  interval: MetricInterval | null,
): string | null {
  return interval === null
    ? null
    : `[${fmt(interval[0])}, ${fmt(interval[1])}]`;
}
