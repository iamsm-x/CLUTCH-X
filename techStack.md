# Technical Architecture & 2026 Tech Stack: CLUTCH-X

**Contextual Leverage & Under-Pressure T20 Execution Engine**  
**Document Type:** System Architecture & Technology Stack Specification  
**Version:** 1.0 (2026 Reference Standard)  
**Aligned Specifications:** `PRD` (v1.0) & `design.md` (Catapult Sports Telemetry Aesthetic)

---

## 1. Executive Architecture Overview

**CLUTCH-X** is engineered as a **deterministic, zero-latency sports analytics platform** that transforms raw T20 ball-by-ball CSV logs (`ball_by_ball.csv`, `matches.csv`, `competitions.csv`, `playing_eleven.csv`, `teams.csv`, and `competition_team_player_mapping.csv`) into interactive franchise telemetry and a reproducible PDF methodology whitepaper.

Because the underlying dataset consists of historical IPL and T20I match records (2022–present) rather than high-frequency streaming IoT sensors, the architecture avoids bloated distributed databases in favor of **in-process columnar analytics (Polars + DuckDB)** paired with a **hardware-accelerated React 19 telemetry frontend**.

### End-to-End Data & Application Flow

```text
[Raw CSV Datasets (7 Relational Files)]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  1. DETERMINISTIC ETL & PRESSURE ENGINE (Python 3.13)  │
│     • Polars: Pre-delivery state reconstruction        │
│     • NumPy/SciPy: Pressure Index (PI) & Shrinkage     │
│     • Output: Pre-compiled Parquet + DuckDB Artifacts  │
└─────────────────────────┬──────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
┌───────────────────────┐   ┌────────────────────────────┐
│ 2. FASTAPI SERVING    │   │ 3. REPORT GENERATOR        │
│    • DuckDB SQL Engine│   │    • Typst Typesetting     │
│    • Pydantic v2      │   │    • High-DPI Chart Export │
│    • Dynamic Filtering│   │    • Auditable PDF Output  │
└───────────┬───────────┘   └────────────────────────────┘
            │ (REST / JSON over HTTP/3)
            ▼
┌────────────────────────────────────────────────────────┐
│  4. REACT 19 + TYPESCRIPT TELEMETRY COMMAND CENTER     │
│     • Tailwind CSS v4 (Obsidian #000105 / #FF5500)     │
│     • Apache ECharts (2x2 Quadrant & Over Timelines)   │
│     • TanStack Table v8 (Auditable Top-10 Leaderboards)│
└────────────────────────────────────────────────────────┘
```

---

## 2. 2026 Tech Stack Summary Matrix

| Layer | Recommended 2026 Technology | Primary Role in CLUTCH-X |
| :--- | :--- | :--- |
| **Data Engineering & Math** | **Python 3.13**, **Polars**, **NumPy**, **SciPy** | Reconstructing pre-delivery scoreboard states, computing the Pressure Index ($PI$), context normalization, and Bayesian reliability shrinkage. |
| **Analytical Storage** | **DuckDB** + **Apache Parquet** | Embedded OLAP storage enabling sub-50ms multi-dimensional slicing (IPL vs. T20I, Innings 1 vs. 2, Knockout filters) without a separate DB server. |
| **Backend API** | **FastAPI** + **Pydantic v2** + **Uvicorn** | High-throughput async REST API serving filtered leaderboard rankings, scatter coordinates, and match-by-match audit logs. |
| **Frontend Framework** | **React 19** + **TypeScript 5.8** + **Vite 6** | Type-safe, ultra-responsive Single Page Application (SPA) powering the three-view tactical command center. |
| **UI & Styling System** | **Tailwind CSS v4** + **Radix UI Primitives** | CSS-first design token architecture implementing Catapult's `#000105` obsidian dark mode, `#FF5500` signal orange, and `2px`–`4px` machined geometry. |
| **Telemetry Charts & Grids** | **Apache ECharts 5/6** + **TanStack Table v8** | Canvas/WebGL rendering for the 2x2 Quadrant Scatter Plot, 20-over OpenField timeline, and tabular-numeral leaderboards. |
| **PDF Methodology Report** | **Typst** + **Matplotlib / ECharts SSR** | Programmatic generation of the submission PDF whitepaper directly from verified pipeline outputs to guarantee 100% rank parity. |
| **Deployment & CI/CD** | **Cloudflare Pages / Vercel** + **Docker on Railway** + **GitHub Actions** | Edge CDN hosting for the frontend, containerized FastAPI + DuckDB backend, and automated statistical validation gates on every commit. |

