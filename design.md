# Design Document: CLUTCH-X
**Contextual Leverage & Under-Pressure T20 Execution Engine**  
**Aesthetic Benchmark:** Catapult Sports Cricket (`catapult.com/sports/cricket`) & OpenField Telemetry Suite  
**Version:** 1.0  
**Target Users:** Auction Scouts & Recruitment Teams, Performance Analysts & Data Scientists, Head Coaches & Team Captains, Franchise & National Selectors  

---

## 1. Design Vision & Brand Positioning

**CLUTCH-X** translates raw T20 ball-by-ball event logs into elite, decision-grade sports science intelligence. Inspired by **Catapult Sports' Cricket Performance Platform**, the visual language rejects generic "consumer SaaS" softness in favor of **precision-engineered athletic telemetry**. 

Every screen, chart, and report table is designed to look and feel like a franchise performance command center—pairing obsidian-dark telemetry surfaces with high-contrast white editorial blocks, condensed athletic typography, and vivid signal-orange highlights that isolate high-leverage match moments ($PI \ge 60$) at a single glance.

---

## 2. Part I: Reference Aesthetic Teardown (`catapult.com/sports/cricket`)

An audit of Catapult's cricket product experience reveals four foundational pillars that govern its visual authority:

### 2.1 Color System & Surface Polarity
* **High-Contrast Dark/Light Alternation:** Catapult anchors its hero sections, navigation, and telemetry panels in deep carbon/blue-charcoal black (`#000105` / `#000000`), creating an immediate high-tech command-room mood. It alternates cleanly into stark white (`#FFFFFF`) and cool technical gray (`#F4F6F8`) sections for dense analytical copy and validation benchmarks.
* **Signature Signal Orange Accent:** Vivid athletic orange (`#FF5500` / `#F25C05`) is used with surgical restraint—reserved strictly for primary CTAs, active period timelines, key performance thresholds, and interactive focus states.
* **Monochrome Photography + Data Pop:** Athlete imagery is treated with desaturated, high-contrast monochrome or moody dark overlays so overlaid telemetry metrics and orange accents remain 100% legible.

### 2.2 Typography & Editorial Hierarchy
* **Condensed Uppercase Display Headings:** Headlines use bold, tight-tracked condensed sans-serif letterforms (e.g., *DIN Condensed* / *Gobold* / *Barlow Condensed* aesthetic) set in ALL CAPS (`OPTIMISE CRICKET PERFORMANCE`, `DESIGNED FOR CRICKET`, `CRICKET VIDEO ANALYSIS`). This evokes stadium scoreboards, tactical playbooks, and biomechanical precision.
* **Neutral Geometric Body Copy:** Supporting descriptions use clean humanist/geometric sans-serif typography (*Roboto* / *Inter*) at generous line heights ($1.5\times$ to $1.6\times$) for rapid scanning by coaches and analysts.
* **Tabular Telemetry Numerals:** All sensor outputs (`Velocity`, `PlayerLoad`, `Max Rotation`) enforce monospaced/tabular figure alignment (`font-variant-numeric: tabular-nums`) so multi-row tables and live readouts never jitter horizontally.

### 2.3 Layout Grid & Spatial Rhythm
* **12-Column Precision Grid:** Built on a strict 12-column desktop container (`1280px` max width) with crisp `1px` structural hairlines (`#1F242D` on dark, `#E2E8F0` on light) instead of heavy drop shadows.
* **3-Column Value Pillars:** Core analytical pillars (e.g., *Optimise Performance*, *Mitigate Risk*, *Support Return to Play*) are presented in symmetrical 3-column cards with uppercase category kickers and concise 3-line tactical explanations.
* **Asymmetric 50/50 Split Modules:** Deep-dive features pair a left-aligned narrative block (kicker + condensed headline + bulleted capabilities + CTA) with a right-aligned visual artifact (telemetry dashboard UI, video scrubbers, or sensor charts).
* **Institutional Credibility Strip:** A dedicated monochrome logo bar displaying elite cricket boards and franchises (*Cricket Australia*, *New Zealand Cricket*, *Mumbai Indians*, *Chennai Super Kings*) establishes immediate domain trust.

