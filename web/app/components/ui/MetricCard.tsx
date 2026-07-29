import { ci, fmt, type MetricInterval } from "./metric-format";

export interface MetricCardInterval {
  label: string;
  interval: MetricInterval | null;
}

export interface MetricCardProps {
  label: string;
  value: number | null;
  intervals: MetricCardInterval[];
}

export function MetricCard({
  label,
  value,
  intervals,
}: MetricCardProps) {
  return (
    <div className="metric-card">
      <h3>{label}</h3>
      <p className="metric-value">{fmt(value)}</p>
      {intervals.map((item, index) => {
        const formattedInterval = ci(item.interval);

        return formattedInterval === null ? null : (
          <p
            className="metric-ci"
            key={`${item.label}:${index}`}
          >
            {item.label} {formattedInterval}
          </p>
        );
      })}
    </div>
  );
}