---

## 3. Layer-by-Layer Justification

### 3.1 Data Engineering & Quantitative Analytics Layer

* **Selected Stack:** `Python 3.13`, `Polars`, `DuckDB`, `NumPy`, `SciPy`
* **Why It Wins in 2026:**
  1. **Vectorized Window Speed (`Polars`):** Reconstructing the live match state before every delivery requires grouped cumulative window functions (`runs`, `wickets_lost`, `legal_balls_bowled`, and DLS `revised_target` adjustments partitioned by `match_id` and `innings`). Polars' Rust-native multi-threaded engine executes these transformations $10\times$–$30\times$ faster than legacy Pandas with strict schema typing and zero silent type-coercion bugs.
  2. **Zero-Infrastructure OLAP (`DuckDB` + `Parquet`):** Instead of provisioning and paying for a cloud PostgreSQL instance for ~150k–300k historical ball-by-ball rows, baking the enriched dataset into a compressed `.parquet` / `.duckdb` file allows FastAPI to execute complex analytical aggregations (`GROUP BY player_id`, dynamic percentile cutoffs, and over-by-over timelines) in **under 30 milliseconds** in memory.
  3. **Statistical Rigor (`SciPy` & `NumPy`):** Directly supports the PRD's reliability guardrails—computing Bayesian shrinkage weights toward peer cohort means, volatility penalties ($\mu - \lambda\sigma$), $p$-values for pressure regime separation ($PI \ge 60$ vs. $PI < 60$), and Spearman rank correlation ($\rho \ge 0.65$) for split-half stability audits.

---

### 3.2 Backend & API Layer

* **Selected Stack:** `FastAPI`, `Pydantic v2`, `Orjson`
* **Why It Wins in 2026:**
  1. **Unified Language Ecosystem:** Keeping the backend in Python eliminates serialization friction between the quantitative modeling pipeline (`Polars`/`SciPy`) and the API endpoints serving the frontend.
  2. **Strict Contract Validation (`Pydantic v2`):** Ensures that every API response powering the Top-10 Batting and Bowling Leaderboards enforces non-duplicate ranks (`01` through `10`), valid numeric bounds, and clean player metadata mapping for Unstop dropdown verification.
  3. **High-Speed JSON Serialization (`Orjson`):** Serializes dense scatter-plot arrays (hundreds of eligible player nodes + match-level audit drawers) with minimal latency so interactive slider adjustments feel instantaneous.

---

### 3.3 Frontend Telemetry Interface Layer

* **Selected Stack:** `React 19`, `TypeScript 5.8`, `Vite 6`, `Tailwind CSS v4`, `TanStack Query v5`, `TanStack Table v8`, `Apache ECharts`
* **Why It Wins in 2026:**
  1. **60fps Interactive Telemetry (`React 19` + `Vite 6`):** CLUTCH-X behaves like Catapult's **OpenField Cloud**—a dense analytical workstation where coaches and scouts toggle competition filters (`IPL` vs. `T20I`), innings contexts, and minimum high-pressure ball sliders (`100`–`300` balls). React 19's concurrent rendering and automatic compiler optimizations keep UI transitions lag-free without manual `useMemo` boilerplate.
  2. **Native CSS Design Tokens (`Tailwind CSS v4`):** Tailwind v4's CSS-first `@theme` engine maps 1:1 to the design tokens defined in `design.md` (`--bg-obsidian: #000105`, `--accent-clutch-orange: #FF5500`, `--font-display: 'Barlow Condensed'`, `--font-mono: 'JetBrains Mono'`), guaranteeing exact visual fidelity with Catapult's high-contrast aesthetic.
  3. **Hardware-Accelerated Sports Visualization (`Apache ECharts`):** Standard SVG charting libraries bog down when rendering custom quadrant overlays, direct leader-line annotations, diverging delta bars, and interactive 20-block over timelines. Apache ECharts uses HTML5 Canvas rendering, supports custom graphic primitives for the **2x2 Quadrant Diagnostic Chart** (*All-Weather Elites* vs. *Clutch Elevators*), and allows one-click high-DPI PNG export for the report.
  4. **Headless Precision Grids (`TanStack Table v8`):** Powers the **Auditable Top-10 Leaderboards** with native sorting, expandable match-by-match audit rows, and strict `tabular-nums` column alignment without imposing opinionated styling that would clash with our `1px` hairline dark theme.

---

### 3.4 Automated Methodology Report Engine

