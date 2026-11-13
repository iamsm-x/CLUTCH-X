export interface Overview {
  product_name: "CLUTCH-X";
  competitions: ("IPL" | "T20I")[];
  first_season: string;
  latest_season: string;
  delivery_count: number;
  match_count: number;
  eligible_batters: number;
  eligible_bowlers: number;
  high_pressure_cutoff: number;
  store_schema_version: string;
  split_half_stability_target: number;
  batting_split_half_rho: number;
  bowling_split_half_rho: number;
  rankings_meet_stability_target: boolean;
}

export interface FilterOptions {
  competitions: ("ALL" | "IPL" | "T20I")[];
  seasons: string[];
  match_stages: ("ALL" | "LEAGUE" | "KNOCKOUTS_PLAYOFFS")[];
  innings: (1 | 2)[];
  minimum_high_pressure_balls: number[];
}

export interface AnalyticsFilterState {
  competition: "ALL" | "IPL" | "T20I";
  innings: 1 | 2 | null;
  match_stage: "ALL" | "LEAGUE" | "KNOCKOUTS_PLAYOFFS";
  min_high_pressure_balls: number;
  over: number | null;
}

export interface TimelinePoint {
  over: number;
  average_pressure_index: number;
  high_pressure_deliveries: number;
  wickets: number;
}

export interface ScatterPoint {
  player_id: number;
  player_name: string;
  baseline_rating: number;
  pressure_rating: number;
  net_clutch_delta: number;
  rank: number | null;
}

export interface QuadrantScatter {
  discipline: "batting" | "bowling";
  baseline_median: number;
  pressure_median: number;
  points: ScatterPoint[];
}

export interface MatchAuditRecord {
  match_id: number;
  match_date: string;
  high_pressure_volume: number;
  impact: number;
  impact_rate: number | null;
  is_positive_impact: boolean;
}

export interface ComparisonPlayer {
  player_id: number;
  player_name: string;
  rank: number | null;
  baseline_rating: number;
  pressure_rating: number;
  net_clutch_delta: number;
  high_pressure_volume: number;
  high_pressure_matches: number;
  primary_metric_name: string;
  normal_primary_metric: number;
  pressure_primary_metric: number;
  primary_metric_delta: number;
  match_audit: MatchAuditRecord[];
}

export interface PlayerComparison {
  discipline: "batting" | "bowling";
  players: ComparisonPlayer[];
}

export interface BattingLeaderboardEntry {
  rank: number;
  player_id: number;
  player_name: string;
  high_pressure_balls_faced: number;
  high_pressure_matches: number;
  normal_strike_rate: number;
  high_pressure_strike_rate: number;
  strike_rate_delta: number;
  prae_per_100: number;
  positive_impact_rate: number;
  baseline_rating: number;
  pressure_rating: number;
  net_clutch_delta: number;
  clutch_x_score: number;
}

export interface BowlingLeaderboardEntry {
  rank: number;
  player_id: number;
  player_name: string;
  high_pressure_legal_balls: number;
  high_pressure_matches: number;
  normal_economy: number;
  high_pressure_economy: number;
  economy_delta: number;
  prsae_per_over: number;
  high_pressure_dot_rate: number;
  high_pressure_wickets: number;
  positive_impact_rate: number;
  baseline_rating: number;
  pressure_rating: number;
  net_clutch_delta: number;
  clutch_x_score: number;
}

export type Leaderboard =
  | {
      discipline: "batting";
      entries: BattingLeaderboardEntry[];
      filters: AnalyticsFilterState;
    }
  | {
      discipline: "bowling";
      entries: BowlingLeaderboardEntry[];
      filters: AnalyticsFilterState;
    };

export function getLeaderboard(
  discipline: "batting" | "bowling",
  filters: AnalyticsFilterState,
) {
  return getJson<Leaderboard>(
    `/leaderboards/${discipline}?${serializeAnalyticsFilters(filters)}`,
  );
}

export function serializeAnalyticsFilters(
  filters: AnalyticsFilterState,
): string {
  const params = new URLSearchParams({
    competition: filters.competition,
    match_stage: filters.match_stage,
    min_high_pressure_balls: String(filters.min_high_pressure_balls),
  });
  if (filters.innings !== null) {
    params.set("innings", String(filters.innings));
  }
  if (filters.over !== null) {
    params.set("over", String(filters.over));
  }
  return params.toString();
}

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "/api/v1"
).replace(/\/$/, "");

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const body = (await response.json()) as { detail?: string };
      throw new Error(body.detail ?? `API request failed (${response.status})`);
    }
    throw new Error(
      `API request failed (${response.status}). Check that VITE_API_BASE_URL points to the FastAPI /api/v1 endpoint.`,
    );
  }
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    throw new Error(
      "The configured analytics URL returned HTML instead of JSON. Check VITE_API_BASE_URL and the backend deployment URL.",
    );
  }
  return (await response.json()) as T;
}

export const getOverview = () => getJson<Overview>("/overview");
export const getFilterOptions = () => getJson<FilterOptions>("/filters");

export function getPressureTimeline(
  innings: 1 | 2,
  filters: AnalyticsFilterState,
) {
  const timelineFilters = { ...filters, innings, over: null };
  return getJson<{ innings: 1 | 2; overs: TimelinePoint[] }>(
    `/timeline/${innings}?${serializeAnalyticsFilters(timelineFilters)}`,
  );
}

export function getQuadrantScatter(
  discipline: "batting" | "bowling",
  filters: AnalyticsFilterState,
) {
  return getJson<QuadrantScatter>(
    `/scatter/${discipline}?${serializeAnalyticsFilters(filters)}`,
  );
}

export function getPlayerComparison(
  discipline: "batting" | "bowling",
  playerIds: number[],
  filters: AnalyticsFilterState,
) {
  const params = new URLSearchParams(serializeAnalyticsFilters(filters));
  params.set("discipline", discipline);
  for (const playerId of playerIds) {
    params.append("player_ids", String(playerId));
  }
  return getJson<PlayerComparison>(`/players/compare?${params.toString()}`);
}