### 2.4 Signature Component Patterns
* **Sharp, Machined Geometry:** Buttons, cards, and inputs use minimal border radii (`2px` to `4px`) rather than pill shapes—reinforcing an industrial, hardware-software engineering aesthetic.
* **OpenField Activity & Period Timelines:** Horizontal multi-segment timeline bars where standard play renders in neutral slate/green and high-intensity/selected periods illuminate in bright orange.
* **Players-In-Period (PIP) Roster Tiles:** Compact, selectable athlete cards displaying jersey/role tags, player names, and an active orange bottom underline bar when selected to filter dashboard widgets.

---

## 3. Part II: CLUTCH-X Design Token System

To achieve seamless visual cohesion across the **CLUTCH-X interactive web dashboard** and the **SupeRR Selector Methodology Report**, all interfaces must implement the following design tokens.

### 3.1 Color Palette

| Token Name | Hex Value | RGB | Usage & Semantic Role |
| :--- | :--- | :--- | :--- |
| `--bg-obsidian` | `#000105` | `0, 1, 5` | Primary app background, hero canvas, top navigation bar |
| `--bg-carbon` | `#0B0E14` | `11, 14, 20` | Elevated dashboard panels, sidebar navigation, chart containers |
| `--bg-slate-card` | `#131822` | `19, 24, 34` | Interactive KPI cards, table row hover states, modal surfaces |
| `--bg-paper-light` | `#FFFFFF` | `255, 255, 255` | Editorial whitepaper sections, printable report backgrounds |
| `--bg-paper-tint` | `#F4F6F9` | `244, 246, 249` | Alternating light-mode table rows, callout boxes |
| `--border-hairline-dark` | `#1E2532` | `30, 37, 50` | `1px` structural grid dividers on dark surfaces |
| `--border-hairline-light` | `#DCE1E8` | `220, 225, 232` | `1px` structural grid dividers on light surfaces |
| `--text-primary-dark` | `#FFFFFF` | `255, 255, 255` | Primary headings, active metrics, selected player names |
| `--text-secondary-dark` | `#94A3B8` | `148, 163, 184` | Metric labels, axis ticks, secondary descriptions |
| `--text-primary-light` | `#0A0D14` | `10, 13, 20` | Body copy and headings in light report sections |
| `--accent-clutch-orange` | `#FF5500` | `255, 85, 0` | **Hero Brand Accent:** High-Pressure regime ($PI \ge 60$), primary CTAs, Rank #1–3 badges, active timeline segments |
| `--accent-orange-hover` | `#E04B00` | `224, 75, 0` | Interactive button hover and active border states |
| `--data-baseline-cyan` | `#00A3FF` | `0, 163, 255` | Normal-Pressure baseline ($PI < 60$), expected par trendlines |
| `--data-positive-emerald` | `#10B981` | `16, 185, 129` | Positive Clutch Delta ($+\Delta SR$, $+\text{Runs Saved Above Expected}$) |
| `--data-negative-crimson` | `#EF4444` | `239, 68, 68` | Negative performance dip under pressure, wicket fall markers |
| `--data-warning-amber` | `#F59E0B` | `245, 158, 11` | Medium-pressure transition zone ($45 \le PI < 60$), sample-size caution flags |

### 3.2 Typography Scale

* **Display Font (`--font-display`):** `'Barlow Condensed', 'DIN Condensed', 'Oswald', sans-serif` (Weights: `600 SemiBold`, `700 Bold`, Uppercase, Letter-Spacing: `+0.04em`).
* **UI & Body Font (`--font-sans`):** `'Inter', 'Roboto', -apple-system, sans-serif` (Weights: `400 Regular`, `500 Medium`, `600 SemiBold`).
* **Telemetry & Code Font (`--font-mono`):** `'JetBrains Mono', 'Roboto Mono', monospace` (Used for all KPI numbers, Pressure Index scores, Strike Rates, Economies, and formulas).

