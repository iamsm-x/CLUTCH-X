import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  getLeaderboard,
  getPlayerComparison,
  type AnalyticsFilterState,
  type BattingLeaderboardEntry,
  type BowlingLeaderboardEntry,
} from "../api";
import { useAnalyticsFilters } from "../filters";
import { QueryState } from "./QueryState";

type Discipline = "batting" | "bowling";

function percentage(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}`;
}

function Delta({ value }: { value: number }) {
  return (
    <span className={value >= 0 ? "delta-positive" : "delta-negative"}>
      {signed(value)}
    </span>
  );
}

function MatchAuditDetails({
  discipline,
  playerId,
  filters,
}: {
  discipline: Discipline;
  playerId: number;
  filters: AnalyticsFilterState;
}) {
  const audit = useQuery({
    queryKey: ["leaderboard-match-audit", discipline, playerId, filters],
    queryFn: () => getPlayerComparison(discipline, [playerId], filters),
  });

  return (
    <QueryState isLoading={audit.isLoading} error={audit.error}>
      {audit.data ? (
        <div className="leaderboard-audit">
          <strong>MATCH-BY-MATCH IMPACT</strong>
          {audit.data.players[0].match_audit.length ? (
            <div className="leaderboard-audit-table">
              <div className="leaderboard-audit-head">
                <span>MATCH DATE</span>
                <span>HP BALLS</span>
                <span>IMPACT</span>
                <span>IMPACT RATE</span>
              </div>
              {audit.data.players[0].match_audit.map((match) => (
                <div className="leaderboard-audit-row" key={match.match_id}>
                  <time>{match.match_date}</time>
                  <span>{match.high_pressure_volume}</span>
                  <Delta value={match.impact} />
                  <span>
                    {match.impact_rate === null ? "—" : signed(match.impact_rate)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p>No high-pressure match audit rows for this player in the selected period.</p>
          )}
        </div>
      ) : null}
    </QueryState>
  );
}

function RankOneSpotlight({
  entry,
}: {
  entry: BattingLeaderboardEntry | BowlingLeaderboardEntry;
}) {
  return (
    <section className="rank-one-spotlight" aria-label="Rank one spotlight">
      <div>
        <span className="eyebrow">RANK 01 / CLUTCH-X LEADER</span>
        <h3>{entry.player_name}</h3>
        <p>
          Baseline {entry.baseline_rating.toFixed(1)} · pressure{" "}
          {entry.pressure_rating.toFixed(1)} · net delta{" "}
          <Delta value={entry.net_clutch_delta} />
        </p>
      </div>
      <div className="spotlight-score">
        <span>CLUTCH-X SCORE</span>
        <strong>{entry.clutch_x_score.toFixed(1)}</strong>
      </div>
      {"normal_strike_rate" in entry ? (
        <div className="spotlight-telemetry">
          <span>
            STRIKE RATE
            <strong>
              {entry.normal_strike_rate.toFixed(1)} →{" "}
              {entry.high_pressure_strike_rate.toFixed(1)}
            </strong>
          </span>
          <span>
            PRESSURE BALLS
            <strong>{entry.high_pressure_balls_faced}</strong>
          </span>
          <span>
            POSITIVE IMPACT
            <strong>{percentage(entry.positive_impact_rate)}</strong>
          </span>
        </div>
      ) : (
        <div className="spotlight-telemetry">
          <span>
            ECONOMY
            <strong>
              {entry.normal_economy.toFixed(2)} →{" "}
              {entry.high_pressure_economy.toFixed(2)}
            </strong>
          </span>
          <span>
            HP WICKETS
            <strong>{entry.high_pressure_wickets}</strong>
          </span>
          <span>
            POSITIVE IMPACT
            <strong>{percentage(entry.positive_impact_rate)}</strong>
          </span>
        </div>
      )}
    </section>
  );
}

export function LeaderboardPanel() {
  const [discipline, setDiscipline] = useState<Discipline>("batting");
  const [expandedPlayerId, setExpandedPlayerId] = useState<number | null>(null);
  const { filters } = useAnalyticsFilters();
  const leaderboard = useQuery({
    queryKey: ["leaderboard", discipline, filters],
    queryFn: () => getLeaderboard(discipline, filters),
  });

  return (
    <QueryState
      isLoading={leaderboard.isLoading}
      error={leaderboard.error}
    >
      {leaderboard.data ? (
        <section className="leaderboard-panel" aria-label="Top 10 rankings">
          <div className="leaderboard-heading">
            <div>
              <div className="eyebrow">PRESSURE-ADJUSTED TOP 10</div>
              <h2>{discipline} leaderboard</h2>
            </div>
            <div className="discipline-switch" aria-label="Leaderboard discipline">
              <button
                type="button"
                aria-pressed={discipline === "batting"}
                onClick={() => {
                  setExpandedPlayerId(null);
                  setDiscipline("batting");
                }}
              >
                BATTING
              </button>
              <button
                type="button"
                aria-pressed={discipline === "bowling"}
                onClick={() => {
                  setExpandedPlayerId(null);
                  setDiscipline("bowling");
                }}
              >
                BOWLING
              </button>
            </div>
          </div>
          <RankOneSpotlight
            entry={leaderboard.data.entries[0]}
          />
          <div className="leaderboard-table-scroll">
            {leaderboard.data.discipline === "batting" ? (
              <table className="leaderboard-table">
                <caption>Batting Top 10. Select a row to inspect match audit data.</caption>
                <thead>
                  <tr>
                    <th scope="col">RANK</th>
                    <th scope="col">PLAYER</th>
                    <th scope="col">HP BALLS / MATCHES</th>
                    <th scope="col">STRIKE RATE BASE → HP</th>
                    <th scope="col">SR DELTA</th>
                    <th scope="col">PRAE / 100</th>
                    <th scope="col">POSITIVE IMPACT</th>
                    <th scope="col">BASE → PRESSURE</th>
                    <th scope="col">NET DELTA</th>
                    <th scope="col">CLUTCH-X</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.data.entries.map((entry) => (
                    <BattingRow
                      key={entry.player_id}
                      entry={entry}
                      expanded={expandedPlayerId === entry.player_id}
                      onToggle={() =>
                        setExpandedPlayerId((current) =>
                          current === entry.player_id ? null : entry.player_id,
                        )
                      }
                      filters={filters}
                    />
                  ))}
                </tbody>
              </table>
            ) : (
              <table className="leaderboard-table">
                <caption>Bowling Top 10. Select a row to inspect match audit data.</caption>
                <thead>
                  <tr>
                    <th scope="col">RANK</th>
                    <th scope="col">PLAYER</th>
                    <th scope="col">HP LEGAL BALLS / MATCHES</th>
                    <th scope="col">ECONOMY BASE → HP</th>
                    <th scope="col">ECONOMY DELTA</th>
                    <th scope="col">PRSAE / OVER</th>
                    <th scope="col">HP DOTS / WICKETS</th>
                    <th scope="col">POSITIVE IMPACT</th>
                    <th scope="col">BASE → PRESSURE</th>
                    <th scope="col">NET DELTA</th>
                    <th scope="col">CLUTCH-X</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.data.entries.map((entry) => (
                    <BowlingRow
                      key={entry.player_id}
                      entry={entry}
                      expanded={expandedPlayerId === entry.player_id}
                      onToggle={() =>
                        setExpandedPlayerId((current) =>
                          current === entry.player_id ? null : entry.player_id,
                        )
                      }
                      filters={filters}
                    />
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      ) : null}
    </QueryState>
  );
}

function BattingRow({
  entry,
  expanded,
  onToggle,
  filters,
}: {
  entry: BattingLeaderboardEntry;
  expanded: boolean;
  onToggle: () => void;
  filters: AnalyticsFilterState;
}) {
  return (
    <>
      <tr className={expanded ? "is-expanded" : ""}>
        <td className="rank-cell">{String(entry.rank).padStart(2, "0")}</td>
        <th scope="row">
          <button
            className="player-audit-toggle"
            type="button"
            aria-expanded={expanded}
            onClick={onToggle}
          >
            {entry.player_name}
          </button>
        </th>
        <td>{entry.high_pressure_balls_faced} / {entry.high_pressure_matches}</td>
        <td>{entry.normal_strike_rate.toFixed(1)} → {entry.high_pressure_strike_rate.toFixed(1)}</td>
        <td><Delta value={entry.strike_rate_delta} /></td>
        <td><Delta value={entry.prae_per_100} /></td>
        <td>{percentage(entry.positive_impact_rate)}</td>
        <td>{entry.baseline_rating.toFixed(1)} → {entry.pressure_rating.toFixed(1)}</td>
        <td><Delta value={entry.net_clutch_delta} /></td>
        <td className="score-cell">{entry.clutch_x_score.toFixed(1)}</td>
      </tr>
      {expanded ? (
        <tr className="audit-detail-row">
          <td colSpan={10}>
            <MatchAuditDetails discipline="batting" playerId={entry.player_id} filters={filters} />
          </td>
        </tr>
      ) : null}
    </>
  );
}

function BowlingRow({
  entry,
  expanded,
  onToggle,
  filters,
}: {
  entry: BowlingLeaderboardEntry;
  expanded: boolean;
  onToggle: () => void;
  filters: AnalyticsFilterState;
}) {
  return (
    <>
      <tr className={expanded ? "is-expanded" : ""}>
        <td className="rank-cell">{String(entry.rank).padStart(2, "0")}</td>
        <th scope="row">
          <button
            className="player-audit-toggle"
            type="button"
            aria-expanded={expanded}
            onClick={onToggle}
          >
            {entry.player_name}
          </button>
        </th>
        <td>{entry.high_pressure_legal_balls} / {entry.high_pressure_matches}</td>
        <td>{entry.normal_economy.toFixed(2)} → {entry.high_pressure_economy.toFixed(2)}</td>
        <td><Delta value={entry.economy_delta} /></td>
        <td><Delta value={entry.prsae_per_over} /></td>
        <td>{percentage(entry.high_pressure_dot_rate)} / {entry.high_pressure_wickets}</td>
        <td>{percentage(entry.positive_impact_rate)}</td>
        <td>{entry.baseline_rating.toFixed(1)} → {entry.pressure_rating.toFixed(1)}</td>
        <td><Delta value={entry.net_clutch_delta} /></td>
        <td className="score-cell">{entry.clutch_x_score.toFixed(1)}</td>
      </tr>
      {expanded ? (
        <tr className="audit-detail-row">
          <td colSpan={11}>
            <MatchAuditDetails discipline="bowling" playerId={entry.player_id} filters={filters} />
          </td>
        </tr>
      ) : null}
    </>
  );
}
