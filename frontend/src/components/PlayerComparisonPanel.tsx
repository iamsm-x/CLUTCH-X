import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getPlayerComparison, getQuadrantScatter } from "../api";
import { useAnalyticsFilters } from "../filters";
import { QueryState } from "./QueryState";

export function PlayerComparisonPanel() {
  const [discipline, setDiscipline] = useState<"batting" | "bowling">(
    "batting",
  );
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const { filters } = useAnalyticsFilters();
  const scatter = useQuery({
    queryKey: ["quadrant-scatter", discipline, filters],
    queryFn: () => getQuadrantScatter(discipline, filters),
  });
  const options = scatter.data?.points ?? [];
  const optionIds = new Set(options.map((player) => player.player_id));
  const validSelectedIds = selectedIds
    .filter((playerId) => optionIds.has(playerId))
    .slice(0, 3);
  const comparisonIds = validSelectedIds.length
    ? validSelectedIds
    : options.slice(0, 3).map((player) => player.player_id);
  const comparison = useQuery({
    queryKey: ["player-comparison", discipline, comparisonIds, filters],
    queryFn: () => getPlayerComparison(discipline, comparisonIds, filters),
    enabled: comparisonIds.length > 0,
  });
  const auditRates =
    comparison.data?.players.flatMap((player) =>
      player.match_audit.map((match) => Math.abs(match.impact_rate ?? 0)),
    ) ?? [];
  const maxImpactRate = Math.max(1, ...auditRates);

  function updatePlayer(index: number, value: string) {
    const next = [...comparisonIds];
    if (value === "") {
      next.splice(index, 1);
    } else {
      next[index] = Number(value);
    }
    setSelectedIds([...new Set(next)].slice(0, 3));
  }

  return (
    <QueryState
      isLoading={scatter.isLoading || comparison.isLoading}
      error={scatter.error ?? comparison.error}
    >
      <section className="comparison-panel" aria-label="Player comparison">
        <div className="comparison-heading">
          <div>
            <div className="eyebrow">PLAYER-IN-PERIOD COMPARISON</div>
            <h2>Baseline vs. pressure execution</h2>
          </div>
          <div className="discipline-switch" aria-label="Comparison discipline">
            <button
              type="button"
              aria-pressed={discipline === "batting"}
              onClick={() => {
                setSelectedIds([]);
                setDiscipline("batting");
              }}
            >
              BATTING
            </button>
            <button
              type="button"
              aria-pressed={discipline === "bowling"}
              onClick={() => {
                setSelectedIds([]);
                setDiscipline("bowling");
              }}
            >
              BOWLING
            </button>
          </div>
        </div>
        <div className="comparison-selectors">
          {[0, 1, 2].map((index) => (
            <label key={index}>
              <span>PLAYER {index + 1}</span>
              <select
                aria-label={`Comparison player ${index + 1}`}
                value={comparisonIds[index] ?? ""}
                onChange={(event) =>
                  updatePlayer(index, event.currentTarget.value)
                }
              >
                <option value="">NOT SELECTED</option>
                {options.map((player) => (
                  <option
                    key={player.player_id}
                    value={player.player_id}
                    disabled={
                      comparisonIds.includes(player.player_id) &&
                      comparisonIds[index] !== player.player_id
                    }
                  >
                    {player.rank ? `#${player.rank} ` : ""}
                    {player.player_name}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
        {comparison.data ? (
          <div className="comparison-cards">
            {comparison.data.players.map((player) => (
              <article
                className="comparison-card"
                key={player.player_id}
              >
                <div className="comparison-player-title">
                  <span>{player.rank ? `RANK ${player.rank}` : "ELIGIBLE"}</span>
                  <h3>{player.player_name}</h3>
                </div>
                <div className="comparison-rating-row">
                  <span>
                    BASELINE
                    <strong>{player.baseline_rating.toFixed(1)}</strong>
                  </span>
                  <span>
                    PRESSURE
                    <strong>{player.pressure_rating.toFixed(1)}</strong>
                  </span>
                  <span>
                    NET DELTA
                    <strong
                      className={
                        player.net_clutch_delta >= 0
                          ? "delta-positive"
                          : "delta-negative"
                      }
                    >
                      {player.net_clutch_delta > 0 ? "+" : ""}
                      {player.net_clutch_delta.toFixed(1)}
                    </strong>
                  </span>
                </div>
                <div className="primary-metric">
                  <span>
                    {player.primary_metric_name.replaceAll("_", " ")} / HP
                    VOLUME
                  </span>
                  <strong>
                    {player.normal_primary_metric.toFixed(1)} →{" "}
                    {player.pressure_primary_metric.toFixed(1)}
                  </strong>
                  <small>
                    {player.high_pressure_volume} balls ·{" "}
                    {player.high_pressure_matches} matches
                  </small>
                </div>
                <div className="match-audit">
                  <h4>MATCH-BY-MATCH IMPACT</h4>
                  {player.match_audit.map((match) => {
                    const rate = match.impact_rate ?? 0;
                    return (
                      <div
                        className="match-impact-row"
                        key={`${player.player_id}-${match.match_id}`}
                        title={`${match.match_date} · ${match.high_pressure_volume} balls`}
                      >
                        <time>{match.match_date}</time>
                        <span className="impact-track">
                          <span
                            className={
                              rate >= 0 ? "impact-positive" : "impact-negative"
                            }
                            style={{
                              width: `${Math.max(3, (Math.abs(rate) / maxImpactRate) * 100)}%`,
                            }}
                          />
                        </span>
                        <strong className={rate >= 0 ? "delta-positive" : "delta-negative"}>
                          {match.impact_rate === null
                            ? "—"
                            : `${rate > 0 ? "+" : ""}${rate.toFixed(1)}`}
                        </strong>
                      </div>
                    );
                  })}
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </QueryState>
  );
}