| Role | Font Family | Size / Line Height | Weight | Case & Tracking |
| :--- | :--- | :--- | :--- | :--- |
| **Hero Display (`H1`)** | `--font-display` | `56px` / `60px` | `700 Bold` | UPPERCASE, `+0.03em` |
| **Section Header (`H2`)** | `--font-display` | `36px` / `40px` | `700 Bold` | UPPERCASE, `+0.04em` |
| **Card / Module Title (`H3`)** | `--font-display` | `22px` / `26px` | `600 SemiBold` | UPPERCASE, `+0.03em` |
| **Section Kicker / Eyebrow** | `--font-mono` | `11px` / `16px` | `600 SemiBold` | UPPERCASE, `+0.12em` (`#FF5500`) |
| **Body Copy** | `--font-sans` | `15px` / `24px` | `400 Regular` | Sentence case, `0em` |
| **Hero KPI Readout** | `--font-mono` | `32px` / `36px` | `700 Bold` | Tabular numerals (`tnum`) |
| **Table Cell Telemetry** | `--font-mono` | `13px` / `20px` | `500 Medium` | Tabular numerals (`tnum`) |

### 3.3 Spacing, Radii & Elevation
* **Spacing Base Unit:** `4px` (`0.25rem`). Standard card internal padding: `20px` (`p-5`). Section vertical padding: `64px` (`py-16`).
* **Border Radius:** Strictly angular (`2px` on badges/inputs, `4px` on cards and buttons). Zero rounded-full pills except circular scatter-plot nodes.
* **Elevation Strategy:** Flat surface layering separated by `1px solid var(--border-hairline-dark)` borders rather than blurred drop shadows. Active cards receive a `2px` top or left border accent in `#FF5500`.

---

## 4. Part III: Core Page & Dashboard Architecture

CLUTCH-X is structured into **three primary views**, accessible via a persistent top command header (`64px` height, `#000105` background, angular orange `CLUTCH-X` geometric emblem on the left, view switcher tabs in the center, and dataset filter pills `[IPL + T20I | 2022–PRESENT]` on the right).

### 4.1 View 1: Executive Overview & Methodology Blueprint
Modeled directly on Catapult's product landing architecture for stakeholders and competition evaluators:
1. **Dark Telemetry Hero Banner:**
   * **Left Column (60%):** Eyebrow kicker `T20 CONTEXTUAL LEVERAGE ENGINE`, bold condensed headline `QUANTIFY EXECUTION WHEN THE GAME IS ON THE LINE`, 2-line value summary, and dual angular CTAs (`EXPLORE TOP-10 RANKINGS` in solid `#FF5500` and `INSPECT PRESSURE FORMULA` in `1px` white outline).
   * **Right Column (40%):** High-contrast monochrome stadium/cricket action silhouette overlaid with a live glowing vector telemetry card showing a sample ball state (`OVER 18.4 | RRR 13.50 | WICKETS: 6 | PI: 88.4 [EXTREME PRESSURE]`).
2. **Validation & Scope Strip:** Monochrome horizontal bar displaying dataset coverage metrics (`2022–PRESENT`, `IPL & T20 INTERNATIONALS`, `DELIVERY-LEVEL STATE ENGINE`, `BAYESIAN RELIABILITY FILTERED`).
3. **3-Column Core Engine Pillars (Light `#FFFFFF` Band):**
   * *Column 01:* **DYNAMIC BALL-BY-BALL PRESSURE ENGINE** (Unified 1st-innings collapse/death + 2nd-innings chase leverage index).
   * *Column 02:* **ERA & FORMAT NORMALIZATION** (Context-expected runs and wicket probabilities across IPL and T20I environments).
   * *Column 03:* **RELIABILITY & VOLATILITY GUARDRAILS** (Minimum sample-size cutoffs and cross-match consistency penalties).

