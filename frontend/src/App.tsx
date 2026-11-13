import { lazy, Suspense } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import { useQuery } from "@tanstack/react-query";

import { getFilterOptions, getOverview } from "./api";
import { QueryState } from "./components/QueryState";
import { GlobalFilters } from "./components/GlobalFilters";
import { PressureTimeline } from "./components/PressureTimeline";
import { PlayerComparisonPanel } from "./components/PlayerComparisonPanel";
import { LeaderboardPanel } from "./components/LeaderboardPanel";
import { AnalyticsFiltersProvider } from "./filters";

const numberFormat = new Intl.NumberFormat("en-IN");
const QuadrantChart = lazy(() =>
  import("./components/QuadrantChart").then((module) => ({
    default: module.QuadrantChart,
  })),
);

function OverviewPanel() {
  const overview = useQuery({
    queryKey: ["overview"],
    queryFn: getOverview,
  });
  const filters = useQuery({
    queryKey: ["filter-options"],
    queryFn: getFilterOptions,
  });

  return (
    <QueryState
      isLoading={overview.isLoading || filters.isLoading}
      error={overview.error ?? filters.error}
    >
      {overview.data && filters.data ? (
        <>
          <section className="hero-panel">
            <div className="eyebrow">T20 CONTEXTUAL LEVERAGE ENGINE</div>
            <h1>Quantify execution when the game is on the line.</h1>
            <p>
              A delivery-level pressure engine and contextual player rankings
              for IPL and T20 internationals.
            </p>
            <div className="scope-line">
              {overview.data.competitions.join(" + ")} ·{" "}
              {overview.data.first_season}–{overview.data.latest_season} ·
              PRESSURE CUTOFF {overview.data.high_pressure_cutoff}
            </div>
          </section>
          <section className="validation-strip" aria-label="Model validation">
            <div>
              <span>PRESSURE INDEX</span>
              <strong>ACCEPTANCE PASSED</strong>
            </div>
            <div>
              <span>RANKING STABILITY</span>
              <strong
                className={
                  overview.data.rankings_meet_stability_target
                    ? "status-pass"
                    : "status-warning"
                }
              >
                {overview.data.rankings_meet_stability_target
                  ? "TARGET MET"
                  : "BELOW TARGET"}
              </strong>
            </div>
            <div className="stability-detail">
              Split-half Spearman · batting{" "}
              {overview.data.batting_split_half_rho.toFixed(2)} · bowling{" "}
              {overview.data.bowling_split_half_rho.toFixed(2)} · target{" "}
              {overview.data.split_half_stability_target.toFixed(2)}
            </div>
          </section>
          <section className="metric-grid" aria-label="Dataset coverage">
            <article className="metric-card">
              <span>DELIVERIES</span>
              <strong>{numberFormat.format(overview.data.delivery_count)}</strong>
            </article>
            <article className="metric-card">
              <span>MATCHES</span>
              <strong>{numberFormat.format(overview.data.match_count)}</strong>
            </article>
            <article className="metric-card">
              <span>ELIGIBLE BATTERS</span>
              <strong>{overview.data.eligible_batters}</strong>
            </article>
            <article className="metric-card">
              <span>ELIGIBLE BOWLERS</span>
              <strong>{overview.data.eligible_bowlers}</strong>
            </article>
          </section>
          <p className="quiet-note">
            {filters.data.seasons.length} seasons indexed · minimum pressure
            volume filters from{" "}
            {filters.data.minimum_high_pressure_balls[0]} to{" "}
            {filters.data.minimum_high_pressure_balls.at(-1)} balls
          </p>
          <section className="engine-pillars" aria-label="Analytics methodology">
            <article>
              <span>01 / PRESSURE ENGINE</span>
              <h2>Dynamic match leverage</h2>
              <p>
                Chase tension, wicket scarcity, collapse recovery, and
                end-of-innings urgency score each delivery from 0 to 100.
              </p>
            </article>
            <article>
              <span>02 / CONTEXT NORMALIZATION</span>
              <h2>Format and season aware</h2>
              <p>
                Expected performance adjusts for innings, phase, competition,
                and season before player impact is measured.
              </p>
            </article>
            <article>
              <span>03 / RELIABILITY GUARDRAILS</span>
              <h2>Sample and consistency</h2>
              <p>
                Minimum pressure volume, multi-match exposure, peer shrinkage,
                and volatility penalties limit small-sample outliers.
              </p>
            </article>
          </section>
        </>
      ) : null}
    </QueryState>
  );
}

function PlaceholderPanel({ title, detail }: { title: string; detail: string }) {
  return (
    <section className="placeholder-panel">
      <div className="eyebrow">ANALYTICS WORKSPACE</div>
      <h2>{title}</h2>
      <p>{detail}</p>
    </section>
  );
}

export default function App() {
  return (
    <main className="app-shell">
      <AnalyticsFiltersProvider>
        <Tabs.Root className="view-tabs" defaultValue="overview">
          <header className="command-header">
            <a className="brand" href="/" aria-label="CLUTCH-X overview">
              <span className="brand-mark">C</span>
              <span>CLUTCH-X</span>
            </a>
            <Tabs.List aria-label="Main views">
              <Tabs.Trigger value="overview">OVERVIEW</Tabs.Trigger>
              <Tabs.Trigger value="analytics">TACTICAL ANALYTICS</Tabs.Trigger>
              <Tabs.Trigger value="rankings">TOP 10 RANKINGS</Tabs.Trigger>
            </Tabs.List>
            <div className="dataset-tag">IPL + T20I</div>
          </header>
          <Tabs.Content value="overview">
            <OverviewPanel />
          </Tabs.Content>
          <Tabs.Content value="analytics">
            <GlobalFilters />
            <PressureTimeline />
            <Suspense
              fallback={
                <div className="query-state" role="status">
                  Loading quadrant chart…
                </div>
              }
            >
              <QuadrantChart />
            </Suspense>
            <PlayerComparisonPanel />
            <PlaceholderPanel
              title="Tactical command center"
              detail="Pressure timelines, baseline quadrants, and player comparisons."
            />
          </Tabs.Content>
          <Tabs.Content value="rankings">
            <GlobalFilters />
            <LeaderboardPanel />
          </Tabs.Content>
        </Tabs.Root>
      </AnalyticsFiltersProvider>
    </main>
  );
}
