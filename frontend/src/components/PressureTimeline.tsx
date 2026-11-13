import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getPressureTimeline } from "../api";
import { useAnalyticsFilters } from "../filters";
import { QueryState } from "./QueryState";

export function PressureTimeline() {
  const { filters, setFilters } = useAnalyticsFilters();
  const [unfilteredInnings, setUnfilteredInnings] = useState<1 | 2>(1);
  const innings = filters.innings ?? unfilteredInnings;
  const timeline = useQuery({
    queryKey: [
      "pressure-timeline",
      filters.competition,
      filters.match_stage,
      innings,
    ],
    queryFn: () => getPressureTimeline(innings, filters),
  });
  const points = new Map(
    (timeline.data?.overs ?? []).map((point) => [point.over, point]),
  );

  return (
    <QueryState isLoading={timeline.isLoading} error={timeline.error}>
      <section className="timeline-panel" aria-label="Innings pressure timeline">
        <div className="timeline-heading">
          <div>
            <div className="eyebrow">OPENFIELD-STYLE INNINGS INTENSITY</div>
            <h2>Pressure by over</h2>
          </div>
          {filters.innings === null ? (
            <div className="innings-switch" aria-label="Timeline innings">
              <button
                type="button"
                aria-pressed={innings === 1}
                onClick={() => setUnfilteredInnings(1)}
              >
                1ST INNINGS
              </button>
              <button
                type="button"
                aria-pressed={innings === 2}
                onClick={() => setUnfilteredInnings(2)}
              >
                2ND INNINGS
              </button>
            </div>
          ) : null}
        </div>
        <div className="timeline-track">
          {Array.from({ length: 20 }, (_, index) => {
            const over = index + 1;
            const point = points.get(over);
            const pressure = point?.average_pressure_index ?? 0;
            const intensity =
              pressure >= 60 ? "high" : pressure >= 45 ? "medium" : "low";
            const selected = filters.over === over;
            return (
              <button
                key={over}
                type="button"
                className={`over-tile intensity-${intensity}${selected ? " is-selected" : ""}`}
                aria-label={`Over ${over}, average pressure ${pressure.toFixed(1)}, ${point?.wickets ?? 0} wickets across the filtered dataset`}
                aria-pressed={selected}
                title={`Over ${over} · PI ${pressure.toFixed(1)} · ${point?.wickets ?? 0} wickets · ${point?.high_pressure_deliveries ?? 0} high-pressure balls`}
                onClick={() =>
                  setFilters((current) => ({
                    ...current,
                    over: selected ? null : over,
                  }))
                }
              >
                <span className="wicket-marker">
                  {point && point.wickets > 0 ? <i aria-hidden="true" /> : null}
                </span>
                <span className="over-bar-track">
                  <span
                    className="over-bar"
                    style={{ height: `${Math.max(4, pressure)}%` }}
                  />
                </span>
                <span className="over-number">{String(over).padStart(2, "0")}</span>
              </button>
            );
          })}
        </div>
        <div className="timeline-legend">
          <span>
            <i className="legend-low" /> ROUTINE
          </span>
          <span>
            <i className="legend-medium" /> BUILDING
          </span>
          <span>
            <i className="legend-high" /> HIGH PRESSURE
          </span>
          <span>W = WICKET</span>
          <span>{filters.over ? `OVER ${filters.over} SELECTED` : "SELECT AN OVER"}</span>
        </div>
      </section>
    </QueryState>
  );
}