### 4.2 View 2: CLUTCH-X Tactical Command Center (Interactive Analytics Workspace)
Modeled after Catapult's **OpenField Cloud** telemetry console for Performance Analysts and Head Coaches:
* **Top Global Filter Strip:** Multi-select toggles for Competition (`ALL`, `IPL`, `T20I`), Innings (`BOTH`, `1ST INNINGS SETTING`, `2ND INNINGS CHASING`), Match Stage (`ALL`, `LEAGUE`, `KNOCKOUTS / PLAYOFFS`), and Minimum High-Pressure Balls slider (`100` to `300` balls).
* **OpenField-Style Innings Pressure Timeline (Full Width):**
  * A 20-block horizontal bar representing Overs `1` through `20`.
  * Each over block displays average Pressure Index ($PI$) intensity via color saturation (`#1E2532` for low pressure, `#F59E0B` for medium pressure, `#FF5500` for high pressure) and wicket markers (`W` crimson dots above the bar). Clicking any over filters the telemetry widgets below.
* **2-Column Diagnostic Split:**
  * **Left Panel (55%):** Interactive **2x2 Quadrant Scatter Plot** (*Normal Baseline Rating* on X-axis vs. *High-Pressure Clutch Rating* on Y-axis).
  * **Right Panel (45%):** **Player-In-Period (PIP) Comparison Drawer** allowing coaches/scouts to select up to 3 players side-by-side to compare their Pressure Strike Rate/Economy delta, boundary retention, dot-ball rate, and match-by-match consistency distribution.

### 4.3 View 3: Auditable Top-10 Leaderboards (Batting & Bowling)
Designed for **Auction Scouts**, **Selectors**, and **Unstop Submission Verification**:
* **Side-by-Side or Tabbed Discipline Switcher:** `[TOP 10 PRESSURE BATTERS]` | `[TOP 10 PRESSURE BOWLERS]`.
* **Rank #1 Spotlight Card:** A featured full-width telemetry card at the top of each list highlighting the #1 ranked player with a monochrome portrait badge, composite `CLUTCH-X RATING`, sparkline of match-by-match pressure impact, and 4 key delta callouts.
* **Precision Telemetry Leaderboard Table (Ranks 1–10):**
  * Strictly ordered `01` through `10` with zero duplicate players, high-contrast tabular numerals, inline diverging horizontal delta bars (`#10B981` positive vs. `#EF4444` negative), and an expandable row drawer revealing match-by-match audit logs.

---

## 5. Part IV: Signature Component Specifications

### 5.1 Pressure Index ($PI$) Gauge & Regime Pill
* **Purpose:** Visually communicates the delivery-level pressure score ($0$ to $100$) calculated by the engine.
* **Anatomy:**
  * Compact rectangular badge (`2px` radius) with `1px` border and `JetBrains Mono` bold readout.
  * **Low Pressure ($PI < 40$):** Border `#334155`, Text `#94A3B8`, Label `ROUTINE`.
  * **Moderate Pressure ($40 \le PI < 60$):** Border `#F59E0B`, Text `#F59E0B`, Label `BUILDING`.
  * **High Pressure ($60 \le PI < 80$):** Border `#FF5500`, Background `rgba(255, 85, 0, 0.12)`, Text `#FF5500`, Label `HIGH PRESSURE`.
  * **Extreme Pressure ($PI \ge 80$):** Solid `#FF5500` fill, `#FFFFFF` bold text, Label `CRITICAL LEVERAGE`.

