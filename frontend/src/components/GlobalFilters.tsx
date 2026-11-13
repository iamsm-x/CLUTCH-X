import { useQuery } from "@tanstack/react-query";

import { getFilterOptions } from "../api";
import { useAnalyticsFilters } from "../filters";
import { QueryState } from "./QueryState";

type Competition = "ALL" | "IPL" | "T20I";
type MatchStage = "ALL" | "LEAGUE" | "KNOCKOUTS_PLAYOFFS";

function isCompetition(value: string): value is Competition {
  return value === "ALL" || value === "IPL" || value === "T20I";
}

function isMatchStage(value: string): value is MatchStage {
  return (
    value === "ALL" ||
    value === "LEAGUE" ||
    value === "KNOCKOUTS_PLAYOFFS"
  );
}

export function GlobalFilters() {
  const { filters, setFilters } = useAnalyticsFilters();
  const options = useQuery({
    queryKey: ["filter-options"],
    queryFn: getFilterOptions,
  });

  return (
    <QueryState isLoading={options.isLoading} error={options.error}>
      {options.data ? (
        <section className="global-filters" aria-label="Analytics filters">
          <label>
            <span>COMPETITION</span>
            <select
              value={filters.competition}
              onChange={(event) => {
                const competition = event.currentTarget.value;
                if (isCompetition(competition)) {
                  setFilters((current) => ({ ...current, competition }));
                }
              }}
            >
              {options.data.competitions.map((competition) => (
                <option key={competition} value={competition}>
                  {competition}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>INNINGS</span>
            <select
              value={filters.innings ?? "BOTH"}
              onChange={(event) => {
                const value = event.currentTarget.value;
                const innings =
                  value === "1" ? 1 : value === "2" ? 2 : null;
                setFilters((current) => ({ ...current, innings }));
              }}
            >
              <option value="BOTH">BOTH</option>
              <option value={1}>1ST INNINGS</option>
              <option value={2}>2ND INNINGS</option>
            </select>
          </label>
          <label>
            <span>MATCH STAGE</span>
            <select
              value={filters.match_stage}
              onChange={(event) => {
                const matchStage = event.currentTarget.value;
                if (isMatchStage(matchStage)) {
                  setFilters((current) => ({
                    ...current,
                    match_stage: matchStage,
                  }));
                }
              }}
            >
              <option value="ALL">ALL STAGES</option>
              <option value="LEAGUE">LEAGUE</option>
              <option value="KNOCKOUTS_PLAYOFFS">KNOCKOUTS / PLAYOFFS</option>
            </select>
          </label>
          <label className="volume-filter">
            <span>
              MIN PRESSURE BALLS
              <strong>{filters.min_high_pressure_balls}</strong>
            </span>
            <input
              type="range"
              min={100}
              max={300}
              step={50}
              value={filters.min_high_pressure_balls}
              onChange={(event) => {
                const minHighPressureBalls = Number(
                  event.currentTarget.value,
                );
                setFilters((current) => ({
                  ...current,
                  min_high_pressure_balls: minHighPressureBalls,
                }));
              }}
            />
          </label>
        </section>
      ) : null}
    </QueryState>
  );
}