* **Selected Stack:** `Typst` (with JSON data binding + High-DPI ECharts/Matplotlib exports)
* **Why It Wins in 2026:**
  1. **Single Source of Truth (100% Rank Parity):** A common failure mode in data science competitions is manually copy-pasting numbers into Word/Google Docs and accidentally creating discrepancies between the PDF report and the Unstop dropdown submission. By compiling the report with **Typst** (a fast, modern Rust-based typesetting alternative to LaTeX) directly from the backend's exported `top10_rankings.json`, every rank, Strike Rate delta, and formula callout stays 100% synchronized with the live dashboard.
  2. **Catapult Whitepaper Aesthetics:** Typst provides effortless control over crisp `#FFFFFF` editorial pages, `#000105` dark section banners, condensed uppercase headers, `#FF5500` left-accented formula blocks, and vector-sharp tables.

---

### 3.5 Deployment, Infrastructure & CI/CD

* **Selected Stack:**
  * **Frontend:** `Cloudflare Pages` (or `Vercel`)
  * **Backend:** `Docker` container deployed on `Railway` (or `Render`)
  * **CI/CD & Testing:** `GitHub Actions` + `Pytest` + `Playwright`
* **Why It Wins in 2026:**
  1. **Zero-Latency Global Edge Delivery (`Cloudflare Pages`):** Serves the compiled Vite/React static bundle and web fonts (`Barlow Condensed`, `Inter`, `JetBrains Mono`) from edge nodes globally (including low-latency nodes across India) with automatic SSL, HTTP/3, and preview URLs for every pull request.
  2. **Self-Contained Compute Container (`Docker` + `Railway`):** During the Docker image build step, the deterministic Polars ETL script runs once against the version-controlled CSVs to generate `clutch_x.duckdb`. At runtime, the FastAPI container boots in $<1\text{ second}$ with zero external database dependencies, eliminating connection-pool failures during live demos or judging.
  3. **Automated Analytical Quality Gates (`GitHub Actions`):** Every push triggers a `pytest` suite that verifies:
     * Zero duplicate `player_id` values in the Top 10 Batter and Bowler outputs.
     * Pressure regime ($PI \ge 60$) captures between $15\%$ and $25\%$ of total legal deliveries.
     * Split-half Spearman rank stability remains $\rho \ge 0.65$.

---

## 4. Recommended Monorepo Directory Structure

```text
clutch-x/
├── .github/
│   └── workflows/
│       └── validate_and_deploy.yml   # CI: Pytest statistical checks + Docker build
├── data/
│   ├── raw/                          # Original competition CSV files
│   └── processed/                    # Generated clutch_x.duckdb & Parquet artifacts
├── engine/                           # Python 3.13 Quantitative & API Core
│   ├── etl/
│   │   ├── state_reconstructor.py    # Polars pre-delivery scoreboard & DLS logic
│   │   ├── pressure_index.py         # Unified 1st/2nd innings PI (0-100) formula
│   │   ├── normalizer.py             # Context-expected runs/wickets (IPL vs T20I)
│   │   └── scorer.py                 # Clutch ratings, Bayesian shrinkage & rankings
│   ├── api/
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── schemas.py                # Pydantic v2 strict leaderboard & audit models
│   │   └── queries.py                # Sub-50ms DuckDB analytical queries
│   ├── tests/
│   │   └── test_rankings_audit.py    # Automated parity, sample-size & stability tests
│   └── Dockerfile                    # Pre-bakes DuckDB artifact into API container
├── frontend/                         # React 19 + TypeScript Telemetry UI
│   ├── src/
│   │   ├── styles/
│   │   │   └── tokens.css            # Tailwind v4 @theme Catapult color/font tokens
│   │   ├── components/
│   │   │   ├── PressurePill.tsx      # PI regime badge (Routine -> Critical Leverage)
│   │   │   ├── OverTimeline.tsx      # OpenField-style 20-over pressure bar
│   │   │   ├── QuadrantChart.tsx     # ECharts 2x2 Baseline vs. Pressure scatter
│   │   │   └── LeaderboardTable.tsx  # TanStack Table v8 with inline delta bars
│   │   └── views/
│   │       ├── OverviewBlueprint.tsx # Executive methodology & value pillars
│   │       ├── TacticalConsole.tsx   # Interactive OpenField command center
│   │       └── Top10Leaderboards.tsx # Auditable Top-10 Batters & Bowlers
│   └── package.json
└── report/                           # Automated Methodology Report Deliverable
    ├── clutch_x_report.typ           # Typst template styled as Catapult whitepaper
    ├── figures/                      # High-DPI dark-mode diagnostic charts
    └── build_report.py               # Injects verified JSON metrics & compiles PDF
```