### 5.2 2x2 Quadrant Diagnostic Chart (*Baseline vs. Pressure Execution*)
* **Purpose:** Proves that rankings are driven by empirical data rather than reputation by separating four distinct player archetypes.
* **Visual Specification:**
  * **Canvas:** `#0B0E14` background with `#1E2532` dashed crosshair lines marking the cohort median on both axes.
  * **Quadrant Labels (Uppercase Condensed, `12px`, `40%` opacity in corners):**
    * *Top-Right (`#FF5500` tint):* **ALL-WEATHER ELITES** (High Normal Baseline + Elite Pressure Output).
    * *Top-Left (`#00A3FF` tint):* **CLUTCH ELEVATORS** (Moderate Normal Baseline + Massive Surge Under Pressure — prime auction value targets).
    * *Bottom-Right (`#94A3B8` tint):* **FRONT-RUNNERS** (High Normal Baseline + Dip Under Pressure).
    * *Bottom-Left (`#475569` tint):* **BELOW PAR** (Low Baseline + Low Pressure Output).
  * **Data Nodes:** Eligible pool plotted as muted slate circles (`#475569`, `r = 5px`); **Top-10 Ranked Players** highlighted as solid `#FF5500` circles (`r = 8px`) with crisp white rank tags (`#1`–`#10`) and direct leader-line name annotations.

### 5.3 Dual-Discipline Telemetry Table Columns
To guarantee transparent comparison across batting and bowling, tables adhere to strict column schemas:

* **Batting Leaderboard Schema:**
  1. `RANK` (`01`–`10` in `#FF5500` bold mono)
  2. `PLAYER` (Full Name + Primary Team/Nation tag)
  3. `HP BALLS / INNS` (High-Pressure balls faced & distinct matches)
  4. `NORM SR` (Baseline Strike Rate when $PI < 60$)
  5. `CLUTCH SR` (High-Pressure Strike Rate when $PI \ge 60$)
  6. `SR DELTA` (Diverging bar + signed numeric value, e.g., `+18.4`)
  7. `pRAE / 100` (Pressure Runs Above Expected per 100 balls)
  8. `CONSISTENCY` (% of high-pressure innings with positive net impact)
  9. `CLUTCH-X SCORE` (Final reliability-adjusted composite score in bold `#FFFFFF` pill)

* **Bowling Leaderboard Schema:**
  1. `RANK` (`01`–`10` in `#FF5500` bold mono)
  2. `PLAYER` (Full Name + Primary Team/Nation tag)
  3. `HP BALLS / INNS` (High-Pressure legal deliveries & distinct matches)
  4. `NORM ECON` (Baseline Economy when $PI < 60$)
  5. `CLUTCH ECON` (High-Pressure Economy when $PI \ge 60$)
  6. `ECON DELTA` (Diverging bar + runs saved per over vs. baseline)
  7. `pRSAE / OV` (Pressure Runs Saved Above Expected per over)
  8. `HP DOT % & WKTS` (High-pressure dot-ball % and clutch wickets)
  9. `CLUTCH-X SCORE` (Final reliability-adjusted composite score in bold `#FFFFFF` pill)

---

## 6. Part V: Data Visualization & Methodology Report Styling Guidelines

When exporting static charts (via `matplotlib` / `seaborn` / `plotly`) for the **SupeRR Selector Season 2 Methodology Report PDF**, apply the following styling rules so the PDF looks like an official Catapult Sports whitepaper:

1. **Report Page Theme:** Use crisp white pages (`#FFFFFF`) for maximum print/screen legibility, accented with `#000105` dark header banners, condensed uppercase section headers (`H1`/`H2`), and `#FF5500` left-border callout blocks for key mathematical formulas.
2. **Chart Theme Consistency:** Render analytical charts on dark `#0B0E14` panels with `#FFFFFF` titles and `#FF5500` / `#00A3FF` data series to create striking visual contrast against white report pages—mirroring Catapult's editorial whitepaper aesthetic.
3. **Direct Data Labeling:** Eliminate cluttered chart legends wherever possible. Label key thresholds (e.g., `PI = 60 High-Pressure Cutoff`) and Top-10 player markers directly on the canvas using `JetBrains Mono` `9pt` callouts.
4. **Accessibility & Colorblind Safety:** Never rely on red/green alone to encode performance deltas. Pair color encoding (`#10B981` vs. `#EF4444`) with explicit `+` / `-` signs, directional arrows (`▲` / `▼`), and luminance contrast ratios exceeding `4.5:1` (WCAG 2.1 AA compliant).