import { ci, fmt, type MetricInterval } from "./metric-format";

export interface MetricCardInterval {
  label: string;
  interval: MetricInterval | null;
}

export interface MetricCardProps {
  label: string;
  value: number | null;
  intervals: MetricCardInterval[];
  headingLevel?: "h2" | "h3" | "h4";
}

export function MetricCard({
  label,
  value,
  intervals,
  headingLevel = "h3",
}: MetricCardProps) {
  const Heading = headingLevel;

  return (
    <div className="metric-card">
      <Heading>{label}</Heading>
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
