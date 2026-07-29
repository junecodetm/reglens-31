import type { DiffOp } from "../reglens-types";

// Word-level comparison of a model quote against its closest source passage.
// <ins>/<del> semantics plus visually-hidden prefixes keep the distinction
// available to assistive tech; styling never relies on hue alone.
export function DiffComparison({ diff }: { diff: DiffOp[] }) {
  return (
    <>
      {diff.map(([kind, text], index) => {
        const key = `${kind}-${index}`;

        if (kind === "model") {
          return (
            <ins className="diff-model" key={key}>
              <span className="screen-reader-only">model wrote: </span>
              {text}{" "}
            </ins>
          );
        }

        if (kind === "source") {
          return (
            <del className="diff-source" key={key}>
              <span className="screen-reader-only">source reads: </span>
              {text}{" "}
            </del>
          );
        }

        return <span key={key}>{text} </span>;
      })}
    </>
  );
}
